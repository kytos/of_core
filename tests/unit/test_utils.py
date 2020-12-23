"""Test utils methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kytos.lib.helpers import get_connection_mock, get_switch_mock
from napps.kytos.of_core.utils import (GenericHello, _emit_message,
                                       _unpack_int, emit_message_in,
                                       emit_message_out, of_slicer)
from tests.helpers import get_controller_mock


class TestUtils(TestCase):
    """Test utils."""

    def setUp(self):
        """Execute steps before each tests."""
        self.mock_controller = get_controller_mock()
        self.mock_switch = get_switch_mock('00:00:00:00:00:00:00:01', 0x04)
        self.mock_connection = get_connection_mock(0x04, self.mock_switch)

    def test_of_slicer(self):
        """Test of_slicer."""
        data = b'\x04\x00\x00\x10\x00\x00\x00\x3e'
        data += b'\x00\x01\x00\x08\x00\x00\x00\x10'
        response = of_slicer(data)
        self.assertEqual(data, response[0][0])
        self.assertCountEqual(response[1], [])

    def test_unpack_int(self):
        """Test test_unpack_int."""
        mock_packet = MagicMock()
        response = _unpack_int(mock_packet)
        self.assertEqual(int.from_bytes(mock_packet,
                                        byteorder='big'), response)

    @patch('napps.kytos.of_core.utils.KytosEvent')
    def test_emit_message(self, mock_event):
        """Test emit_message."""
        mock_message = MagicMock()
        _emit_message(self.mock_controller, self.mock_connection, mock_message,
                      'in')
        mock_event.assert_called()

        _emit_message(self.mock_controller, self.mock_connection, mock_message,
                      'out')
        mock_event.assert_called()

    @patch('napps.kytos.of_core.utils._emit_message')
    def test_emit_message_in_out(self, mock_message_in):
        """Test emit_message in and out."""

        emit_message_in(self.mock_controller, self.mock_connection, 'in')
        mock_message_in.assert_called()

        emit_message_out(self.mock_controller, self.mock_connection, 'in')
        mock_message_in.assert_called()


class TestGenericHello(TestCase):
    """Test GenericHello."""

    data = b'\x04\x00\x00\x10\x00\x00\x00\x00\x00\x01\x00\x08\x00\x00\x00\x10'

    @patch('napps.kytos.of_core.utils.OFPTYPE')
    def test_pack(self, mock_ofptype):
        """Test pack."""
        mock_ofptype.return_value = True
        generic = GenericHello(packet=self.data, versions=b'\x04')
        response = generic.pack()
        self.assertEqual(self.data, response)
