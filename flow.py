"""Module with main classes related to Flows."""
# pylint: disable=missing-docstring

import json
from abc import ABC, abstractmethod
from hashlib import md5

# Note: FlowModCommand is the same in both v0x01 and v0x04
from pyof.v0x04.controller2switch.flow_mod import FlowModCommand


class Flow(ABC):  # pylint: disable=too-many-instance-attributes
    """Class to abstract a Flow to switches.

    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """

    # Subclasses must set their version-specific classes
    _action_class = None
    _flow_mod_class = None
    _match_class = None

    def __init__(self, switch, table_id=0xff, match=None, priority=0,
                 idle_timeout=0, hard_timeout=0, cookie=0, actions=None):
        """Assign parameters to attributes.

        Args:
            table_id (int): The index of a single table or 0xff for all tables.
            match (|match|): Match object.
            priority (int): Priority level of flow entry.
            idle_timeout (int): Idle time before discarding in seconds.
            hard_timeout (int): Max time before discarding in seconds.
            cookie (int): Opaque controller-issued identifier.
            actions (|list_of_actions|): List of action to apply.
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
        self.stats = {}

    @property
    def id(self):  # pylint: disable=invalid-name
        """Return the flow unique identifier.

        Calculates the hash of the object by using Python's md5 on the json
        without statistics.

        Returns:
            str: Flow unique identifier (md5sum).
        """
        json_str = self.as_json(sort_keys=True, include_id=False)
        md5sum = md5()
        md5sum.update(json_str.encode('utf-8'))
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
        return flow_dict

    @classmethod
    def from_dict(cls, flow_dict, switch):
        flow = cls(switch)

        for attr_name, attr_value in flow_dict.items():
            if attr_name in flow.__dict__:
                setattr(flow, attr_name, attr_value)

        if 'match' in flow_dict:
            flow.match = cls._match_class.from_dict(flow_dict['match'])

        flow.actions = []
        if 'actions' in flow_dict:
            for action_dict in flow_dict['actions']:
                action = cls._action_class.from_dict(action_dict)
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

    def as_add_flow_mod(self):
        return self._as_flow_mod(FlowModCommand.OFPFC_ADD)

    def as_delete_flow_mod(self):
        return self._as_flow_mod(FlowModCommand.OFPFC_DELETE)

    def _as_flow_mod(self, command):
        # Disable not-callable error as subclasses set a class
        flow_mod = self._flow_mod_class()  # pylint: disable=E1102
        flow_mod.match = self.match.as_of_match()
        flow_mod.cookie = self.cookie
        flow_mod.command = command
        flow_mod.idle_timeout = self.idle_timeout
        flow_mod.hard_timeout = self.hard_timeout
        flow_mod.priority = self.priority
        flow_mod.actions = [action.as_of_action() for action in self.actions]
        return flow_mod

    @classmethod
    def from_of_flow_stats(cls, flow_stats, switch):
        actions = [cls._action_class.from_of_action(action)
                   for action in flow_stats.actions]
        flow = cls(switch=switch,
                   table_id=flow_stats.table_id.value,
                   match=cls._match_class.from_of_match(flow_stats.match),
                   priority=flow_stats.priority.value,
                   idle_timeout=flow_stats.idle_timeout.value,
                   hard_timeout=flow_stats.hard_timeout.value,
                   cookie=flow_stats.cookie.value,
                   actions=actions)
        return flow


class Match:  # pylint: disable=too-many-instance-attributes
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
