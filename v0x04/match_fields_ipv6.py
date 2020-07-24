"""IPv6 Match Fields."""

from pyof.foundation.basic_types import IPv6Address
from pyof.v0x04.common.flow_match import OxmOfbMatchField, OxmTLV

from napps.kytos.of_core.v0x04.match_fields_base import MatchField
from napps.kytos.of_core.v0x04.utils import bytes_to_mask, mask_to_bytes


class MatchIPv6Src(MatchField):
    """Match for IPv6 source."""

    name = 'ipv6_src'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_SRC

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPv6Address(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 128:
            value_bytes += mask_to_bytes(ip_addr.netmask, 128)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 128,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPv6Address()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[16:], 128)}'
        return cls(value)


class MatchIPv6Dst(MatchField):
    """Match for IPv6 destination."""

    name = 'ipv6_dst'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_DST

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        ip_addr = IPv6Address(self.value)
        value_bytes = ip_addr.pack()
        if ip_addr.netmask < 128:
            value_bytes += mask_to_bytes(ip_addr.netmask, 128)
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=ip_addr.netmask < 128,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        ip_address = IPv6Address()
        ip_address.unpack(tlv.oxm_value)
        addr_str = str(ip_address)
        value = addr_str
        if tlv.oxm_hasmask:
            value = f'{addr_str}/{bytes_to_mask(tlv.oxm_value[16:], 128)}'
        return cls(value)


class MatchIPv6FLabel(MatchField):
    """Match for IPv6 Flow Label."""

    name = 'ipv6_flabel'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_FLABEL

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        try:
            value = int(self.value)
            mask = None
            oxm_hasmask = False
        except ValueError:
            value, mask = map(int, self.value.split('/'))
            oxm_hasmask = True
        value_bytes = value.to_bytes(4, 'big')
        if mask:
            value_bytes += mask.to_bytes(4, 'big')
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value[:4], 'big')
        if tlv.oxm_hasmask:
            flabel_mask = int.from_bytes(tlv.oxm_value[4:], 'big')
            value = f'{value}/{flabel_mask}'
        return cls(value)


class MatchICMPV6Type(MatchField):
    """Match for ICMPV6 type."""

    name = 'icmpv6_type'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ICMPV6_TYPE

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        port = int.from_bytes(tlv.oxm_value, 'big')
        return cls(port)


class MatchICMPV6Code(MatchField):
    """Match for ICMPV6 code."""

    name = 'icmpv6_code'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_ICMPV6_CODE

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(1, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        priority = int.from_bytes(tlv.oxm_value, 'big')
        return cls(priority)


class MatchNDTarget(MatchField):
    """Match for IPv6 ND Target."""

    name = 'nd_tar'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_ND_TARGET

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(16, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        target = int.from_bytes(tlv.oxm_value, 'big')
        return cls(target)


class MatchNDSLL(MatchField):
    """Match for IPv6 ND SLL."""

    name = 'nd_sll'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_ND_SLL

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(6, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        sll = int.from_bytes(tlv.oxm_value, 'big')
        return cls(sll)


class MatchNDTLL(MatchField):
    """Match for IPv6 ND TLL."""

    name = 'nd_tll'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_ND_TLL

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        value_bytes = self.value.to_bytes(6, 'big')
        return OxmTLV(oxm_field=self.oxm_field, oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        tll = int.from_bytes(tlv.oxm_value, 'big')
        return cls(tll)


class MatchEXTHDR(MatchField):
    """Match for IPv6 EXTHDR."""

    name = 'v6_hdr'
    oxm_field = OxmOfbMatchField.OFPXMT_OFB_IPV6_EXTHDR

    def as_of_tlv(self):
        """Return a pyof OXM TLV instance."""
        try:
            value = int(self.value)
            mask = None
            oxm_hasmask = False
        except ValueError:
            value, mask = map(int, self.value.split('/'))
            oxm_hasmask = True
        value_bytes = value.to_bytes(2, 'big')
        if mask:
            value_bytes += mask.to_bytes(2, 'big')
        return OxmTLV(oxm_field=self.oxm_field,
                      oxm_hasmask=oxm_hasmask,
                      oxm_value=value_bytes)

    @classmethod
    def from_of_tlv(cls, tlv):
        """Return an instance from a pyof OXM TLV."""
        value = int.from_bytes(tlv.oxm_value[:2], 'big')
        if tlv.oxm_hasmask:
            exhead_mask = int.from_bytes(tlv.oxm_value[2:], 'big')
            value = f'{value}/{exhead_mask}'
        return cls(value)
