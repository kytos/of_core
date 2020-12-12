"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch

from pyof.foundation.network_types import Ethernet
from pyof.v0x01.controller2switch.common import StatsType
from pyof.v0x04.controller2switch.common import MultipartType

from kytos.core.connection import ConnectionState
from kytos.lib.helpers import (get_connection_mock, get_kytos_event_mock,
                               get_switch_mock)
from napps.kytos.of_core.utils import NegotiationException
from tests.helpers import get_controller_mock


# pylint: disable=protected-access, too-many-public-methods
class TestMain(TestCase):
    """Test the Main class."""

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
        from napps.kytos.of_core.main import Main
        self.addCleanup(patch.stopall)
        self.napp = Main(get_controller_mock())

    @patch('napps.kytos.of_core.v0x01.utils.send_echo')
    @patch('napps.kytos.of_core.v0x04.utils.send_echo')
    def test_execute(self, *args):
        """Test execute."""
        (mock_of_core_v0x04_utils, mock_of_core_v0x01_utils) = args
        self.switch_v0x01.is_connected.return_value = True
        self.switch_v0x04.is_connected.return_value = True
        self.napp.controller.switches = {"00:00:00:00:00:00:00:01":
                                         self.switch_v0x01}
        self.napp.execute()
        mock_of_core_v0x01_utils.assert_called()

        self.napp.controller.switches = {"00:00:00:00:00:00:00:01":
                                         self.switch_v0x04}
        self.napp.execute()
        mock_of_core_v0x04_utils.assert_called()

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
    def test_handle_stats_reply(self, mock_from_of_flow_stats_v0x01):
        """Test handle stats reply."""
        mock_from_of_flow_stats_v0x01.return_value = "ABC"

        flow_msg = MagicMock()
        flow_msg.body = "A"
        flow_msg.body_type = StatsType.OFPST_FLOW

        name = 'kytos/of_core.v0x01.messages.in.ofpt_stats_reply'
        content = {"source": self.switch_v0x01.connection,
                   "message": flow_msg}
        event = get_kytos_event_mock(name=name, content=content)
        self.napp.handle_stats_reply(event)
        mock_from_of_flow_stats_v0x01.assert_called_with(
            flow_msg.body, self.switch_v0x01.connection.switch)

        desc_msg = MagicMock()
        desc_msg.body = "A"
        desc_msg.body_type = StatsType.OFPST_DESC
        content = {"source": self.switch_v0x01.connection,
                   "message": desc_msg}
        event = get_kytos_event_mock(name=name, content=content)
        switch_update = self.switch_v0x01.connection.switch.update_description
        self.napp.handle_stats_reply(event)
        self.assertEqual(switch_update.call_count, 1)

    @patch('napps.kytos.of_core.main.Main._handle_multipart_flow_stats')
    @patch('napps.kytos.of_core.v0x04.utils.handle_port_desc')
    def test_handle_multipart_reply(self, *args):
        """Test handle multipart reply."""
        (mock_of_core_v0x04_utils, mock_from_of_flow_stats_v0x04) = args

        flow_msg = MagicMock()
        flow_msg.multipart_type = MultipartType.OFPMP_FLOW
        name = 'kytos/of_core.v0x04.messages.in.ofpt_multipart_reply'
        content = {"source": self.switch_v0x04.connection,
                   "message": flow_msg}
        event = get_kytos_event_mock(name=name, content=content)

        self.napp.handle_multipart_reply(event)
        mock_from_of_flow_stats_v0x04.assert_called_with(
            flow_msg, self.switch_v0x04.connection.switch)

        ofpmp_port_desc = MagicMock()
        ofpmp_port_desc.body = "A"
        ofpmp_port_desc.multipart_type = MultipartType.OFPMP_PORT_DESC
        content = {"source": self.switch_v0x04.connection,
                   "message": ofpmp_port_desc}
        event = get_kytos_event_mock(name=name, content=content)
        self.napp.handle_multipart_reply(event)
        mock_of_core_v0x04_utils.assert_called_with(
            self.napp.controller, self.switch_v0x04.connection.switch,
            ofpmp_port_desc.body)

        ofpmp_desc = MagicMock()
        ofpmp_desc.body = "A"
        ofpmp_desc.multipart_type = MultipartType.OFPMP_DESC
        content = {"source": self.switch_v0x04.connection,
                   "message": ofpmp_desc}
        event = get_kytos_event_mock(name=name, content=content)
        switch_update = self.switch_v0x04.connection.switch.update_description
        self.napp.handle_multipart_reply(event)
        self.assertEqual(switch_update.call_count, 1)

    @patch('kytos.core.buffers.KytosEventBuffer.put')
    @patch('napps.kytos.of_core.v0x04.utils.send_set_config')
    @patch('napps.kytos.of_core.v0x01.utils.send_set_config')
    @patch('napps.kytos.of_core.v0x04.utils.send_desc_request')
    @patch('napps.kytos.of_core.v0x01.utils.send_desc_request')
    @patch('napps.kytos.of_core.v0x04.utils.handle_features_reply')
    @patch('napps.kytos.of_core.v0x01.utils.handle_features_reply')
    def test_handle_features_reply(self, *args):
        """Test handle features reply."""
        (mock_freply_v0x01, mock_freply_v0x04, mock_send_desc_request_v0x01,
         mock_send_desc_request_v0x04, mock_send_set_config_v0x01,
         mock_send_set_config_v0x04, mock_buffers_put) = args
        mock_freply_v0x01.return_value = self.switch_v0x01.connection.switch
        mock_freply_v0x04.return_value = self.switch_v0x04.connection.switch

        self.switch_v0x01.connection.state = ConnectionState.SETUP
        self.switch_v0x01.connection.protocol.state = 'waiting_features_reply'
        name = 'kytos/of_core.v0x0[14].messages.in.ofpt_features_reply'
        content = {"source": self.switch_v0x01.connection}
        event = get_kytos_event_mock(name=name, content=content)
        self.napp.handle_features_reply(event)
        mock_freply_v0x01.assert_called_with(self.napp.controller, event)
        mock_send_desc_request_v0x01.assert_called_with(
            self.napp.controller, self.switch_v0x01.connection.switch)
        mock_send_set_config_v0x01.assert_called_with(
            self.napp.controller, self.switch_v0x01.connection.switch)

        self.switch_v0x04.connection.state = ConnectionState.SETUP
        self.switch_v0x04.connection.protocol.state = 'waiting_features_reply'
        content = {"source": self.switch_v0x04.connection}
        event = get_kytos_event_mock(name=name, content=content)
        self.napp.handle_features_reply(event)
        mock_freply_v0x04.assert_called_with(self.napp.controller, event)
        mock_send_desc_request_v0x04.assert_called_with(
            self.napp.controller, self.switch_v0x04.connection.switch)
        mock_send_set_config_v0x04.assert_called_with(
            self.napp.controller, self.switch_v0x04.connection.switch)

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

    def test_update_switch_flows(self):
        """Test update_switch_flows."""
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_switch.id = dpid
        self.napp._multipart_replies_flows = {dpid: mock_switch}
        self.napp._multipart_replies_xids = {dpid: mock_switch}
        self.napp._update_switch_flows(mock_switch)
        self.assertEqual(self.napp._multipart_replies_xids, {})
        self.assertEqual(self.napp._multipart_replies_flows, {})

    def test_is_multipart_reply_ours(self):
        """Test _is_multipart_reply_ours."""
        dpid_a = '00:00:00:00:00:00:00:01'
        dpid_b = '00:00:00:00:00:00:00:02'
        mock_switch = get_switch_mock(dpid_a)
        mock_reply = MagicMock()
        mock_reply.header.xid = mock_switch
        type(mock_switch).id = PropertyMock(side_effect=[dpid_a,
                                                         dpid_a, dpid_b])
        self.napp._multipart_replies_xids = {dpid_a: mock_switch}
        response = self.napp._is_multipart_reply_ours(mock_reply, mock_switch)
        self.assertEqual(response, True)

        response = self.napp._is_multipart_reply_ours(mock_reply, mock_switch)
        self.assertEqual(response, False)

    @patch('napps.kytos.of_core.main.of_slicer')
    @patch('napps.kytos.of_core.main.Main._negotiate')
    @patch('napps.kytos.of_core.main.Main.emit_message_in')
    def test_handle_raw_in(self, *args):
        """Test handle_raw_in."""
        (mock_emit_message_in, mock_negotiate, mock_of_slicer) = args

        mock_packets = MagicMock()
        mock_data = MagicMock()
        mock_connection = MagicMock()
        mock_connection.is_new.side_effect = [True, False, True, False]
        mock_connection.is_during_setup.return_value = False
        mock_of_slicer.return_value = [[mock_packets, mock_packets], b'']
        name = 'kytos/core.openflow.raw.in'
        content = {'source': mock_connection, 'new_data': mock_data}
        mock_event = get_kytos_event_mock(name=name, content=content)

        self.napp.handle_raw_in(mock_event)
        mock_negotiate.assert_called()
        mock_emit_message_in.assert_called()

        # Test Fail
        mock_negotiate.side_effect = NegotiationException('Foo')
        self.napp.handle_raw_in(mock_event)
        self.assertEqual(mock_connection.close.call_count, 1)

        mock_connection.close.call_count = 0
        mock_connection.protocol.unpack.side_effect = AttributeError()
        self.napp.handle_raw_in(mock_event)
        self.assertEqual(mock_connection.close.call_count, 1)

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

    @patch('napps.kytos.of_core.main.emit_message_out')
    def test_emit_message_out(self, mock_emit_message_out):
        """Test emit message_out."""
        mock_connection = MagicMock()
        mock_message = MagicMock()
        mock_connection.is_alive.return_value = True
        self.napp.emit_message_out(mock_connection, mock_message)
        mock_emit_message_out.assert_called()

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
        mock_version_bitmask.side_effect = [4, None]
        mock_connection = MagicMock()
        mock_message = MagicMock()
        type(mock_message).versions = PropertyMock(side_effect=[4, 4, 4,
                                                                False])

        self.napp._negotiate(mock_connection, mock_message)
        mock_version_bitmask.assert_called_with(mock_message.versions)
        mock_say_hello.assert_called_with(self.napp.controller,
                                          mock_connection)
        mock_features_request.assert_called_with(mock_connection)

        self.napp._negotiate(mock_connection, mock_message)
        mock_say_hello.assert_called_with(self.napp.controller,
                                          mock_connection)
        mock_features_request.assert_called_with(mock_connection)

        # Test Fail
        with self.assertRaises(NegotiationException):
            type(mock_message).versions = PropertyMock(return_value=[4])
            self.napp._negotiate(mock_connection, mock_message)

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

    def test_handle_features_request_sent(self):
        """Test tests_handle_features_request_sent."""
        mock_protocol = MagicMock()
        mock_protocol.protocol.state = 'sending_features'
        expected = 'waiting_features_reply'
        name = 'kytos/of_core.v0x0[14].messages.out.ofpt_features_request'
        content = {'destination': mock_protocol}
        mock_event = get_kytos_event_mock(name=name, content=content)
        self.napp.handle_features_request_sent(mock_event)
        self.assertEqual(mock_event.destination.protocol.state, expected)

    def test_handle_openflow_in_hello_failed(self):
        """Test handle_openflow_in_hello_failed."""
        mock_destination = MagicMock()
        content = {'destination': mock_destination}
        mock_event = get_kytos_event_mock(name='kytos/of_core',
                                          content=content)
        self.napp.handle_openflow_in_hello_failed(mock_event)
        self.assertEqual(mock_event.destination.close.call_count, 1)

    @patch('napps.kytos.of_core.main.log')
    def test_shutdown(self, mock_log):
        """Test shutdown."""
        self.napp.shutdown()
        self.assertEqual(mock_log.debug.call_count, 1)

    @patch('kytos.core.buffers.KytosEventBuffer.put')
    @patch('napps.kytos.of_core.main.Ethernet')
    def test_update_links(self, *args):
        """Test update_links."""
        (mock_ethernet, mock_buffer_put) = args
        ethernet = create_autospec(Ethernet)
        ethernet.ether_type = "A"
        mock_ethernet.side_effect = ethernet
        mock_message = MagicMock()
        mock_s = MagicMock()
        mock_s.switch.get_interface_by_port_no.side_effect = [AttributeError(),
                                                              True]
        self.napp.update_links(mock_message, mock_s)
        mock_ethernet.assert_called()
        mock_buffer_put.assert_called()

    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_send_specific_port_mod(self, mock_buffer_put):
        """Test send specific port."""
        mock_port = MagicMock()
        mock_interface = MagicMock()
        type(mock_port.state).value = PropertyMock(side_effect=[0, 1, 2])
        current_state = 0
        self.napp._send_specific_port_mod(mock_port,
                                          mock_interface, current_state)
        mock_buffer_put.assert_called()

        current_state = 1
        self.napp._send_specific_port_mod(mock_port,
                                          mock_interface, current_state)
        mock_buffer_put.assert_called()

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

        mock_port_status.reason.value.side_effect = [0, 1, 2]
        mock_port_status.reason.enum_ref(0).name = 'OFPPR_ADD'
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_interface.assert_called()

        # check OFPRR_MODIFY
        mock_port_status.reason.enum_ref(1).name = 'OFPPR_MODIFY'
        mock_source.switch.get_interface_by_port_no.return_value = False
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_port_mod.assert_called()
        mock_buffer_put.assert_called()

        mock_source.switch.get_interface_by_port_no.return_value = MagicMock()
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_port_mod.assert_called()
        mock_buffer_put.assert_called()

        # check OFPRR_DELETE
        mock_port_status.reason.enum_ref(2).name = 'OFPPR_DELETE'
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_port_mod.assert_called()
        mock_buffer_put.assert_called()
