"""Module with main classes related to Flows."""

import hashlib
import json

from napps.kytos.of_core.flow import Flow as FlowBase
from napps.kytos.of_core.flow import Match as MatchBase

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
        actions = [ action.as_dict() for action in self.actions ]
        match = self.match.as_dict()

        fields = [self.switch.id, self.table_id, match, self.priority,
                  self.idle_timeout, self.hard_timeout, self.cookie, actions]

        hash_result = hashlib.md5()
        for field in fields:
            hash_result.update(str(field).encode('utf-8'))

        return hash_result.hexdigest()

    def as_dict(self):
        flow = super().as_dict()
        flow["actions"] = [ action.as_dict() for action in self.actions ]
        return flow


class Match(MatchBase):
    pass


class Action(object):
    """FlowAction represents a action to be executed once a flow is actived."""

    @staticmethod
    def from_dict(dict_content):
        """Build one of the Actions from a dictionary.

        Args:
            dict_content (dict): Python dictionary to build a FlowAction.
        """
        pass


class ActionOutput(Action):
    """FlowAction represents a change in forwarding network into a port."""

    def __init__(self, output_port):
        """Require an output port.

        Args:
            output_port (int): Specific port number.
        """
        self.output_port = output_port

    def as_dict(self):
        """Return this action as a python dictionary.

        Returns:
            dictionary (dict): Dict that represent a ActionOutput.

        """
        return {"type": "action_output",
                "port": self.output_port}

    def from_dict(dict_content):
        """Build an ActionOutput from a dictionary.

        Args:
            dict_content (dict): Python dictionary with ActionOutput attribute.

        Returns:
            :class:`ActionOutput`: A instance of ActionOutput.

        """
        return ActionOutput(output_port=dict_content['port'])
