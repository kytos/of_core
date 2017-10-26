"""Test Match abstraction for v0x01 and v0x04."""
import unittest

from napps.kytos.of_core.v0x01.flow import Match as Match01
from napps.kytos.of_core.v0x04.flow import Match as Match04


class TestMatch(unittest.TestCase):
    """Tests for the Match class."""

    def test_all_fields(self):
        """Test all match fields from and to dict."""
        expected = {
            'in_port': 1,
            'dl_src': '11:22:33:44:55:66',
            'dl_dst': 'aa:bb:cc:dd:ee:ff',
            'dl_vlan': 2,
            'dl_vlan_pcp': 3,
            'dl_type': 4,
            'nw_proto': 5,
            'nw_src': '1.2.3.4/32',
            'nw_dst': '5.6.7.0/24',
            'tp_src': 6,
            'tp_dst': 7}
        for match_class in Match01, Match04:
            with self.subTest(match_class=match_class):
                match = match_class.from_dict(expected)
                actual = match.as_dict()
                self.assertDictEqual(expected, actual)
