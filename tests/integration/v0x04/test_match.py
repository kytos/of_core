"""Test Match abstraction for v0x04."""
import unittest

from napps.kytos.of_core.v0x04.flow import Match
from napps.kytos.of_core.v0x04.match_fields import MatchDLVLAN


class TestMatch(unittest.TestCase):
    """Tests for the Match class."""

    def test_dl_vlan_dict(self):
        """Convert from JSON dict to OF Match."""
        match_dict = {'dl_vlan': 42}
        match = Match.from_dict(match_dict)
        self.assertEqual(42, match.dl_vlan)

    def test_dl_vlan_pyof(self):
        """Convert to and from pyof OxmTLV."""
        expected = MatchDLVLAN(42)
        of_tlv = expected.as_of_tlv()
        actual = MatchDLVLAN.from_of_tlv(of_tlv)
        self.assertEqual(expected, actual)
