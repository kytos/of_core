"""Module with main classes related to Flows."""
# pylint: disable=missing-docstring

from pyof.v0x01.common.action import ActionOutput as OFActionOutput
from pyof.v0x01.common.action import ActionVlanVid as OFActionVlanVid
from pyof.v0x01.common.flow_match import Match as OFMatch
from pyof.v0x01.controller2switch.flow_mod import FlowMod

from napps.kytos.of_core.flow import (ActionBase, ActionFactoryBase, FlowBase,
                                      MatchBase)


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


class ActionOutput(ActionBase):
    """FlowAction represents a change in forwarding network into a port."""

    def __init__(self, port):
        """Require an output port.

        Args:
            port (int): Specific port number.
        """
        self.port = port
        self.action_type = 'output'

    @classmethod
    def from_of_action(cls, of_action):
        return ActionOutput(port=of_action.port.value)

    def as_of_action(self):
        return OFActionOutput(port=self.port)


class ActionSetVlan(ActionBase):
    """FlowAction represents a change in the vlan id."""

    def __init__(self, vlan_id):
        """Require a vlan id."""
        self.vlan_id = vlan_id
        self.action_type = 'set_vlan'

    @classmethod
    def from_of_action(cls, of_action):
        return cls(vlan_id=of_action.vlan_id.value)

    def as_of_action(self):
        return OFActionVlanVid(vlan_id=self.vlan_id)


class Action(ActionFactoryBase):
    """FlowAction represents a action to be executed once a flow is actived."""

    _action_class = {
        'output': ActionOutput,
        'set_vlan': ActionSetVlan,
        OFActionOutput: ActionOutput,
        OFActionVlanVid: ActionSetVlan
    }


class Flow(FlowBase):
    """Behaves the same as 1.0's flow from end-user perspective.

    This subclass only defines version-specific classes.
    """

    _action_factory = Action
    _flow_mod_class = FlowMod
    _match_class = Match

    @staticmethod
    def _get_of_actions(of_flow_stats):
        return of_flow_stats.actions

    def _as_of_flow_mod(self, command):
        flow_mod = super()._as_of_flow_mod(command)
        flow_mod.actions = [action.as_of_action() for action in self.actions]
        return flow_mod
