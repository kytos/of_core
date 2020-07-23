"""OpenFlow 1.3 OXM match fields.

Flow's match is very different from OF 1.0. Instead of always having all
fields, there's a variable list of match fields and each one is an Openflow
eXtended Match Type-Length-Value (OXM TLV) element.

This module provides high-level Python classes for OXM TLV fields in order to
make the OF 1.3 match fields easy to use and to be coded.
"""
from abc import ABC, abstractmethod

from pyof.foundation.basic_types import HWAddress, IPAddress, IPV6Address
from pyof.v0x04.common.flow_match import OxmOfbMatchField, OxmTLV, VlanId

from napps.kytos.of_core.v0x04.utils import bytes_to_mask, mask_to_bytes


class MatchField(ABC):
    """Base class for match fields. Abstract OXM TLVs of python-openflow.

    Just extend this class and you will be forced to define the required
    low-level attributes and methods below:

    * "name" attribute (field name to be displayed in JSON);
    * "oxm_field" attribute (``OxmOfbMatchField`` enum);
    * Method to return a pyof OxmTLV;
    * Method to create an instance from an OxmTLV.
    """

    def __init__(self, value):
        """Define match field value."""
        self.value = value

    @property
    @classmethod
    @abstractmethod
    def name(cls):
        """Define a name to be displayed in JSON.

        It can be overriden just by a class attibute.
        """

    @property
    @classmethod
    @abstractmethod
    def oxm_field(cls):
        """Define this subclass ``OxmOfbMatchField`` value.

        It can be overriden just by as a class attibute.
        """

    @abstractmethod
    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""

    @classmethod
    @abstractmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""

    def __eq__(self, other):
        """Two objects are equal if their values are the same.

        The oxm_field equality is checked indirectly when comparing whether
        the objects are instances of the same class.
        """
        return isinstance(other, self.__class__) and other.value == self.value


class MatchDLVLAN(MatchField):
    """Match for datalink VLAN ID."""

    name = 'dl_vlan'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_VID

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        try:
            value = int(self.value)
            mask = None
            oxm_hasmask = False
        except ValueError:
            value, mask = map(int, self.value.split('/'))
            oxm_hasmask = True
        value = value | VlanId.OFPVID_PRESENT
        value_bytes = value.to_bytes(2, 'big')
        if mask:
            mask = mask | VlanId.OFPVID_PRESENT
            value_bytes += mask.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        vlan_id = int.from_bytes(tlv.oxm_value[:2], 'big') & 4095
        value = vlan_id
        if tlv.oxm_hasmask:
            vlan_mask = int.from_bytes(tlv.oxm_value[2:], 'big') & 4095
            value = f'{vlan_id}/{vlan_mask}'
        return cls(value)


class MatchDLVLANPCP(MatchField):
    """Match for VLAN Priority Code Point."""

    name = 'dl_vlan_pcp'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_PCP

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchDLSrc(MatchField):
    """Match for datalink source."""

    name = 'dl_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ETH_SRC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        if '/' in self.value:
            value, mask = self.value.split('/')
            mask = mask.upper()
            if mask == 'FF:FF:FF:FF:FF:FF':
                mask = None
                oxm_hasmask = False
            else:
                oxm_hasmask = True
        else:
            value = self.value
            mask = None
            oxm_hasmask = False
        value_bytes = HWAddress(value).pack()
        if mask:
            value_bytes += HWAddress(mask).pack()
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        hw_address = HWAddress()
        hw_address.unpack(tlv.oxm_value)
        addr_str = str(hw_address)
        value = addr_str
        if tlv.oxm_hasmask:
            hw_mask = HWAddress()
            hw_mask.unpack(tlv.oxm_value[6:])
            mask_str = str(hw_mask)
            value = f'{addr_str}/{mask_str}'
        return cls(value)


