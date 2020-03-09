"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyof.v0x04.controller2switch.common import MultipartType
from pyof.v0x01.controller2switch.common import StatsType
from kytos.core.connection import ConnectionState

from tests.helpers import (get_controller_mock, get_kytos_event_mock,
                           get_switch_mock, get_connection_mock)


# pylint: disable=protected-access
class TestMain(TestCase):
    """docstring for TestMain."""

    def setUp(self):
        """Execute steps before each tests.

        Set the server_name_url from kytos/of_core
        """
        self.switch_v0x01 = get_switch_mock("00:00:00:00:00:00:00:01")
        self.switch_v0x04 = get_switch_mock("00:00:00:00:00:00:00:02")
        self.switch_v0x01.connection = get_connection_mock(
            0x01, get_switch_mock("00:00:00:00:00:00:00:03"))
        self.switch_v0x04.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:04"))

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        from napps.kytos.of_core.main import Main
        self.addCleanup(patch.stopall)

        self.napp = Main(get_controller_mock())

    @patch('napps.kytos.of_core.v0x04.utils.update_flow_list')
    @patch('napps.kytos.of_core.v0x01.utils.update_flow_list')
    def test_request_flow_list(self, *args):
        """Test request flow list."""
        (mock_update_flow_list_v0x01, mock_update_flow_list_v0x04) = args
        mock_update_flow_list_v0x04.return_value = "ABC"

        self.napp._request_flow_list(self.switch_v0x01)
        mock_update_flow_list_v0x01.assert_called_with(self.napp.controller,
                                                       self.switch_v0x01)
        self.napp._request_flow_list(self.switch_v0x04)
        mock_update_flow_list_v0x04.assert_called_with(self.napp.controller,
                                                       self.switch_v0x04)

    @patch('napps.kytos.of_core.v0x01.flow.Flow.from_of_flow_stats')
    @patch('kytos.core.switch.Switch.update_description')
    def test_handle_stats_reply(self, *args):
        """Test handle stats reply."""
        (mock_update_description, mock_from_of_flow_stats_v0x01) = args
        mock_from_of_flow_stats_v0x01.return_value = "ABC"

        flow_msg = MagicMock()
        flow_msg.body = "A"
        flow_msg.body_type = StatsType.OFPST_FLOW
        event = get_kytos_event_mock(source=self.switch_v0x01.connection,
                                     message=flow_msg)
        self.napp.handle_stats_reply(event)
        mock_from_of_flow_stats_v0x01.assert_called_with(
            flow_msg.body, self.switch_v0x01.connection.switch)

        desc_msg = MagicMock()
        desc_msg.body = "A"
        desc_msg.body_type = StatsType.OFPST_DESC
        event = get_kytos_event_mock(source=self.switch_v0x01.connection,
                                     message=desc_msg)
        self.napp.handle_stats_reply(event)
        mock_update_description.assert_called_with(desc_msg.body)

    @patch('kytos.core.switch.Switch.update_description')
    @patch('napps.kytos.of_core.main.Main._handle_multipart_flow_stats')
    @patch('napps.kytos.of_core.v0x04.utils.handle_port_desc')
    def test_handle_multipart_reply(self, *args):
        """Test handle multipart reply."""
        (mock_of_core_v0x04_utils, mock_from_of_flow_stats_v0x04,
         mock_update_description) = args

        flow_msg = MagicMock()
        flow_msg.multipart_type = MultipartType.OFPMP_FLOW
        event = get_kytos_event_mock(source=self.switch_v0x01.connection,
                                     message=flow_msg)

        self.napp.handle_multipart_reply(event)
        mock_from_of_flow_stats_v0x04.assert_called_with(
            flow_msg, self.switch_v0x01.connection.switch)

        ofpmp_port_desc = MagicMock()
        ofpmp_port_desc.body = "A"
        ofpmp_port_desc.multipart_type = MultipartType.OFPMP_PORT_DESC
        event = get_kytos_event_mock(source=self.switch_v0x01.connection,
                                     message=ofpmp_port_desc)
        self.napp.handle_multipart_reply(event)
        mock_of_core_v0x04_utils.assert_called_with(
            self.napp.controller, self.switch_v0x01.connection.switch,
            ofpmp_port_desc.body)

        ofpmp_desc = MagicMock()
        ofpmp_desc.body = "A"
        ofpmp_desc.multipart_type = MultipartType.OFPMP_DESC
        event = get_kytos_event_mock(source=self.switch_v0x01.connection,
                                     message=ofpmp_desc)
        self.napp.handle_multipart_reply(event)
        mock_update_description.assert_called_with(ofpmp_desc.body)

    @patch('kytos.core.buffers.KytosEventBuffer.put')
    @patch('napps.kytos.of_core.v0x04.utils.send_set_config')
    @patch('napps.kytos.of_core.v0x01.utils.send_set_config')
    @patch('napps.kytos.of_core.v0x04.utils.send_desc_request')
    @patch('napps.kytos.of_core.v0x01.utils.send_desc_request')
    @patch('kytos.core.connection.Connection.set_established_state')
    @patch('kytos.core.connection.Connection.is_during_setup')
    @patch('napps.kytos.of_core.v0x04.utils.handle_features_reply')
    @patch('napps.kytos.of_core.v0x01.utils.handle_features_reply')
    def test_handle_features_reply(self, *args):
        """Test handle features reply."""
        (mock_freply_v0x01, mock_freply_v0x04, mock_is_during_setup,
         mock_set_established_state, mock_send_desc_request_v0x01,
         mock_send_desc_request_v0x04, mock_send_set_config_v0x01,
         mock_send_set_config_v0x04, mock_buffers_put) = args
        mock_freply_v0x01.return_value = self.switch_v0x01.connection.switch
        mock_freply_v0x04.return_value = self.switch_v0x04.connection.switch
        mock_is_during_setup.return_value = True

        self.switch_v0x01.connection.state = ConnectionState.SETUP
        self.switch_v0x01.connection.protocol.state = 'waiting_features_reply'
        event = get_kytos_event_mock(source=self.switch_v0x01.connection)
        self.napp.handle_features_reply(event)
        mock_freply_v0x01.assert_called_with(self.napp.controller, event)
        mock_send_desc_request_v0x01.assert_called_with(
            self.napp.controller, self.switch_v0x01.connection.switch)
        mock_send_set_config_v0x01.assert_called_with(
            self.napp.controller, self.switch_v0x01.connection.switch)

        self.switch_v0x04.connection.state = ConnectionState.SETUP
        self.switch_v0x04.connection.protocol.state = 'waiting_features_reply'
        event = get_kytos_event_mock(source=self.switch_v0x04.connection)
        self.napp.handle_features_reply(event)
        mock_freply_v0x04.assert_called_with(self.napp.controller, event)
        mock_send_desc_request_v0x04.assert_called_with(
            self.napp.controller, self.switch_v0x04.connection.switch)
        mock_send_set_config_v0x04.assert_called_with(
            self.napp.controller, self.switch_v0x04.connection.switch)

        mock_is_during_setup.assert_called()
        mock_set_established_state.assert_called()
        mock_buffers_put.assert_called()

    @patch('napps.kytos.of_core.main.Main._update_switch_flows')
    @patch('napps.kytos.of_core.v0x04.flow.Flow.from_of_flow_stats')
    @patch('napps.kytos.of_core.main.Main._is_multipart_reply_ours')
    def test_handle_multipart_flow_stats(self, *args):
        """Test handle multipart flow stats."""
        (mock_is_multipart_reply_ours, mock_from_of_flow_stats_v0x01,
         mock_update_switch_flows) = args
        mock_is_multipart_reply_ours.return_value = True
        mock_from_of_flow_stats_v0x01.return_value = "ABC"

        flow_msg = MagicMock()
        flow_msg.body = "A"
        flow_msg.flags.value = 2
        flow_msg.body_type = StatsType.OFPST_FLOW

        self.napp._handle_multipart_flow_stats(flow_msg, self.switch_v0x04)

        mock_is_multipart_reply_ours.assert_called_with(flow_msg,
                                                        self.switch_v0x04)
        mock_from_of_flow_stats_v0x01.assert_called_with(flow_msg.body,
                                                         self.switch_v0x04)
        mock_update_switch_flows.assert_called_with(self.switch_v0x04)
