"""Module to help to create tests."""
from unittest.mock import MagicMock, Mock, create_autospec

from pyof.utils import unpack
from kytos.core import Controller
from kytos.core.config import KytosConfig
from kytos.core.connection import Connection, ConnectionState
from kytos.core.interface import Interface
from kytos.core.switch import Switch


def get_controller_mock():
    """Return a controller mock."""
    options = KytosConfig().options['daemon']
    controller = Controller(options)
    controller.log = Mock()
    return controller


def get_interface_mock(interface_name, port, *args, **kwargs):
    """Return a interface mock."""
    switch = get_switch_mock(0x04)
    switch.connection = Mock()
    iface = Interface(interface_name, port, switch, *args, **kwargs)
    return iface


def get_switch_mock(dpid):
    """Return a switch mock."""
    return Switch(dpid)


def get_connection_mock(of_version, target_switch,
                        connection_state=ConnectionState.NEW):
    connection = Connection(Mock(), Mock(), Mock())
    connection.switch = target_switch
    connection.protocol.unpack = unpack
    connection.protocol.version = of_version
    connection.state = connection_state
    return connection


def get_kytos_event_mock(**kwargs):
    destination = kwargs.get('destination')
    message = kwargs.get('message')
    source = kwargs.get('source')

    event = MagicMock()
    event.source = source
    event.content = {'destination': destination,
                     'message': message}
    return event
