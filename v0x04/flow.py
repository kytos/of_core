"""Module with main classes related to Flows."""

import hashlib
import json

from abc import ABC
from napps.kytos.of_core.flow import Flow as FlowBase
from napps.kytos.of_core.flow import Match as MatchBase

class Flow(FlowBase):
    """Class to abstract a Flow to OF 1.0 switches.

    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """
    def __init__(self, *args, match=None, flags=None, instructions=None,
                 **kwargs):
        kwargs['match'] = match or Match()
        super().__init__(*args, **kwargs)
        self.flags = flags
        self.instructions = instructions or []

    @property
    def id(self):  # pylint: disable=invalid-name
        """Return the hash of the object.

        Calculates the hash of the object by using the hashlib we use md5 of
        strings.

        Returns:
            string: Hash of object.

        """
        instructions = [ i.as_dict() for i in self.instructions ]
        match = self.match.as_dict()

        fields = [self.switch.id, self.table_id, match, self.priority,
                  self.idle_timeout, self.hard_timeout, self.cookie,
                  self.flags, instructions]

        hash_result = hashlib.md5()
        for field in fields:
            hash_result.update(str(field).encode('utf-8'))

        return hash_result.hexdigest()

    def as_dict(self):
        flow = super().as_dict()
        flow["flags"] = self.flags
        flow["instructions"] = [ i.as_dict() for i in self.instructions ]
        return flow


class InstructionApplyAction:
    def __init__(self, actions=None):
        self.intruction_type = 4
        self.actions = actions or []


class ActionOutput:
    def __init__(self, port=None):
        self.action_type = 0
        self.port = port


class Match(MatchBase):
    pass


#class ActionSetField:
#    def __init__(self, field=None):
#        self.action_type = 25
#        self.field = field
#
#
#class Field:


#class Field(ABC):
#    def __init__(self, name, value, field_type):
#        self.name = name
#        self.value = value
#        self.field_type = field_type
#
#class InPortField(Field):
#    def __init__(self, port):
#        super().__init__('in_port', port, 0)
#
#
#class DLDstField(Field):
#    def __init__(self, dl_dst):
#        super().__init__('dl_dst', dl_src, 3)
#
#
#class DLSrcField(Field):
#    def __init__(self, dl_src):
#        super().__init__('dl_src', dl_src, 4)
#
#
#class DLTypeField(Field):
#    def __init__(self, dl_type):
#        super().__init__('dl_type', dl_type, 5)
#
#
#class DLVlanField(Field):
#    def __init__(self, dl_vlan):
#        super().__init__('dl_vlan', dl_type, 6)
#
#
#class DLVlanPCPField(Field):
#    def __init__(self, dl_vlan_pcp):
#        super().__init__('dl_vlan_pcp', dl_vlan_pcp, 7)
#
#
#class NWProtoField(Field):
#    def __init__(self, nw_proto):
#        super().__init__('nw_proto', nw_proto, 10)
#
#
#class NWSrcField(Field):
#    def __init__(self, nw_src):
#        super().__init__('nw_src', nw_src, 11)
#
#
#class NWDstField(Field):
#    def __init__(self, nw_dst):
#        super().__init__('nw_dst', nw_dst, 12)


#class Action(object):
#    """FlowAction represents a action to be executed once a flow is actived."""
#
#    @staticmethod
#    def from_dict(dict_content):
#        """Build one of the Actions from a dictionary.
#
#        Args:
#            dict_content (dict): Python dictionary to build a FlowAction.
#        """
#        pass
#
#
#class ActionOutput(Action):
#    """FlowAction represents a change in forwarding network into a port."""
#
#    def __init__(self, output_port):
#        """Require an output port.
#
#        Args:
#            output_port (int): Specific port number.
#        """
#        self.output_port = output_port
#
#    def as_dict(self):
#        """Return this action as a python dictionary.
#
#        Returns:
#            dictionary (dict): Dict that represent a ActionOutput.
#
#        """
#        return {"type": "action_output",
#                "port": self.output_port}
#
#    def from_dict(dict_content):
#        """Build an ActionOutput from a dictionary.
#
#        Args:
#            dict_content (dict): Python dictionary with ActionOutput attribute.
#
#        Returns:
#            :class:`ActionOutput`: A instance of ActionOutput.
#
#        """
#        return ActionOutput(output_port=dict_content['port'])
