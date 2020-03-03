"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyof.v0x01.controller2switch.common import StatsType 

from napps.kytos.of_core.main import Main
from tests.helpers import get_controller_mock, get_kytos_event_mock, get_switch_mock, get_connection_mock

class TestMain(TestCase):
    """docstring for TestMain."""

    def setUp(self):
        """Execute steps before each tests.

        Set the server_name_url from kytos/of_core
        """
        # self.server_name_url = 'http://localhost:8181/api/kytos/of_core'
        self.controller = get_controller_mock()
        self.switch_01 = get_switch_mock("00:00:00:00:00:00:00:01")
        self.switch_02 = get_switch_mock("00:00:00:00:00:00:00:02")
        self.switch_03 = get_switch_mock("00:00:00:00:00:00:00:03")
        self.switch_04 = get_switch_mock("00:00:00:00:00:00:00:04")
        self.switch_01.connection = get_connection_mock(0x01, self.switch_02)
        self.switch_02.connection = get_connection_mock(0x01, self.switch_01)
        self.switch_03.connection = get_connection_mock(0x04, self.switch_04)
        self.switch_04.connection = get_connection_mock(0x04, self.switch_03)
        self.napp = Main(self.controller)
        # self.patched_events = []

    @patch('napps.kytos.of_core.v0x04.utils.update_flow_list')
    @patch('napps.kytos.of_core.v0x01.utils.update_flow_list')
    def test_request_flow_list(self, *args):
        (mock_update_flow_list_v0x01, mock_update_flow_list_v0x04) = args
        mock_update_flow_list_v0x04.return_value = "ABC"

        self.napp._request_flow_list(self.switch_01)
        mock_update_flow_list_v0x01.assert_called_with(self.controller,
                                                       self.switch_01)
        self.napp._request_flow_list(self.switch_03)
        mock_update_flow_list_v0x04.assert_called_with(self.controller,
                                                       self.switch_03)

    @patch('napps.kytos.of_core.v0x01.flow.Flow.from_of_flow_stats')
    @patch('kytos.core.switch.Switch.update_description')
    def test_handle_stats_reply(self, *args):
        (mock_update_description, mock_from_of_flow_stats_v0x01) = args
        mock_from_of_flow_stats_v0x01.return_value = "ABC"

        flow_msg = MagicMock()
        flow_msg.body = "A"
        flow_msg.body_type = StatsType.OFPST_FLOW
        event = get_kytos_event_mock(source=self.switch_01.connection,
                                     message=flow_msg)
        self.napp.handle_stats_reply(event)
        mock_from_of_flow_stats_v0x01.assert_called_with(flow_msg.body,
                                                         self.switch_01.connection.switch)

        desc_msg = MagicMock()
        desc_msg.body = "A"
        desc_msg.body_type = StatsType.OFPST_DESC
        event = get_kytos_event_mock(source=self.switch_01.connection,
                                     message=desc_msg)
        self.napp.handle_stats_reply(event)
        mock_update_description.assert_called_with(desc_msg.body)
