"""Test v0x01.utils methods."""
from unittest import TestCase, mock
from unittest.mock import MagicMock, PropertyMock, patch

from kytos.lib.helpers import get_connection_mock, get_switch_mock
from napps.kytos.of_core.v0x01.utils import (handle_features_reply, say_hello,
                                             send_desc_request, send_echo,
                                             send_set_config)
from tests.helpers import get_controller_mock


class TestUtils(TestCase):
    """Test utils."""

    def setUp(self):
        """Execute steps before each tests."""
        self.mock_controller = get_controller_mock()
        self.mock_switch = get_switch_mock('00:00:00:00:00:00:00:01', 0x01)
        self.mock_connection = get_connection_mock(0x01, self.mock_switch)

    @patch('napps.kytos.of_core.v0x01.utils.emit_message_out')
    def test_send_desc_request(self, mock_emit_message_out):
        """Test send_desc_request."""
        send_desc_request(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    def test_handle_features_reply(self):
        """test Handle features reply."""
        mock_event = MagicMock()
        mock_features = MagicMock()
        mock_controller = MagicMock()
        self.mock_switch.get_interface_by_port_no.side_effect = [MagicMock(),
                                                                 False]
        type(mock_features).ports = PropertyMock(return_value=[MagicMock()])
        type(mock_event).content = PropertyMock(return_value={'message':
                                                mock_features})
        mock_controller.get_switch_or_create.return_value = self.mock_switch
        response = handle_features_reply(mock_controller, mock_event)
        self.assertEqual(self.mock_switch, response)
        self.assertEqual(self.mock_switch.update_features.call_count, 1)

        self.mock_switch.update_features.call_count = 0
        response = handle_features_reply(mock_controller, mock_event)
        self.assertEqual(self.mock_switch, response)
        self.assertEqual(self.mock_switch.update_features.call_count, 1)

    @patch('napps.kytos.of_core.v0x01.utils.emit_message_out')
    def test_send_echo(self, mock_emit_message_out):
        """Test send_echo."""
        send_echo(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    @patch('napps.kytos.of_core.v0x01.utils.emit_message_out')
    def test_set_config(self, mock_emit_message_out):
        """Test set_config."""
        send_set_config(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    @patch('napps.kytos.of_core.v0x01.utils.emit_message_out')
    def test_say_hello(self, mock_emit_message_out):
        """Test say_hello."""
        say_hello(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()


class TestJSONEncoderOF10(TestCase):
    """Test custom JSON encoder for OF 1.0 ."""

    def setUp(self):
        """Execute steps before each tests.
        Set the server_name_url from kytos/of_core
        """
        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.kytos.of_core.v0x01.utils import JSONEncoderOF10
        self.addCleanup(patch.stopall)

        self.encoder = JSONEncoderOF10()

    # This method tests the conversion of the ``UBIntBase`` class to int.
    # This patch and mock avoids the need to import the class ``UBIntBase``
    # into the test file to create an object of type ``UBIntBase``.
    # Without the patch, ``object_mock`` does not enter the ``isinstance``
    # condition which is being tested here.
    @patch('napps.kytos.of_core.v0x01.utils.UBIntBase', new=mock.Mock)
    def test_cast(self):
        """Test custom JSON encoder for OF 1.0 flow representation."""
        object_mock = MagicMock()
        response = self.encoder.default(object_mock)
        self.assertEqual(response, 1)

    @patch('json.JSONEncoder.default')
    def test_cast_not_equal_case(self, mock_json):
        """Test the custom JSON encoder in case the object is not UBInt."""
        self.encoder.default('1')
        mock_json.assert_called()
