"""OpenFlow 1.3 OXM match fields."""
# TODO Enable missing docstring warning after development
# pylint: disable=C0111
from abc import ABC, abstractmethod

from pyof.foundation.basic_types import HWAddress, IPAddress
from pyof.v0x04.common.flow_match import OxmTLV, OxmOfbMatchField, VlanId


class MatchField(ABC):
    """Base class for match fields. They are TLVs in python-openflow.

    Just extend this class and you will be forced to define the low-level
    attributes and methods below:

    * Attribute name (field name as displayed in JSON);
    * Attribute oxm_field (OxmOfbMatchField enum);
    * Method to return an OxmTLV;
    * Method to create an instance from an OxmTLV.
    """

    def __init__(self, value):
        self.value = value

    @property
    @classmethod
    @abstractmethod
    def name(cls):
        """Field name. Can be overriden by as a class attibute."""
        pass

    @property
    @classmethod
    @abstractmethod
    def oxm_field(cls):
        """OxmTLV.oxm_field. Can be overriden by as a class attibute."""
        pass

    @abstractmethod
    def as_of_tlv(self):
        pass

    @classmethod
    @abstractmethod
    def from_of_tlv(cls, tlv):
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.value == self.value


class MatchDLVLAN(MatchField):

    name = 'dl_vlan'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_VID

    def as_of_tlv(self):
        value = self.value | VlanId.OFPVID_PRESENT
        value_bytes = value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        vlan_id = int.from_bytes(tlv.oxm_value, 'big') & 4095
        return cls(vlan_id)


class MatchDLVLANPCP(MatchField):

    name = 'dl_vlan_pcp'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_PCP

    def as_of_tlv(self):
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchDLSrc(MatchField):

    name = 'dl_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ETH_SRC

    def as_of_tlv(self):
        value_bytes = HWAddress(self.value).pack()
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        hw_address = HWAddress()
        hw_address.unpack(tlv.oxm_value)
        addr_str = str(hw_address)
        return cls(addr_str)


class MatchDLDst(MatchField):

    name = 'dl_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ETH_DST

    def as_of_tlv(self):
        value_bytes = HWAddress(self.value).pack()
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        hw_address = HWAddress()
        hw_address.unpack(tlv.oxm_value)
        addr_str = str(hw_address)
        return cls(addr_str)


class MatchDLType(MatchField):

    name = 'dl_type'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ETH_TYPE

    def as_of_tlv(self):
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchNwSrc(MatchField):

    name = 'nw_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV4_SRC

    def as_of_tlv(self):
        value_bytes = IPAddress(self.value).pack()
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        ip_address = IPAddress()
        ip_address.unpack(tlv.oxm_value)
        ip_str = str(ip_address)
        return cls(ip_str)


class MatchNwDst(MatchField):

    name = 'nw_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV4_DST

    def as_of_tlv(self):
        value_bytes = IPAddress(self.value).pack()
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        ip_address = IPAddress()
        ip_address.unpack(tlv.oxm_value)
        ip_str = str(ip_address)
        return cls(ip_str)


class MatchNwProto(MatchField):

    name = 'nw_proto'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IP_PROTO

    def as_of_tlv(self):
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchInPort(MatchField):

    name = 'in_port'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IN_PORT

    def as_of_tlv(self):
        value_bytes = self.value.to_bytes(4, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchTCPSrc(MatchField):

    name = 'tp_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_TCP_SRC

    def as_of_tlv(self):
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchTCPDst(MatchField):

    name = 'tp_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_TCP_DST

    def as_of_tlv(self):
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchFieldFactory(ABC):
    """Create the correct MatchField subclass instance.

    As OF 1.3 has many match fields and there are many ways to (un)pack their
    OxmTLV.oxm_value, this class does all the work of finding the correct
    MatchField class and instantiating the corresponding object.
    """

    __classes = {}

    @classmethod
    def from_name(cls, name, value):
        field_class = cls._get_class(name)
        if field_class:
            return field_class(value)

    @classmethod
    def from_of_tlv(cls, tlv):
        field_class = cls._get_class(tlv.oxm_field)
        if field_class:
            return field_class.from_of_tlv(tlv)

    @classmethod
    def _get_class(cls, name_or_field):
        """Return the proper object by field name or OxmTLV.oxm_field."""
        if not cls.__classes:
            cls._index_classes()
        return cls.__classes.get(name_or_field)

    @classmethod
    def _index_classes(cls):
        for subclass in MatchField.__subclasses__():
            cls.__classes[subclass.name] = subclass
            cls.__classes[subclass.oxm_field] = subclass
