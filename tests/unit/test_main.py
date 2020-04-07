"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, create_autospec, patch

from pyof.foundation.network_types import Ethernet
from pyof.v0x01.controller2switch.common import StatsType
from pyof.v0x04.controller2switch.common import MultipartType

from kytos.core.connection import ConnectionState
from tests.helpers import (get_connection_mock, get_controller_mock,
                           get_kytos_event_mock, get_switch_mock)


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
        # pylint: disable=bad-option-value
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

    @patch('napps.kytos.of_core.main.Main.update_port_status')
    @patch('napps.kytos.of_core.main.Main.update_links')
    def test_emit_message_in(self, *args):
        """Test emit_message_in."""
        (mock_update_links, mock_update_port_status) = args

        mock_port_connection = MagicMock()
        msg_port_mock = MagicMock()
        msg_port_mock.header.message_type.name = 'ofpt_port_status'
        mock_port_connection.side_effect = True
        self.napp.emit_message_in(mock_port_connection,
                                  msg_port_mock)
        mock_update_port_status.assert_called_with(msg_port_mock,
                                                   mock_port_connection)

        mock_packet_in_connection = MagicMock()
        msg_packet_in_mock = MagicMock()
        mock_packet_in_connection.side_effect = True
        msg_packet_in_mock.header.message_type.name = 'ofpt_packet_in'
        self.napp.emit_message_in(mock_packet_in_connection,
                                  msg_packet_in_mock)
        mock_update_links.assert_called_with(msg_packet_in_mock,
                                             mock_packet_in_connection)

    @patch('pyof.utils.v0x04.symmetric.echo_reply.EchoReply')
    @patch('napps.kytos.of_core.main.Main.emit_message_out')
    def test_handle_echo_request(self, *args):
        """Test handle echo request messages."""
        (mock_emit_message_out, mock_echo_reply) = args
        mock_event = MagicMock()
        mock_echo_request = MagicMock()
        mock_echo_reply.return_value = "A"
        mock_echo_request.header.xid = "A"
        mock_echo_request.data = "A"
        mock_event.source.protocol.version = 4
        mock_event.message = mock_echo_request
        self.napp.handle_echo_request(mock_event)
        mock_echo_reply.assert_called_with(xid=mock_echo_request.header.xid,
                                           data=mock_echo_request.data)
        mock_emit_message_out.assert_called_with(mock_event.source, "A")

    @patch('napps.kytos.of_core.main.Main.send_features_request')
    @patch('napps.kytos.of_core.v0x04.utils.say_hello')
    @patch('napps.kytos.of_core.main._get_version_from_bitmask')
    @patch('napps.kytos.of_core.main._get_version_from_header')
    def test_negotiate(self, *args):
        """Test negotiate."""
        (mock_version_header, mock_version_bitmask, mock_say_hello,
         mock_features_request) = args
        mock_version_header.return_value = 4
        mock_version_bitmask.return_value = 4
        mock_connection = MagicMock()
        mock_message = MagicMock()
        mock_message.versions = 4
        self.napp._negotiate(mock_connection, mock_message)
        mock_version_bitmask.assert_called_with(mock_message.versions)
        mock_say_hello.assert_called_with(self.napp.controller,
                                          mock_connection)
        mock_features_request.assert_called_with(mock_connection)

    @patch('pyof.utils.v0x04.asynchronous.error_msg.ErrorMsg')
    @patch('napps.kytos.of_core.main.Main.emit_message_out')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def tests_fail_negotiation(self, *args):
        """Test fail_negotiation."""
        (mock_event_buffer, mock_emit_message_out,
         mock_error_msg) = args
        mock_connection = MagicMock()
        mock_message = MagicMock()
        mock_connection.id = "A"
        mock_message.side_effect = 4
        self.napp.fail_negotiation(mock_connection, mock_message)
        mock_event_buffer.assert_called()
        mock_emit_message_out.assert_called_with(mock_connection,
                                                 mock_error_msg.return_value)

    @patch('napps.kytos.of_core.settings.SEND_FEATURES_REQUEST_ON_ECHO')
    @patch('napps.kytos.of_core.main.Main.send_features_request')
    def test_handle_queued_openflow_echo_reply(self, *args):
        """Test handle queued OpenFlow echo reply messages."""
        (mock_send_features_request, mock_settings) = args
        mock_settings.return_value = True
        mock_event = MagicMock()
        self.napp.handle_queued_openflow_echo_reply(mock_event)
        mock_send_features_request.assert_called_with(mock_event.destination)

    @patch('pyof.utils.v0x04.controller2switch.'
           'features_request.FeaturesRequest')
    @patch('napps.kytos.of_core.main.Main.emit_message_out')
    def test_send_features_request(self, *args):
        """Test send send_features_request."""
        (mock_emit_message_out, mock_features_request) = args
        mock_destination = MagicMock()
        mock_destination.protocol.version = 4
        mock_features_request.return_value = "A"
        self.napp.send_features_request(mock_destination)
        mock_features_request.assert_called()
        mock_emit_message_out.assert_called_with(mock_destination, "A")

    @patch('kytos.core.buffers.KytosEventBuffer.put')
    @patch('napps.kytos.of_core.main.Ethernet')
    def test_update_links(self, *args):
        """Test update_links."""
        (mock_ethernet, mock_buffer_put) = args
        ethernet = create_autospec(Ethernet)
        ethernet.ether_type = "A"
        mock_ethernet.side_effect = ethernet
        mock_message = MagicMock()
        mock_source = MagicMock()
        self.napp.update_links(mock_message, mock_source)
        mock_ethernet.assert_called()
        mock_buffer_put.assert_called()

    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_send_specific_port_mod(self, mock_buffer_put):
        """Test send specific port."""
        mock_port = MagicMock()
        mock_interface = MagicMock()
        current_state = 2
        self.napp._send_specific_port_mod(mock_port,
                                          mock_interface, current_state)
        mock_buffer_put.assert_called()

    @patch('kytos.core.buffers.KytosEventBuffer.put')
    @patch('napps.kytos.of_core.main.Interface')
    @patch('napps.kytos.of_core.main.Main._send_specific_port_mod')
    def test_update_port_status(self, *args):
        """Test update_port_status."""
        (mock_port_mod, mock_interface, mock_buffer_put) = args
        mock_port_status = MagicMock()
        mock_source = MagicMock()
        mock_port_status.reason.value.side_effect = [0, 1]
        mock_port_status.reason.enum_ref(0).name = 'OFPPR_ADD'
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_interface.assert_called()

        # check OFPRR_MODIFY
        mock_port_status.reason.enum_ref(1).name = 'OFPPR_MODIFY'
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_port_mod.assert_called()
        mock_buffer_put.assert_called()