class MatchDLDst(MatchField):
    """Match for datalink destination."""

    name = 'dl_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ETH_DST

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        if '/' in self.value:
            value, mask = self.value.split('/')
            mask = mask.upper()
            if mask == 'FF:FF:FF:FF:FF:FF':
                mask = None
                oxm_hasmask = False
            else:
                oxm_hasmask = True
        else:
            value = self.value
            mask = None
            oxm_hasmask = False
        value_bytes = HWAddress(value).pack()
        if mask:
            value_bytes += HWAddress(mask).pack()
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        hw_address = HWAddress()
        hw_address.unpack(tlv.oxm_value)
        addr_str = str(hw_address)
        value = addr_str
        if tlv.oxm_hasmask:
            hw_mask = HWAddress()
            hw_mask.unpack(tlv.oxm_value[6:])
            mask_str = str(hw_mask)
            value = f'{addr_str}/{mask_str}'
        return cls(value)


class MatchDLType(MatchField):
    """Match for datalink type."""

    name = 'dl_type'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ETH_TYPE

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchNwSrc(MatchField):
    """Match for IPV4 source."""

    name = 'nw_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV4_SRC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPAddress(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 32:
            value_bytes += mask_to_bytes(ip_addr.netmask, 32)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 32,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPAddress()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[4:], 32)}'
        return cls(value)


class MatchNwDst(MatchField):
    """Match for IPV4 destination."""

    name = 'nw_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV4_DST

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPAddress(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 32:
            value_bytes += mask_to_bytes(ip_addr.netmask, 32)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 32,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPAddress()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[4:], 32)}'
        return cls(value)


class MatchNwProto(MatchField):
    """Match for IP protocol."""

    name = 'nw_proto'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IP_PROTO

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchInPort(MatchField):
    """Match for input port."""

    name = 'in_port'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IN_PORT

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(4, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchTCPSrc(MatchField):
    """Match for TCP source."""

    name = 'tp_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_TCP_SRC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchTCPDst(MatchField):
    """Match for TCP destination."""

    name = 'tp_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_TCP_DST

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchSCTPSrc(MatchField):
    """Match for SCTP source."""

    name = 'sctp_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_SCTP_SRC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchSCTPDst(MatchField):
    """Match for SCTP destination."""

    name = 'sctp_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_SCTP_DST

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchARPSPA(MatchField):
    """Match for ARP Sender IP Address."""

    name = 'arp_spa'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ARP_SPA

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPAddress(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 32:
            value_bytes += mask_to_bytes(ip_addr.netmask, 32)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 32,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPAddress()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[4:], 32)}'
        return cls(value)


class MatchARPTPA(MatchField):
    """Match for ARP Target IP Address."""

    name = 'arp_tpa'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ARP_TPA

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPAddress(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 32:
            value_bytes += mask_to_bytes(ip_addr.netmask, 32)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 32,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPAddress()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[4:], 32)}'
        return cls(value)


class MatchARPSHA(MatchField):
    """Match for ARP Sender MAC Address."""

    name = 'arp_sha'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ARP_SHA

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        if '/' in self.value:
            value, mask = self.value.split('/')
            mask = mask.upper()
            if mask == 'FF:FF:FF:FF:FF:FF':
                mask = None
                oxm_hasmask = False
            else:
                oxm_hasmask = True
        else:
            value = self.value
            mask = None
            oxm_hasmask = False
        value_bytes = HWAddress(value).pack()
        if mask:
            value_bytes += HWAddress(mask).pack()
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        hw_address = HWAddress()
        hw_address.unpack(tlv.oxm_value)
        addr_str = str(hw_address)
        value = addr_str
        if tlv.oxm_hasmask:
            hw_mask = HWAddress()
            hw_mask.unpack(tlv.oxm_value[6:])
            mask_str = str(hw_mask)
            value = f'{addr_str}/{mask_str}'
        return cls(value)


class MatchARPTHA(MatchField):
    """Match for ARP Target MAC Address."""

    name = 'arp_tha'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ARP_THA

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        if '/' in self.value:
            value, mask = self.value.split('/')
            mask = mask.upper()
            if mask == 'FF:FF:FF:FF:FF:FF':
                mask = None
                oxm_hasmask = False
            else:
                oxm_hasmask = True
        else:
            value = self.value
            mask = None
            oxm_hasmask = False
        value_bytes = HWAddress(value).pack()
        if mask:
            value_bytes += HWAddress(mask).pack()
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        hw_address = HWAddress()
        hw_address.unpack(tlv.oxm_value)
        addr_str = str(hw_address)
        value = addr_str
        if tlv.oxm_hasmask:
            hw_mask = HWAddress()
            hw_mask.unpack(tlv.oxm_value[6:])
            mask_str = str(hw_mask)
            value = f'{addr_str}/{mask_str}'
        return cls(value)


