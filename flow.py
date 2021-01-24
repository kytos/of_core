"""High-level abstraction for Flows of multiple OpenFlow versions.

Use common fields of FlowStats/FlowMod of supported OF versions. ``match`` and
``actions`` fields are different, so Flow, Action and Match related classes are
inherited in v0x01 and v0x04 modules.
"""
import json
from abc import ABC, abstractmethod
from hashlib import md5

# Note: FlowModCommand is the same in both v0x01 and v0x04
from pyof.v0x04.controller2switch.flow_mod import FlowModCommand

from napps.kytos.of_core import v0x01, v0x04


class FlowFactory(ABC):  # pylint: disable=too-few-public-methods
    """Choose the correct Flow according to OpenFlow version."""

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats, switch):
        """Return a Flow for the switch OpenFlow version."""
        flow_class = cls.get_class(switch)
        return flow_class.from_of_flow_stats(of_flow_stats, switch)

    @staticmethod
    def get_class(switch):
        """Return the Flow class for the switch OF version."""
        of_version = switch.connection.protocol.version
        if of_version == 0x01:
            return v0x01.flow.Flow
        if of_version == 0x04:
            return v0x04.flow.Flow
        raise NotImplementedError(f'Unsupported OpenFlow version {of_version}')


class FlowBase(ABC):  # pylint: disable=too-many-instance-attributes
    """Class to abstract a Flow to switches.

    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """

    # of_version number: 0x01, 0x04
    of_version = None

    # Subclasses must set their version-specific classes
    _action_factory = None
    _flow_mod_class = None
    _match_class = None

    def __init__(self, switch, table_id=0x0, match=None, priority=0x8000,
                 idle_timeout=0, hard_timeout=0, cookie=0, actions=None,
                 stats=None):
        """Assign parameters to attributes.

        Args:
            switch (kytos.core.switch.Switch): Switch ID is used to uniquely
                identify a flow.
            table_id (int): The index of a single table.
            match (|match|): Match object.
            priority (int): Priority level of flow entry.
            idle_timeout (int): Idle time before discarding, in seconds.
            hard_timeout (int): Max time before discarding, in seconds.
            cookie (int): Opaque controller-issued identifier.
            actions (|list_of_actions|): List of actions to apply.
            stats (Stats): Latest flow statistics.
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
        """Return this flow unique identifier.

        Calculate an md5 hash based on this object's modified json string. The
        json for ID calculation excludes ``stats`` attribute that changes over
        time.

        Returns:
            str: Flow unique identifier (md5sum).

        """
        flow_str = self.as_json(sort_keys=True, include_id=False)
        md5sum = md5()
        md5sum.update(flow_str.encode('utf-8'))
        return md5sum.hexdigest()

    def as_dict(self, include_id=True):
        """Return the Flow as a serializable Python dictionary.

        Args:
            include_id (bool): Default is ``True``. Internally, it is set to
                ``False`` when calculating the flow ID that is based in this
                dictionary's JSON string.

        Returns:
            dict: Serializable dictionary.

        """
        flow_dict = {
            'switch': self.switch.id,
            'table_id': self.table_id,
            'match': self.match.as_dict(),
            'priority': self.priority,
            'idle_timeout': self.idle_timeout,
            'hard_timeout': self.hard_timeout,
            'cookie': self.cookie,
            'actions': [action.as_dict() for action in self.actions]}
        if include_id:
            # Avoid infinite recursion
            flow_dict['id'] = self.id
            # Remove statistics that change over time
            flow_dict['stats'] = self.stats.as_dict()

        return flow_dict

    @classmethod
    def from_dict(cls, flow_dict, switch):
        """Return an instance with values from ``flow_dict``."""
        flow = cls(switch)

        # Set attributes found in ``flow_dict``
        for attr_name, attr_value in flow_dict.items():
            if attr_name in vars(flow):
                setattr(flow, attr_name, attr_value)

        flow.switch = switch
        if 'stats' in flow_dict:
            flow.stats = FlowStats.from_dict(flow_dict['stats'])

        # Version-specific attributes
        if 'match' in flow_dict:
            flow.match = cls._match_class.from_dict(flow_dict['match'])
        if 'actions' in flow_dict:
            flow.actions = []
            for action_dict in flow_dict['actions']:
                action = cls._action_factory.from_dict(action_dict)
                if action:
                    flow.actions.append(action)

        return flow

    def as_json(self, sort_keys=False, include_id=True):
        """Return the representation of a flow in JSON format.

        Args:
            sort_keys (bool): ``False`` by default (Python's default). Sorting
                is used, for example, to calculate the flow ID.
            include_id (bool): ``True`` by default. Internally, the ID is not
                included while calculating it.

        Returns:
            string: Flow JSON string representation.

        """
        return json.dumps(self.as_dict(include_id), sort_keys=sort_keys)

    def as_of_add_flow_mod(self):
        """Return an OpenFlow add FlowMod."""
        return self._as_of_flow_mod(FlowModCommand.OFPFC_ADD)

    def as_of_delete_flow_mod(self):
        """Return an OpenFlow delete FlowMod."""
        return self._as_of_flow_mod(FlowModCommand.OFPFC_DELETE)

    @abstractmethod
    def _as_of_flow_mod(self, command):
        """Return a pyof FlowMod with given ``command``."""
        # Disable not-callable error as subclasses will set a class
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
        """Return pyof actions from pyof FlowStats."""

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats, switch):
        """Create a flow with latest stats based on pyof FlowStats."""
        of_actions = cls._get_of_actions(of_flow_stats)
        actions = (cls._action_factory.from_of_action(of_action)
                   for of_action in of_actions)
        non_none_actions = [action for action in actions if action]
        return cls(switch,
                   table_id=of_flow_stats.table_id.value,
                   match=cls._match_class.from_of_match(of_flow_stats.match),
                   priority=of_flow_stats.priority.value,
                   idle_timeout=of_flow_stats.idle_timeout.value,
                   hard_timeout=of_flow_stats.hard_timeout.value,
                   cookie=of_flow_stats.cookie.value,
                   actions=non_none_actions,
                   stats=FlowStats.from_of_flow_stats(of_flow_stats))

    def __eq__(self, other):
        include_id = False
        if not isinstance(other, self.__class__):
            raise ValueError(f'Error comparing flows: {other} is not '
                             f'an instance of {self.__class__}')

        return self.as_dict(include_id) == other.as_dict(include_id)


class ActionBase(ABC):
    """Base class for a flow action."""

    def as_dict(self):
        """Return a dict that can be dumped as JSON."""
        return vars(self)

    @classmethod
    def from_dict(cls, action_dict):
        """Return an action instance from attributes in a dictionary."""
        action = cls(None)
        for attr_name, value in action_dict.items():
            if hasattr(action, attr_name):
                setattr(action, attr_name, value)
        return action

    @abstractmethod
    def as_of_action(self):
        """Return a pyof action to be used by a FlowMod."""

    @classmethod
    @abstractmethod
    def from_of_action(cls, of_action):
        """Return an action from a pyof action."""


class ActionFactoryBase(ABC):
    """Deal with different implementations of ActionBase."""

    # key: action_type or pyof class, value: ActionBase child
    _action_class = {
        'output': None,
        'set_vlan': None,
        # pyof class: ActionBase child
    }

    @classmethod
    def from_dict(cls, action_dict):
        """Build the proper Action from a dictionary.

        Args:
            action_dict (dict): Action attributes.
        """
        action_type = action_dict.get('action_type')
        action_class = cls._action_class[action_type]
        return action_class.from_dict(action_dict) if action_class else None

    @classmethod
    def from_of_action(cls, of_action):
        """Build the proper Action from a pyof action.

        Args:
            of_action (pyof action): Action from python-openflow.
        """
        of_class = type(of_action)
        action_class = cls._action_class.get(of_class)
        return action_class.from_of_action(of_action) if action_class else None


class MatchBase:  # pylint: disable=too-many-instance-attributes
    """Base class with common high-level Match fields."""

    def __init__(self, in_port=None, dl_src=None, dl_dst=None, dl_vlan=None,
                 dl_vlan_pcp=None, dl_type=None, nw_proto=None, nw_src=None,
                 nw_dst=None, tp_src=None, tp_dst=None, in_phy_port=None,
                 ip_dscp=None, ip_ecn=None, udp_src=None, udp_dst=None,
                 sctp_src=None, sctp_dst=None, icmpv4_type=None,
                 icmpv4_code=None, arp_op=None, arp_spa=None, arp_tpa=None,
                 arp_sha=None, arp_tha=None, ipv6_src=None, ipv6_dst=None,
                 ipv6_flabel=None, icmpv6_type=None, icmpv6_code=None,
                 nd_tar=None, nd_sll=None, nd_tll=None, mpls_lab=None,
                 mpls_tc=None, mpls_bos=None, pbb_isid=None, v6_hdr=None,
                 metadata=None, tun_id=None):
        """Make it possible to set all attributes from the constructor."""
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
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
        self.in_phy_port = in_phy_port
        self.ip_dscp = ip_dscp
        self.ip_ecn = ip_ecn
        self.udp_src = udp_src
        self.udp_dst = udp_dst
        self.sctp_src = sctp_src
        self.sctp_dst = sctp_dst
        self.icmpv4_type = icmpv4_type
        self.icmpv4_code = icmpv4_code
        self.arp_op = arp_op
        self.arp_spa = arp_spa
        self.arp_tpa = arp_tpa
        self.arp_sha = arp_sha
        self.arp_tha = arp_tha
        self.ipv6_src = ipv6_src
        self.ipv6_dst = ipv6_dst
        self.ipv6_flabel = ipv6_flabel
        self.icmpv6_type = icmpv6_type
        self.icmpv6_code = icmpv6_code
        self.nd_tar = nd_tar
        self.nd_sll = nd_sll
        self.nd_tll = nd_tll
        self.mpls_lab = mpls_lab
        self.mpls_tc = mpls_tc
        self.mpls_bos = mpls_bos
        self.pbb_isid = pbb_isid
        self.v6_hdr = v6_hdr
        self.metadata = metadata
        self.tun_id = tun_id

    def as_dict(self):
        """Return a dictionary excluding ``None`` values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, match_dict):
        """Return a Match instance from a dictionary."""
        match = cls()
        for key, value in match_dict.items():
            if key in match.__dict__:
                setattr(match, key, value)
        return match

    @classmethod
    @abstractmethod
    def from_of_match(cls, of_match):
        """Return a Match instance from a pyof Match."""

    @abstractmethod
    def as_of_match(self):
        """Return a python-openflow Match."""


