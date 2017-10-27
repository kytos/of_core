"""Module with main classes related to Flows."""
# pylint: disable=missing-docstring

from napps.kytos.of_core.flow import Flow as FlowBase
from napps.kytos.of_core.flow import Match as MatchBase
from napps.kytos.of_core.flow import Stats

from pyof.v0x01.controller2switch.flow_mod import FlowMod
from pyof.v0x01.common.flow_match import Match as OFMatch
from pyof.v0x01.common.action import ActionOutput as OFActionOutput
from pyof.v0x01.common.action import ActionVlanVid as OFActionVlanVid


class Match(MatchBase):
    @classmethod
    def from_of_match(cls, of_match):
        match = cls(in_port=of_match.in_port.value,
                    dl_src=of_match.dl_src.value,
                    dl_dst=of_match.dl_dst.value,
                    dl_vlan=of_match.dl_vlan.value,
                    dl_vlan_pcp=of_match.dl_vlan_pcp.value,
                    dl_type=of_match.dl_type.value,
                    nw_proto=of_match.nw_proto.value,
                    nw_src=of_match.nw_src.value,
                    nw_dst=of_match.nw_dst.value,
                    tp_src=of_match.tp_src.value,
                    tp_dst=of_match.tp_dst.value)
        return match

    def as_of_match(self):
        match = OFMatch()
        for field, value in self.__dict__.items():
            if value is not None:
                setattr(match, field, value)
        return match


class Action:
    """FlowAction represents a action to be executed once a flow is actived."""

    @staticmethod
    def from_dict(dict_content):
        """Build one of the Actions from a dictionary.

        Args:
            dict_content (dict): Python dictionary to build a FlowAction.
        """
        if dict_content['action_type'] == 'output':
            return ActionOutput.from_dict(dict_content)
        elif dict_content['action_type'] == 'set_vlan':
            return ActionSetVlan.from_dict(dict_content)

    @classmethod
    def from_of_action(cls, of_action):
        if isinstance(of_action, OFActionOutput):
            return ActionOutput.from_of_action(of_action)
        elif isinstance(of_action, OFActionVlanVid):
            return ActionSetVlan.from_of_action(of_action)


class ActionOutput(Action):
    """FlowAction represents a change in forwarding network into a port."""

    def __init__(self, port):
        """Require an output port.

        Args:
            port (int): Specific port number.
        """
        self.port = port

    def as_dict(self):
        """Return this action as a python dictionary.

        Returns:
            dictionary (dict): Dict that represent a ActionOutput.

        """
        return {"action_type": "output",
                "port": self.port}

    @classmethod
    def from_dict(cls, dict_content):
        """Build an ActionOutput from a dictionary.

        Args:
            dict_content (dict): Python dictionary with ActionOutput attribute.

        Returns:
            :class:`ActionOutput`: A instance of ActionOutput.

        """
        return cls(port=dict_content['port'])

    @classmethod
    def from_of_action(cls, of_action):
        return ActionOutput(port=of_action.port.value)

    def as_of_action(self):
        return OFActionOutput(port=self.port)


class ActionSetVlan(Action):
    """FlowAction represents a change in the vlan id."""

    def __init__(self, vlan_id):
        """Require a vlan id.

        """
        self.vlan_id = vlan_id

    def as_dict(self):
        """Return this action as a python dictionary.

        Returns:
            dictionary (dict): Dict that represent a ActionSetVlan.

        """
        return {"action_type": "set_vlan",
                "vlan_id": self.vlan_id}

    @classmethod
    def from_dict(cls, dict_content):
        """Build an ActionSetVlan from a dictionary.

        Args:
            dict_content (dict): Python dictionary with attributes.

        Returns:
            :class:`ActionSetVlan`: A instance of ActionSetVlan.

        """
        return cls(vlan_id=dict_content['vlan_id'])

    @classmethod
    def from_of_action(cls, of_action):
        return cls(vlan_id=of_action.vlan_id.value)

    def as_of_action(self):
        return OFActionVlanVid(vlan_id=self.vlan_id)


class FlowStats(Stats):

    def __init__(self):
        self.byte_count = None
        self.duration_sec = None
        self.duration_nsec = None
        self.packet_count = None

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats):
        stats = cls()
        of_attributes = vars(of_flow_stats).items()
        for stats_name, value in of_attributes:
            if hasattr(stats, stats_name):
                setattr(stats, stats_name, value.value)
        return stats


class Flow(FlowBase):
    """Behaves the same as 1.0's flow from end-user perspective.

    This subclass only defines version-specific classes"""

    _action_class = Action
    _flow_mod_class = FlowMod
    _match_class = Match
    _stats_class = FlowStats

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats, switch):
        """Create a flow with stats latest based on pyof FlowStats."""
        return Flow(switch,
                    table_id=of_flow_stats.table_id.value,
                    match=Match.from_of_match(of_flow_stats.match),
                    priority=of_flow_stats.priority.value,
                    idle_timeout=of_flow_stats.idle_timeout.value,
                    hard_timeout=of_flow_stats.hard_timeout.value,
                    cookie=of_flow_stats.cookie.value,
                    actions=[Action.from_of_action(of_action)
                             for of_action in of_flow_stats.actions
                             if of_action is not None],
                    stats=FlowStats.from_of_flow_stats(of_flow_stats))
