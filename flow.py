"""Module with main classes related to Flows."""
# TODO Enable missing docstring warning after development
# pylint: disable=C0111

import json
from abc import ABC, abstractmethod


class Flow(ABC):  # pylint: disable=too-many-instance-attributes
    """Class to abstract a Flow to switches.

    This class represents a Flow installed or to be installed inside the
    switch. A flow, in this case is represented by a Match object and a set of
    actions that should occur in case any match happen.
    """

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(self, switch, table_id=0xff, match=None, priority=0,
                 idle_timeout=0, hard_timeout=0, cookie=0, actions=None):
        """Assign parameters to attributes.

        Args:
            table_id (int): The index of a single table or 0xff for all tables.
            match (|match|): Match object..
            priority (int): Priority level of flow entry.
            idle_timeout (int): Idle time before discarding in seconds.
            hard_timeout (int): Max time before discarding in seconds.
            cookie (int): Opaque controller-issued identifier.
            actions (|list_of_actions|): List of action to apply.
        """
        self.switch = switch
        self.table_id = table_id
        self.match = match
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout
        self.cookie = cookie
        self.actions = actions or []
        self.stats = {}

    @property
    @abstractmethod
    def id(self):  # pylint: disable=invalid-name
        """Return the hash of the object.

        Calculates the hash of the object by using the hashlib we use md5 of
        strings.

        You MUST implement this method in your child class.

        Returns:
            string: Hash of object.

        """
        pass

    def as_dict(self):
        """Return the representation of a flow as a python dictionary.

        Returns:
            dict: Dictionary using flow attributes.

        """
        match = self.match.as_dict() if self.match else None

        return {"id": self.id,
                "table_id": self.table_id,
                "match": match,
                "priority": self.priority,
                "idle_timeout": self.idle_timeout,
                "hard_timeout": self.hard_timeout,
                "cookie": self.cookie}

    def as_json(self):
        """Return the representation of a flow in a json format.

        Returns:
            string: Json string using flow attributes.

        """
        return json.dumps(self.as_dict())

    def as_flow_mod(self):
        pass


class Match:  # pylint: disable=too-many-instance-attributes
    def __init__(self, in_port=None, dl_src=None, dl_dst=None, dl_vlan=None,
                 dl_vlan_pcp=None, dl_type=None, nw_tos=None, nw_proto=None,
                 nw_src=None, nw_dst=None, tp_src=None, tp_dst=None):
        # pylint: disable=too-many-arguments
        self.in_port = in_port
        self.dl_src = dl_src
        self.dl_dst = dl_dst
        self.dl_vlan = dl_vlan
        self.dl_vlan_pcp = dl_vlan_pcp
        self.dl_type = dl_type
        self.nw_tos = nw_tos
        self.nw_proto = nw_proto
        self.nw_src = nw_src
        self.nw_dst = nw_dst
        self.tp_src = tp_src
        self.tp_dst = tp_dst

    def as_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, dict_content):
        match = cls()
        for key, value in dict_content.items():
            if key in match.__dict__:
                setattr(match, key, value)
        return match