class Stats:
    """Simple class to store statistics as attributes and values."""

    def as_dict(self):
        """Return a dict excluding attributes with ``None`` value."""
        return {attribute: value
                for attribute, value in vars(self).items()
                if value is not None}

    @classmethod
    def from_dict(cls, stats_dict):
        """Return a statistics object from a dictionary."""
        stats = cls()
        cls._update(stats, stats_dict.items())
        return stats

    @classmethod
    def from_of_flow_stats(cls, of_stats):
        """Create an instance from a pyof FlowStats."""
        stats = cls()
        stats.update(of_stats)
        return stats

    def update(self, of_stats):
        """Given a pyof stats object, update attributes' values.

        Avoid object creation and memory leak. pyof values are GenericType
        instances whose native values can be accessed by `.value`.
        """
        # Generator for GenericType values
        attr_name_value = ((attr_name, gen_type.value)
                           for attr_name, gen_type in vars(of_stats).items()
                           if attr_name in vars(self))
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
        """Initialize all statistics as ``None``."""
        self.byte_count = None
        self.duration_sec = None
        self.duration_nsec = None
        self.packet_count = None


class PortStats(Stats):  # pylint: disable=too-many-instance-attributes
    """Common fields for 1.0 and 1.3 PortStats."""

    def __init__(self):
        """Initialize all statistics as ``None``."""
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
