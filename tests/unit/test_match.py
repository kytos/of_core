"""Test Match abstraction for v0x01 and v0x04."""
from unittest import TestCase
from unittest.mock import MagicMock, patch, PropertyMock

from napps.kytos.of_core.v0x01.flow import Match as Match01
from napps.kytos.of_core.v0x04.flow import Match as Match04


class TestMatch(TestCase):
    """Tests for the Match class."""

    EXPECTED = {
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
        'tp_dst': 7,
    }

    def test_all_fields(self):
        """Test all match fields from and to dict."""
        for match_class in Match01, Match04:
            with self.subTest(match_class=match_class):
                match = match_class.from_dict(self.EXPECTED)
                actual = match.as_dict()
                self.assertDictEqual(self.EXPECTED, actual)

    @patch('napps.kytos.of_core.v0x04.flow.MatchFieldFactory')
    def test_from_of_match(self, mock_factory):
        """Test from_of_match."""
        mock_match = MagicMock()
        mock_field = MagicMock()
        mock_tlv = MagicMock()
        mock_field.name = 'A'
        mock_field.value = 42
        mock_factory.from_of_tlv.return_value = mock_field
        type(mock_match).oxm_match_fields = (PropertyMock(
                                             return_value=[[mock_tlv]]))
        response = Match04.from_of_match(mock_match)
        self.assertEqual(mock_factory.from_of_tlv.call_count, 1)
        self.assertIsInstance(response, Match04)
