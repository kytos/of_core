"""Tests for high-level Flow of OpenFlow 1.0 and 1.3."""
import unittest

from pyof.v0x01.controller2switch.flow_mod import FlowMod as OFFlow01
from pyof.v0x04.controller2switch.flow_mod import FlowMod as OFFlow04

from kytos.core.switch import Switch
from napps.kytos.of_core.v0x01.flow import Flow as Flow01
from napps.kytos.of_core.v0x04.flow import Flow as Flow04


class TestFlow(unittest.TestCase):
    """Test OF flow abstraction."""

    SWITCH = Switch('dpid')
    EXPECTED = {'id': '1ce5d08a46496fcb856cb603a5bfa00f',
                'switch': SWITCH.id,
                'table_id': 1,
                'match': {
                    'dl_src': '11:22:33:44:55:66'
                },
                'priority': 2,
                'idle_timeout': 3,
                'hard_timeout': 4,
                'cookie': 5,
                'actions': [
                    {'action_type': 'set_vlan',
                     'vlan_id': 6}],
                'stats': {}}

    def test_flow_mod(self):
        """Convert a dict to flow and vice-versa."""
        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow = flow_class.from_dict(self.EXPECTED, self.SWITCH)
                actual = flow.as_dict()
                self.assertDictEqual(self.EXPECTED, actual)

    def test_of_flow_mod(self):
        """Test convertion from Flow to OFFlow."""
        flow_mod_01 = Flow01.from_dict(self.EXPECTED, self.SWITCH)
        flow_mod_04 = Flow04.from_dict(self.EXPECTED, self.SWITCH)
        of_flow_mod_01 = flow_mod_01.as_of_add_flow_mod()
        of_flow_mod_04 = flow_mod_04.as_of_delete_flow_mod()
        self.assertIsInstance(of_flow_mod_01, OFFlow01)
        self.assertIsInstance(of_flow_mod_04, OFFlow04)
