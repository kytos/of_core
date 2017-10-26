"""Module with main classes related to Flows."""
# TODO Enable missing docstring warning after development
# pylint: disable=C0111

import hashlib

from napps.kytos.of_core.flow import Flow as FlowBase
from napps.kytos.of_core.flow import Match as MatchBase

from pyof.v0x01.controller2switch.flow_mod import FlowMod, FlowModCommand
from pyof.v0x01.common.flow_match import Match as OFMatch
from pyof.v0x01.common.action import ActionOutput as OFActionOutput
from pyof.v0x01.common.action import ActionVlanVid as OFActionVlanVid


class Flow(FlowBase):
    """Class to abstract a Flow to OF 1.0 switches.

    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """

    def __init__(self, *args, match=None, actions=None, **kwargs):
        kwargs['match'] = match or Match()
        super().__init__(*args, **kwargs)
        self.actions = actions or []

    @property
    def id(self):  # pylint: disable=invalid-name
        """Return the hash of the object.

        Calculates the hash of the object by using the hashlib we use md5 of
        strings.

        Returns:
            string: Hash of object.

        """
        actions = [action.as_dict() for action in self.actions]
        match = self.match.as_dict()

        fields = [self.switch.id, self.table_id, match, self.priority,
                  self.idle_timeout, self.hard_timeout, self.cookie, actions]

        hash_result = hashlib.md5()
        for field in fields:
            hash_result.update(str(field).encode('utf-8'))

        return hash_result.hexdigest()

    def as_dict(self):
        flow = super().as_dict()
        flow["actions"] = [action.as_dict() for action in self.actions]
        return flow

    def as_add_flow_mod(self):
        return self.as_flow_mod(FlowModCommand.OFPFC_ADD)

    def as_delete_flow_mod(self):
        return self.as_flow_mod(FlowModCommand.OFPFC_DELETE)

    def as_flow_mod(self, command):
        actions = [action.as_of_action() for action in self.actions]
        flow_mod = FlowMod(match=self.match.as_of_match(),
                           cookie=self.cookie,
                           command=command,
                           idle_timeout=self.idle_timeout,
                           hard_timeout=self.hard_timeout,
                           priority=self.priority,
                           actions=actions)
        return flow_mod

    @classmethod
    def from_of_flow_stats(cls, flow_stats, switch):
        actions = [Action.from_of_action(a) for a in flow_stats.actions]
        flow = cls(switch=switch,
                   table_id=flow_stats.table_id.value,
                   match=Match.from_of_match(flow_stats.match),
                   priority=flow_stats.priority.value,
                   idle_timeout=flow_stats.idle_timeout.value,
                   hard_timeout=flow_stats.hard_timeout.value,
                   cookie=flow_stats.cookie.value,
                   actions=actions)
        return flow

    @classmethod
    def from_dict(cls, dict_content, switch):
        flow = cls(switch=switch)

        for key, value in dict_content.items():
            if key in flow.__dict__:
                setattr(flow, key, value)

        if 'match' in dict_content:
            flow.match = Match.from_dict(dict_content['match'])

        flow.actions = []
        if 'actions' in dict_content:
            for action_dict in dict_content['actions']:
                action = Action.from_dict(action_dict)
                flow.actions.append(action)

        return flow


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
