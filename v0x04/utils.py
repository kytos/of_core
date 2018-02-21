"""Utilities module for of_core OpenFlow v0x04 operations"""
from kytos.core.events import KytosEvent
from kytos.core.interface import Interface

from napps.kytos.of_core.utils import emit_message_out

from pyof.v0x04.symmetric.echo_request import EchoRequest
from pyof.v0x04.controller2switch.common import ConfigFlag, MultipartType
from pyof.v0x04.controller2switch.multipart_request import (FlowStatsRequest,
                                                            MultipartRequest)
from pyof.v0x04.controller2switch.set_config import SetConfig
from pyof.v0x04.common.action import ControllerMaxLen
from pyof.v0x04.symmetric.hello import Hello


def update_flow_list(controller, switch):
    """Method responsible for request stats of flow to switches.

    Args:
        controller(:class:`~kytos.core.controller.Controller`):
            the controller being used.
        switch(:class:`~kytos.core.switch.Switch`):
            target to send a stats request.

    Returns:
        int: multipart request xid

    """
    multipart_request = MultipartRequest()
    multipart_request.multipart_type = MultipartType.OFPMP_FLOW
    multipart_request.body = FlowStatsRequest()
    emit_message_out(controller, switch.connection, multipart_request)
    return multipart_request.header.xid


def send_desc_request(controller, switch):
    """Method responsible for request stats of flow to switches.

    Args:
        controller(:class:`~kytos.core.controller.Controller`):
            the controller being used.
        switch(:class:`~kytos.core.switch.Switch`):
            target to send a stats request.
    """
    multipart_request = MultipartRequest()
    multipart_request.multipart_type = MultipartType.OFPMP_DESC
    emit_message_out(controller, switch.connection, multipart_request)

def send_port_request(controller, connection):
    """Send a Port Description Request after the Features Reply."""
    port_request = MultipartRequest()
    port_request.multipart_type = MultipartType.OFPMP_PORT_DESC
    emit_message_out(controller, connection, port_request)


def handle_features_reply(controller, event):
    """Handle OF v0x04 features_reply message events.

    This is the end of the Handshake workflow of the OpenFlow Protocol.

    Parameters:
        controller (Controller): Controller being used.
        event (KytosEvent): Event with features reply message.
    """

    connection = event.source
    features_reply = event.content['message']
    dpid = features_reply.datapath_id.value

    switch = controller.get_switch_or_create(dpid=dpid,
                                             connection=connection)
    send_port_request(controller, connection)

    switch.update_features(features_reply)

    return switch


def handle_port_desc(controller, switch, port_list):
    """Update interfaces on switch based on port_list information."""
    for port in port_list:
        interface = Interface(name=port.name.value,
                              address=port.hw_addr.value,
                              port_number=port.port_no.value,
                              switch=switch,
                              state=port.state.value,
                              features=port.curr)
        switch.update_interface(interface)
        port_event = KytosEvent(name='kytos/of_core.switch.port.created',
                                content={
                                    'switch': switch.id,
                                    'port': port.port_no.value,
                                    'port_description': {
                                        'alias': port.name.value,
                                        'mac': port.hw_addr.value,
                                        'state': port.state.value
                                        }
                                    })
        controller.buffers.app.put(port_event)

def send_echo(controller, switch):
    """Send echo request to a datapath.

    Keep the connection alive through symmetric echoes.
    """
    echo = EchoRequest(data=b'kytosd_13')
    emit_message_out(controller, switch.connection, echo)


def send_set_config(controller, switch):
    """Send a SetConfig message after the OpenFlow handshake."""
    set_config = SetConfig()
    set_config.flags = ConfigFlag.OFPC_FRAG_NORMAL
    set_config.miss_send_len = ControllerMaxLen.OFPCML_NO_BUFFER
    emit_message_out(controller, switch.connection, set_config)


def say_hello(controller, connection):
    """Send back a Hello packet with the same version as the switch."""
    hello = Hello()
    emit_message_out(controller, connection, hello)
