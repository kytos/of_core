"""Tests for high-level Flow of OpenFlow 1.0 and 1.3."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kytos.lib.helpers import get_connection_mock, get_switch_mock
from napps.kytos.of_core.v0x01.flow import Flow as Flow01
from napps.kytos.of_core.v0x04.flow import Flow as Flow04


class TestFlowFactory(TestCase):
    """Test the FlowFactory class."""

    def setUp(self):
        """Execute steps before each tests.
        Set the server_name_url from kytos/of_core
        """
        self.switch_v0x01 = get_switch_mock("00:00:00:00:00:00:00:01", 0x01)
        self.switch_v0x04 = get_switch_mock("00:00:00:00:00:00:00:02", 0x04)
        self.switch_v0x01.connection = get_connection_mock(
            0x01, get_switch_mock("00:00:00:00:00:00:00:03"))
        self.switch_v0x04.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:04"))

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.kytos.of_core.flow import FlowFactory
        self.addCleanup(patch.stopall)

        self.napp = FlowFactory()

    @patch('napps.kytos.of_core.flow.v0x01')
    @patch('napps.kytos.of_core.flow.v0x04')
    def test_from_of_flow_stats(self, *args):
        """Test from_of_flow_stats."""
        (mock_flow_v0x04, mock_flow_v0x01) = args
        mock_stats = MagicMock()

        self.napp.from_of_flow_stats(mock_stats, self.switch_v0x01)
        mock_flow_v0x01.flow.Flow.from_of_flow_stats.assert_called()

        self.napp.from_of_flow_stats(mock_stats, self.switch_v0x04)
        mock_flow_v0x04.flow.Flow.from_of_flow_stats.assert_called()


class TestFlow(TestCase):
    """Test OF flow abstraction."""

    mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")
    mock_switch.id = "00:00:00:00:00:00:00:01"
    expected = {'switch': mock_switch.id,
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

    @patch('napps.kytos.of_core.flow.v0x01')
    @patch('napps.kytos.of_core.flow.v0x04')
    @patch('napps.kytos.of_core.flow.json.dumps')
    def test_flow_mod(self, *args):
        """Convert a dict to flow and vice-versa."""
        (mock_json, _, _) = args
        dpid = "00:00:00:00:00:00:00:01"
        mock_json.return_value = str(self.expected)
        for flow_class, version in [(Flow04, 0x01), (Flow04, 0x04)]:
            with self.subTest(flow_class=flow_class):
                mock_switch = get_switch_mock(dpid, version)
                mock_switch.id = dpid
                flow = flow_class.from_dict(self.expected, mock_switch)
                actual = flow.as_dict()
                del actual['id']
                self.assertDictEqual(self.expected, actual)

    @patch('napps.kytos.of_core.flow.FlowBase._as_of_flow_mod')
    def test_of_flow_mod(self, mock_flow_mod):
        """Test convertion from Flow to OFFlow."""

        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow = flow_class.from_dict(self.expected, self.mock_switch)
                flow.as_of_add_flow_mod()
                mock_flow_mod.assert_called()

                flow.as_of_delete_flow_mod()
                mock_flow_mod.assert_called()

    # pylint: disable = protected-access
    def test_as_of_flow_mod(self):
        """Test _as_of_flow_mod."""
        mock_command = MagicMock()
        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow_mod = flow_class.from_dict(self.expected,
                                                self.mock_switch)
                response = flow_mod._as_of_flow_mod(mock_command)
                self.assertEqual(response.cookie, self.expected['cookie'])
                self.assertEqual(response.idle_timeout,
                                 self.expected['idle_timeout'])
                self.assertEqual(response.hard_timeout,
                                 self.expected['hard_timeout'])


class TestFlowBase(TestCase):
    """Test FlowBase Class."""

    def test__eq__success_with_equal_flows(self):
        """Test success case to __eq__ override with equal flows."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        flow_dict = {'switch': mock_switch.id,
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
                     'stats': {}
                     }

        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow_1 = flow_class.from_dict(flow_dict, mock_switch)
                flow_2 = flow_class.from_dict(flow_dict, mock_switch)
                self.assertEqual(flow_1 == flow_2, True)

    def test__eq__success_with_different_flows(self):
        """Test success case to __eq__ override with different flows."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        flow_dict_1 = {'switch': mock_switch.id,
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
                       'stats': {}
                       }

        flow_dict_2 = {'switch': mock_switch.id,
                       'table_id': 1,
                       'match': {
                           'dl_src': '11:22:33:44:55:66'
                       },
                       'priority': 1000,
                       'idle_timeout': 3,
                       'hard_timeout': 4,
                       'cookie': 5,
                       'actions': [
                           {'action_type': 'set_vlan',
                            'vlan_id': 6}],
                       'stats': {}
                       }

        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow_1 = flow_class.from_dict(flow_dict_1, mock_switch)
                flow_2 = flow_class.from_dict(flow_dict_2, mock_switch)
                self.assertEqual(flow_1 == flow_2, False)

    def test__eq__fail(self):
        """Test the case where __eq__ receives objects with different types."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        flow_dict = {'switch': mock_switch.id,
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
                     'stats': {}
                     }

        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow_1 = flow_class.from_dict(flow_dict, mock_switch)
                flow_2 = "any_string_object"
                with self.assertRaises(ValueError):
                    return flow_1 == flow_2
