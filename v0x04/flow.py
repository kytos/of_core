"""Deal with OpenFlow 1.3 specificities related to flows."""
from itertools import chain

from pyof.foundation.network_types import EtherType
from pyof.v0x04.common.action import ActionOutput as OFActionOutput
from pyof.v0x04.common.action import ActionPopVLAN as OFActionPopVLAN
from pyof.v0x04.common.action import ActionPush as OFActionPush
from pyof.v0x04.common.action import ActionSetField as OFActionSetField
from pyof.v0x04.common.action import ActionType
from pyof.v0x04.common.flow_instructions import (InstructionApplyAction,
                                                 InstructionType)
from pyof.v0x04.common.flow_match import Match as OFMatch
from pyof.v0x04.common.flow_match import (OxmMatchFields, OxmOfbMatchField,
                                          OxmTLV, VlanId)
from pyof.v0x04.controller2switch.flow_mod import FlowMod

from napps.kytos.of_core.flow import (ActionBase, ActionFactoryBase, FlowBase,
                                      FlowStats, MatchBase, PortStats)
from napps.kytos.of_core.v0x04.match_fields import MatchFieldFactory

__all__ = ('ActionOutput', 'ActionSetVlan', 'Action', 'Flow', 'FlowStats',
           'PortStats')


class Match(MatchBase):
    """High-level Match for OpenFlow 1.3 match fields."""

    @classmethod
    def from_of_match(cls, of_match):
        """Return an instance from a pyof Match."""
        match = cls()
        match_fields = (MatchFieldFactory.from_of_tlv(tlv)
                        for tlv in of_match.oxm_match_fields)
        for field in match_fields:
            if field is not None:
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


class ActionOutput(ActionBase):
    """Action with an output port."""

    def __init__(self, port):
        """Require an output port.

        Args:
            port (int): Specific port number.
        """
        self.port = port
        self.action_type = 'output'

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high-level ActionOuput instance from pyof ActionOutput."""
        return cls(port=of_action.port.value)

    def as_of_action(self):
        """Return a pyof ActionOuput instance."""
        return OFActionOutput(port=self.port)


class ActionPopVlan(ActionBase):
    """Action to pop the outermost VLAN tag."""

    def __init__(self):
        """Initialize the action with the correct action_type."""
        self.action_type = 'pop_vlan'

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high-level ActionPopVlan instance from the pyof class."""
        return cls()

    def as_of_action(self):
        """Return a pyof ActionPopVLAN instance."""
        return OFActionPopVLAN()


class ActionPushVlan(ActionBase):
    """Action to push a VLAN tag."""

    def __init__(self, tag_type):
        """Require a tag_type for the VLAN."""
        self.action_type = 'push_vlan'
        self.tag_type = tag_type

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high level ActionPushVlan instance from pyof ActionPush."""
        if of_action.ethertype.value == EtherType.VLAN_QINQ:
            return cls(tag_type='s')
        return cls(tag_type='c')

    def as_of_action(self):
        """Return a pyof ActionPush instance."""
        if self.tag_type == 's':
            return OFActionPush(action_type=ActionType.OFPAT_PUSH_VLAN,
                                ethertype=EtherType.VLAN_QINQ)
        return OFActionPush(action_type=ActionType.OFPAT_PUSH_VLAN,
                            ethertype=EtherType.VLAN)


class ActionSetVlan(ActionBase):
    """Action to set VLAN ID."""

    def __init__(self, vlan_id):
        """Require a VLAN ID."""
        self.vlan_id = vlan_id
        self.action_type = 'set_vlan'

    @classmethod
    def from_of_action(cls, of_action):
        """Return high-level ActionSetVlan object from pyof ActionSetField."""
        vlan_id = int.from_bytes(of_action.field.oxm_value, 'big') & 4095
        return cls(vlan_id)

    def as_of_action(self):
        """Return a pyof ActionSetField instance."""
        tlv = OxmTLV()
        tlv.oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_VID
        oxm_value = self.vlan_id | VlanId.OFPVID_PRESENT
        tlv.oxm_value = oxm_value.to_bytes(2, 'big')
        return OFActionSetField(field=tlv)


class Action(ActionFactoryBase):
    """An action to be executed once a flow is activated.

    This class behavies like a factory but has no "Factory" suffix for end-user
    usability issues.
    """

    # Set v0x04 classes for action types and pyof classes
    _action_class = {
        'output': ActionOutput,
        'set_vlan': ActionSetVlan,
        'push_vlan': ActionPushVlan,
        'pop_vlan': ActionPopVlan,
        OFActionOutput: ActionOutput,
        OFActionSetField: ActionSetVlan,
        OFActionPush: ActionPushVlan,
        OFActionPopVLAN: ActionPopVlan
    }


class Flow(FlowBase):
    """High-level flow representation for OpenFlow 1.0.

    This is a subclass that only deals with 1.3 flow actions.
    """

    _action_factory = Action
    _flow_mod_class = FlowMod
    _match_class = Match

    def __init__(self, *args, cookie_mask=0, **kwargs):
        """Require a cookie mask."""
        super().__init__(*args, **kwargs)
        self.cookie_mask = cookie_mask

    @staticmethod
    def _get_of_actions(of_flow_stats):
        """Return the pyof actions from pyof ``FlowStats.instructions``."""
        # Add list of high-level actions
        # Filter action instructions
        apply_actions = InstructionType.OFPIT_APPLY_ACTIONS
        of_instructions = (ins for ins in of_flow_stats.instructions
                           if ins.instruction_type == apply_actions)
        # Get actions from a list of actions
        return chain.from_iterable(ins.actions for ins in of_instructions)

    def _as_of_flow_mod(self, command):
        """Return pyof FlowMod with a ``command`` to add or delete a flow.

        Actions become items of the ``instructions`` attribute.
        """
        of_flow_mod = super()._as_of_flow_mod(command)
        of_flow_mod.cookie_mask = self.cookie_mask
        of_actions = [action.as_of_action() for action in self.actions]
        of_instruction = InstructionApplyAction(actions=of_actions)
        of_flow_mod.instructions = [of_instruction]
        return of_flow_mod
