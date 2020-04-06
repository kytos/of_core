"""Module to help to create tests."""
import os
from functools import wraps
from unittest.mock import MagicMock, Mock

from kytos.core import Controller
from kytos.core.config import KytosConfig
from kytos.core.connection import Connection
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


def get_connection_mock(of_version, target_switch):
    """Return a connection mock."""
    connection = Connection(Mock(), Mock(), Mock())
    connection.switch = target_switch
    connection.protocol.version = of_version
    return connection


def get_kytos_event_mock(**kwargs):
    """Return a kytos event mock."""
    destination = kwargs.get('destination')
    message = kwargs.get('message')
    source = kwargs.get('source')

    event = MagicMock()
    event.source = source
    event.content = {'destination': destination,
                     'message': message}
    return event


# pylint: disable=unused-argument
def unit(size='small'):
    """Handle tokens from requests."""
    env_test_size = os.environ.get("KYTOS_TESTS_SIZE", 'small')
    env_test_type = os.environ.get("KYTOS_TESTS_TYPE", 'unit')

    def inner_func(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if env_test_type == 'unit' and size == env_test_size:
                return func(*args, **kwargs)
            return None
        return wrapper

    return inner_func


# pylint: disable=unused-argument
def integration(size='small'):
    """Handle tokens from requests."""
    env_test_size = os.environ.get("KYTOS_TESTS_SIZE", 'small')
    env_test_type = os.environ.get("KYTOS_TESTS_TYPE", 'unit')

    def inner_func(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if env_test_type == 'integration' and size == env_test_size:
                return func(*args, **kwargs)
            return None
        return wrapper

    return inner_func


# pylint: disable=unused-argument
def e2e(size='small'):
    """Handle tokens from requests."""
    env_test_size = os.environ.get("KYTOS_TESTS_SIZE", 'small')
    env_test_type = os.environ.get("KYTOS_TESTS_TYPE", 'unit')

    def inner_func(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if env_test_type == 'e2e' and size == env_test_size:
                return func(*args, **kwargs)
            return None
        return wrapper

    return inner_func