class MatchIPV6Src(MatchField):
    """Match for IPV6 source."""

    name = 'ipv6_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_SRC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPV6Address(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 128:
            value_bytes += mask_to_bytes(ip_addr.netmask, 128)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 128,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPV6Address()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[16:], 128)}'
        return cls(value)


class MatchIPV6Dst(MatchField):
    """Match for IPV6 destination."""

    name = 'ipv6_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_DST

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPV6Address(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 128:
            value_bytes += mask_to_bytes(ip_addr.netmask, 128)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 128,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPV6Address()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[16:], 128)}'
        return cls(value)


class MatchMPLSLabel(MatchField):
    """Match for MPLS Label."""

    name = 'mpls_lab'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_MPLS_LABEL

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(4, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        lab = int.from_bytes(tlv.oxm_value, 'big')
        return cls(lab)


class MatchMPLSTC(MatchField):
    """Match for MPLS TC."""

    name = 'mpls_tc'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_MPLS_TC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value, 'big')
        return cls(value)


class MatchMPLSBOS(MatchField):
    """Match for MPLS BOS."""

    name = 'mpls_bos'
    oxm_field = OxmOfbMatchField.OFPXMT_OFP_MPLS_BOS

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        bos = int.from_bytes(tlv.oxm_value, 'big')
        return cls(bos)


class MatchMetadata(MatchField):
    """Match for table metadata."""

    name = 'metadata'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_METADATA

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        try:
            value = int(self.value)
            mask = None
            oxm_hasmask = False
        except ValueError:
            value, mask = map(int, self.value.split('/'))
            oxm_hasmask = True
        value_bytes = value.to_bytes(8, 'big')
        if mask:
            value_bytes += mask.to_bytes(8, 'big')
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value[:8], 'big')
        if tlv.oxm_hasmask:
            metadata_mask = int.from_bytes(tlv.oxm_value[8:], 'big')
            value = f'{value}/{metadata_mask}'
        return cls(value)


class MatchTunnelID(MatchField):
    """Match for tunnel id."""

    name = 'tun_id'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_TUNNEL_ID

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        try:
            value = int(self.value)
            mask = None
            oxm_hasmask = False
        except ValueError:
            value, mask = map(int, self.value.split('/'))
            oxm_hasmask = True
        value_bytes = value.to_bytes(8, 'big')
        if mask:
            value_bytes += mask.to_bytes(8, 'big')
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value[:8], 'big')
        if tlv.oxm_hasmask:
            tunnel_mask = int.from_bytes(tlv.oxm_value[8:], 'big')
            value = f'{value}/{tunnel_mask}'
        return cls(value)


class MatchFieldFactory(ABC):
    """Create the correct MatchField subclass instance.

    As OF 1.3 has many match fields and there are many ways to (un)pack their
    OxmTLV.oxm_value, this class does all the work of finding the correct
    MatchField class and instantiating the corresponding object.
    """

    __classes = {}

    @classmethod
    def from_name(cls, name, value):
        """Return the proper object from name and value."""
        field_class = cls._get_class(name)
        if field_class:
            return field_class(value)
        return None

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return the proper object from a pyof OXM TLV."""
        field_class = cls._get_class(tlv.oxm_field)
        if field_class:
            return field_class.from_of_tlv(tlv)
        return None

    @classmethod
    def _get_class(cls, name_or_field):
        """Return the proper object from field name or OxmTLV.oxm_field."""
        if not cls.__classes:
            cls._index_classes()
        return cls.__classes.get(name_or_field)

    @classmethod
    def _index_classes(cls):
        for subclass in MatchField.__subclasses__():
            cls.__classes[subclass.name] = subclass
            cls.__classes[subclass.oxm_field] = subclass
