"""Module with main classes related to Flows."""
# pylint: disable=missing-docstring

import json
from abc import ABC, abstractmethod
from hashlib import md5

# Note: FlowModCommand is the same in both v0x01 and v0x04
from pyof.v0x04.controller2switch.flow_mod import FlowModCommand


class FlowBase(ABC):  # pylint: disable=too-many-instance-attributes
    """Class to abstract a Flow to switches.

    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """

    # Subclasses must set their version-specific classes
    _action_factory = None
    _flow_mod_class = None
    _match_class = None

    def __init__(self, switch, table_id=0xff, match=None, priority=0,
                 idle_timeout=0, hard_timeout=0, cookie=0, actions=None,
                 stats=None):
        """Assign parameters to attributes.

        Args:
            table_id (int): The index of a single table or 0xff for all tables.
            match (|match|): Match object.
            priority (int): Priority level of flow entry.
            idle_timeout (int): Idle time before discarding in seconds.
            hard_timeout (int): Max time before discarding in seconds.
            cookie (int): Opaque controller-issued identifier.
            actions (|list_of_actions|): List of actions to apply.
            stats (Stats): Flow latest statistics.
        """
        # pylint: disable=too-many-arguments,too-many-locals
        self.switch = switch
        self.table_id = table_id
        # Disable not-callable error as subclasses set a class
        self.match = match or self._match_class()  # pylint: disable=E1102
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout
        self.cookie = cookie
        self.actions = actions or []
        self.stats = stats or FlowStats()  # pylint: disable=E1102

    @property
    def id(self):  # pylint: disable=invalid-name
        """Return the flow unique identifier.

        Calculates the hash of the object by using Python's md5 on the json
        without statistics.

        Returns:
            str: Flow unique identifier (md5sum).

        """
        flow_str = self.as_json(sort_keys=True, include_id=False)
        flow_str += str(self.switch.id)
        md5sum = md5()
        md5sum.update(flow_str.encode('utf-8'))
        return md5sum.hexdigest()

    def as_dict(self, include_id=True):
        """Return the representation of a flow as a python dictionary.

        Returns:
            dict: Dictionary using flow attributes.

        """
        flow_dict = {'table_id': self.table_id,
                     'match': self.match.as_dict(),
                     'priority': self.priority,
                     'idle_timeout': self.idle_timeout,
                     'hard_timeout': self.hard_timeout,
                     'cookie': self.cookie,
                     'actions': [action.as_dict() for action in self.actions]}
        if include_id:
            flow_dict['id'] = self.id
            flow_dict['stats'] = self.stats.as_dict()

        return flow_dict

    @classmethod
    def from_dict(cls, flow_dict, switch):
        flow = cls(switch)

        for attr_name, attr_value in flow_dict.items():
            if attr_name in flow.__dict__:
                setattr(flow, attr_name, attr_value)

        if 'match' in flow_dict:
            flow.match = cls._match_class.from_dict(flow_dict['match'])
        if 'stats' in flow_dict:
            flow.stats = FlowStats.from_dict(flow_dict['stats'])
        if 'actions' in flow_dict:
            flow.actions = []
            for action_dict in flow_dict['actions']:
                action = cls._action_factory.from_dict(action_dict)
                flow.actions.append(action)

        return flow

    def as_json(self, sort_keys=False, include_id=True):
        """Return the representation of a flow in a json format.

        By default, Python doesn't sort keys. To properly calculate the ID,
        sorting keys is required.

        Returns:
            string: Json string using flow attributes.

        """
        return json.dumps(self.as_dict(include_id), sort_keys=sort_keys)

    def as_of_add_flow_mod(self):
        return self._as_of_flow_mod(FlowModCommand.OFPFC_ADD)

    def as_of_delete_flow_mod(self):
        return self._as_of_flow_mod(FlowModCommand.OFPFC_DELETE)

    @abstractmethod
    def _as_of_flow_mod(self, command):
        # Disable not-callable error as subclasses set a class
        flow_mod = self._flow_mod_class()  # pylint: disable=E1102
        flow_mod.match = self.match.as_of_match()
        flow_mod.cookie = self.cookie
        flow_mod.command = command
        flow_mod.idle_timeout = self.idle_timeout
        flow_mod.hard_timeout = self.hard_timeout
        flow_mod.priority = self.priority
        return flow_mod

    @staticmethod
    @abstractmethod
    def _get_of_actions(of_flow_stats):
        pass

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats, switch):
        """Create a flow with stats latest based on pyof FlowStats."""
        of_actions = cls._get_of_actions(of_flow_stats)
        actions = (cls._action_factory.from_of_action(of_action)
                   for of_action in of_actions)
        return cls(switch,
                   table_id=of_flow_stats.table_id.value,
                   match=cls._match_class.from_of_match(of_flow_stats.match),
                   priority=of_flow_stats.priority.value,
                   idle_timeout=of_flow_stats.idle_timeout.value,
                   hard_timeout=of_flow_stats.hard_timeout.value,
                   cookie=of_flow_stats.cookie.value,
                   actions=actions,
                   stats=FlowStats.from_of_flow_stats(of_flow_stats))


