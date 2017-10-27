"""Module with main classes related to Flows."""
# pylint: disable=missing-docstring

from abc import ABC, abstractmethod

from pyof.v0x04.common.action import ActionOutput as OFActionOutput
from pyof.v0x04.common.action import ActionSetField as OFActionSetField
from pyof.v0x04.common.flow_match import Match as OFMatch
from pyof.v0x04.common.flow_match import (OxmMatchFields, OxmTLV,
                                          OxmOfbMatchField, VlanId)
from pyof.v0x04.controller2switch.flow_mod import FlowMod

from napps.kytos.of_core.flow import Flow as FlowBase
from napps.kytos.of_core.flow import Match as MatchBase
from napps.kytos.of_core.v0x04.match_fields import MatchFieldFactory


class Action(ABC):
    """FlowAction represents a action to be executed once a flow is actived."""

    def as_dict(self):
        return self.__dict__

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
    def from_of_action(cls, action):
        if isinstance(action, OFActionOutput):
            return ActionOutput.from_of_action(action)
        elif isinstance(action, OFActionSetField):
            return ActionSetVlan.from_of_action(action)

    @abstractmethod
    def as_of_action(self):
        pass


class ActionSetVlan(Action):

    def __init__(self, vlan_id):
        self.vlan_id = vlan_id
        self.action_type = 'set_vlan'

    @classmethod
    def from_dict(cls, dict_content):
        return cls(vlan_id=dict_content['vlan_id'])

    def as_of_action(self):
        tlv = OxmTLV()
        tlv.oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_VID
        oxm_value = self.vlan_id | VlanId.OFPVID_PRESENT
        tlv.oxm_value = oxm_value.to_bytes(2, 'big')
        return OFActionSetField(field=tlv)


class ActionOutput(Action):
    def __init__(self, port=None):
        self.action_type = 'output'
        self.port = port

    @classmethod
    def from_dict(cls, dict_content):
        return cls(port=dict_content['port'])

    def as_of_action(self):
        return OFActionOutput(port=self.port)


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

    This subclass only defines version-specific classes"""

    _action_class = Action
    _flow_mod_class = FlowMod
    _match_class = Match

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats):
        pass
