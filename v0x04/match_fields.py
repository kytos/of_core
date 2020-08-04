"""OpenFlow 1.3 OXM match fields.

Flow's match is very different from OF 1.0. Instead of always having all
fields, there's a variable list of match fields and each one is an Openflow
eXtended Match Type-Length-Value (OXM TLV) element.

This module provides high-level Python classes for OXM TLV fields in order to
make the OF 1.3 match fields easy to use and to be coded.
"""

from pyof.foundation.basic_types import HWAddress, IPAddress
from pyof.v0x04.common.flow_match import OxmOfbMatchField, OxmTLV, VlanId

# pylint: disable=unused-import
from napps.kytos.of_core.v0x04.match_fields_base import (MatchField,
                                                         MatchFieldFactory)
from napps.kytos.of_core.v0x04.match_fields_ipv6 import (MatchEXTHDR,
                                                         MatchICMPV6Code,
                                                         MatchICMPV6Type,
                                                         MatchIPv6Dst,
                                                         MatchIPv6FLabel,
                                                         MatchIPv6Src,
                                                         MatchNDSLL,
                                                         MatchNDTarget,
                                                         MatchNDTLL)
# pylint: enable=unused-import
from napps.kytos.of_core.v0x04.utils import bytes_to_mask, mask_to_bytes


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


class MatchInPhyPort(MatchField):
    """Match for physical input port."""

    name = 'in_phy_port'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IN_PHY_PORT

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(4, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchIPDSCP(MatchField):
    """Match for IP DSCP."""

    name = 'ip_dscp'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IP_DSCP

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value, 'big')
        return cls(value)


class MatchIPECN(MatchField):
    """Match for IP ECN."""

    name = 'ip_ecn'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IP_ECN

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value, 'big')
        return cls(value)


class MatchUDPSrc(MatchField):
    """Match for UDP source."""

    name = 'udp_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_UDP_SRC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchUDPDst(MatchField):
    """Match for UDP destination."""

    name = 'udp_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_UDP_DST

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
        value = int.from_bytes(tlv.oxm_value, 'big')
        return cls(value)


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
        value = int.from_bytes(tlv.oxm_value, 'big')
        return cls(value)


class MatchICMPV4Type(MatchField):
    """Match for ICMPV4 type."""

    name = 'icmpv4_type'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ICMPV4_TYPE

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchICMPV4Code(MatchField):
    """Match for ICMPV4 code."""

    name = 'icmpv4_code'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ICMPV4_CODE

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchARPOP(MatchField):
    """Match for ARP opcode."""

    name = 'arp_op'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ARP_OP

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        opcode = int.from_bytes(tlv.oxm_value, 'big')
        return cls(opcode)


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


class MatchPBBISID(MatchField):
    """Match for PBB ISID."""

    name = 'pbb_isid'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_PBB_ISID

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        try:
            value = int(self.value)
            mask = None
            oxm_hasmask = False
        except ValueError:
            value, mask = map(int, self.value.split('/'))
            oxm_hasmask = True
        value_bytes = value.to_bytes(3, 'big')
        if mask:
            value_bytes += mask.to_bytes(3, 'big')
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value[:3], 'big')
        if tlv.oxm_hasmask:
            pbb_isid_mask = int.from_bytes(tlv.oxm_value[3:], 'big')
            value = f'{value}/{pbb_isid_mask}'
        return cls(value)


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


class MatchTUNNELID(MatchField):
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