class ActionBase(ABC):

    def as_dict(self):
        return vars(self)

    @classmethod
    def from_dict(cls, action_dict):
        action = cls(None)
        for attr_name, value in action_dict.items():
            if hasattr(action, attr_name):
                setattr(action, attr_name, value)
        return action

    @abstractmethod
    def as_of_action(self):
        """Create OF action for a FlowMod."""
        pass

    @classmethod
    @abstractmethod
    def from_of_action(cls, of_action):
        pass


class ActionFactoryBase(ABC):
    """FlowAction represents a action to be executed once a flow is actived."""

    # key: action_type or pyof class, value: ActionBase child
    _action_class = {
        'output': None,
        'set_vlan': None,
        # pyof class: ActionBase child
    }

    @classmethod
    def from_dict(cls, action_dict):
        """Build one of the Actions from a dictionary.

        Args:
            action_dict (dict): Python dictionary to build a FlowAction.
        """
        action_type = action_dict.get('action_type')
        action_class = cls._action_class[action_type]
        if action_class:
            return action_class.from_dict(action_dict)

    @classmethod
    def from_of_action(cls, of_action):
        of_class = type(of_action).__class__
        action_class = cls._action_class.get(of_class)
        if action_class:
            return action_class.from_of_action(of_action)


class MatchBase:  # pylint: disable=too-many-instance-attributes

    def __init__(self, in_port=None, dl_src=None, dl_dst=None, dl_vlan=None,
                 dl_vlan_pcp=None, dl_type=None, nw_proto=None, nw_src=None,
                 nw_dst=None, tp_src=None, tp_dst=None):
        # pylint: disable=too-many-arguments
        self.in_port = in_port
        self.dl_src = dl_src
        self.dl_dst = dl_dst
        self.dl_vlan = dl_vlan
        self.dl_vlan_pcp = dl_vlan_pcp
        self.dl_type = dl_type
        self.nw_proto = nw_proto
        self.nw_src = nw_src
        self.nw_dst = nw_dst
        self.tp_src = tp_src
        self.tp_dst = tp_dst

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, dict_content):
        match = cls()
        for key, value in dict_content.items():
            if key in match.__dict__:
                setattr(match, key, value)
        return match

    @classmethod
    @abstractmethod
    def from_of_match(cls, of_match):
        pass

    @abstractmethod
    def as_of_match(self):
        pass


class Stats:
    """Simple class to store statistics as attributes and values."""

    def as_dict(self):
        """Exclude attributes with `None` values."""
        return {attribute: value
                for attribute, value in vars(self).items()
                if value is not None}

    @classmethod
    def from_dict(cls, stats_dict):
        stats = cls()
        cls._update(stats, stats_dict.items())
        return stats

    @classmethod
    def from_of_flow_stats(cls, of_stats):
        stats = cls()
        stats.update(of_stats)
        return stats

    def update(self, of_stats):
        """Given a pyof stats object, update stats attributes' values.

        pyof values are GenericType instances whose native values can be
        accessed by `.value`.
        """
        # Generator for GenericType values
        attr_name_value = ((attr_name, gen_type.value)
                           for attr_name, gen_type in vars(of_stats).items())
        self._update(self, attr_name_value)

    @staticmethod
    def _update(obj, iterable):
        """From attribute name and value pairs, update ``obj``."""
        for attr_name, value in iterable:
            if hasattr(obj, attr_name):
                setattr(obj, attr_name, value)


class FlowStats(Stats):
    """Common fields for 1.0 and 1.3 FlowStats."""

    def __init__(self):
        self.byte_count = None
        self.duration_sec = None
        self.duration_nsec = None
        self.packet_count = None


class PortStats(Stats):  # pylint: disable=too-many-instance-attributes
    """Common fields for 1.0 and 1.3 PortStats."""

    def __init__(self):
        self.rx_packets = None
        self.tx_packets = None
        self.rx_bytes = None
        self.tx_bytes = None
        self.rx_dropped = None
        self.tx_dropped = None
        self.rx_errors = None
        self.tx_errors = None
        self.rx_frame_err = None
        self.rx_over_err = None
        self.rx_crc_err = None
        self.collisions = None
