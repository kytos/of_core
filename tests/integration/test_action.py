"""Test Action abstraction for v0x01 and v0x04."""
import unittest

from napps.kytos.of_core.v0x01.flow import Action as Action01
from napps.kytos.of_core.v0x04.flow import Action as Action04


class TestAction(unittest.TestCase):
    """Tests for the Action class."""

    def test_all_actions(self):
        """Test all action fields from and to dict."""
        action_dicts = [
            {
                'action_type': 'output',
                'port': 1},
            {
                'action_type': 'set_vlan',
                'vlan_id': 2},
        ]
        for action_class in Action01, Action04:
            with self.subTest(action_class=action_class):
                for expected in action_dicts:
                    with self.subTest(expected=expected):
                        action = action_class.from_dict(expected)
                        actual = action.as_dict()
                        self.assertDictEqual(expected, actual)
