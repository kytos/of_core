"""Module with main classes related to Flows."""
# pylint: disable=missing-docstring

from itertools import chain

from pyof.v0x04.common.action import ActionOutput as OFActionOutput
from pyof.v0x04.common.action import ActionSetField as OFActionSetField
from pyof.v0x04.common.flow_instructions import (InstructionApplyAction,
                                                 InstructionType)
from pyof.v0x04.common.flow_match import Match as OFMatch
from pyof.v0x04.common.flow_match import (OxmMatchFields, OxmOfbMatchField,
                                          OxmTLV, VlanId)
from pyof.v0x04.controller2switch.flow_mod import FlowMod

from napps.kytos.of_core.flow import (ActionBase, ActionFactoryBase, FlowBase,
                                      MatchBase)
from napps.kytos.of_core.v0x04.match_fields import MatchFieldFactory


class ActionSetVlan(ActionBase):
    """FlowAction represents a change in the vlan id."""

    def __init__(self, vlan_id):
        """Require a vlan id."""
        self.vlan_id = vlan_id
        self.action_type = 'set_vlan'

    @classmethod
    def from_of_action(cls, of_action):
        vlan_id = int.from_bytes(of_action.field.oxm_value, 'big') & 4095
        return cls(vlan_id)

    def as_of_action(self):
        tlv = OxmTLV()
        tlv.oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_VID
        oxm_value = self.vlan_id | VlanId.OFPVID_PRESENT
        tlv.oxm_value = oxm_value.to_bytes(2, 'big')
        return OFActionSetField(field=tlv)


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
        return cls(port=of_action.port.value)

    def as_of_action(self):
        return OFActionOutput(port=self.port)


class Action(ActionFactoryBase):
    """FlowAction represents a action to be executed once a flow is actived."""

    _action_class = {
        'output': ActionOutput,
        'set_vlan': ActionSetVlan,
        OFActionOutput: ActionOutput,
        OFActionSetField: ActionSetVlan
    }


class Match(MatchBase):
    """Aggregate MatchFields preserving the behavior of Flow 1.0."""

    @classmethod
    def from_of_match(cls, of_match):
        match = cls()
        match_fields = (MatchFieldFactory.from_of_tlv(tlv)
                        for tlv in of_match.oxm_match_fields)
        for field in match_fields:
            setattr(match, field.name, field.value)
        return match

    def as_of_match(self):
        """Create an OF Match with TLVs from instance attributes."""
        oxm_fields = OxmMatchFields()
        for field_name, value in self.__dict__.items():
            if value is not None:
                field = MatchFieldFactory.from_name(field_name, value)
                if field:
                    tlv = field.as_of_tlv()
                    oxm_fields.append(tlv)
        return OFMatch(oxm_match_fields=oxm_fields)


class Flow(FlowBase):
    """Behaves the same as 1.0's flow from end-user perspective.

    This subclass only defines version-specific classes.
    """

    _action_factory = Action
    _flow_mod_class = FlowMod
    _match_class = Match

    @staticmethod
    def _get_of_actions(of_flow_stats):
        # Add list of high-level actions
        # Filter action instructions
        apply_actions = InstructionType.OFPIT_APPLY_ACTIONS
        of_instructions = (ins for ins in of_flow_stats.instructions
                           if ins.instruction_type == apply_actions)
        # Get actions from a list of actions
        return chain.from_iterable(ins.actions for ins in of_instructions)

    def _as_of_flow_mod(self, command):
        of_flow_mod = super()._as_of_flow_mod(command)
        of_actions = [action.as_of_action() for action in self.actions]
        of_instruction = InstructionApplyAction(actions=of_actions)
        of_flow_mod.instructions = [of_instruction]
        print(of_flow_mod.instructions)
        return of_flow_mod
