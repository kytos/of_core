########
Overview
########

.. attention::

    THIS NAPP IS STILL EXPERIMENTAL AND IT'S EVENTS, METHODS AND STRUCTURES MAY
    CHANGE A LOT ON THE NEXT FEW DAYS/WEEKS, USE IT AT YOUR OWN DISCERNEMENT

The NApp **kytos/of_core** is a NApp responsible to handle OpenFlow basic
operations. The messages covered are:

-  hello messages;
-  reply echo request messages;
-  request stats messages;
-  send a feature request after echo reply;
-  update flow list of each switch;
-  update features;
-  handle all input messages.

Besides the operations related to the messages above and OpenFlow handshake,
this NApp emits basic OpenFlow status events.

##########
Installing
##########

All of the Kytos Network Applications are located in the NApps online
repository. To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/of_core

######
Events
######

******
Listen
******

kytos/core.openflow.raw.in
==========================
  Handle a RawEvent and generate a kytos/core.messages.in.* event.

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of napps.kytos.of_core.utils.GenericHello message
      'source': <object>, # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x01.messages.in.ofpt_stats_reply
================================================
  Listen to any input of OpenFlow StatsReply in versions 1.0 (v0x01) and
  updates the switches list with its Flow Stats.

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow StatsReply message
      'source': <object>, # instance of kytos.core.switch.Connection class
    }


kytos/of_core.v0x0[14].messages.in.ofpt_features_reply
======================================================
  Listen to any input of OpenFlow FeaturesReply in versions 1.0 (v0x01) or 1.3
  (v0x04).

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow FeaturesReply message
      'source': <object>, # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.in.ofpt_multipart_reply
====================================================
  Listen to any input of OpenFlow MultiPartReply in versions 1.3 (v0x04) and
  handles Port Description Reply messages

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow MultiPartReply message
      'source': <object>, # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x0[14].messages.in.ofpt_echo_request
====================================================
  Listen to any input of OpenFlow EchoRequest in versions 1.0 (v0x01) or
  1.3 (v0x04) and generate an appropriate echo reply.

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow EchoRequest message
      'source': <object>, # instance of kytos.core.switch.Connection class
    }


kytos/of_core.v0x0[14].messages.out.ofpt_echo_reply
===================================================
  Listen to any output of OpenFlow EchoReply in versions 1.0 (v0x01) or
  1.3 (v0x04).

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow EchoReply message
      'destination': <object>, # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x0[14].messages.out.ofpt_features_request
=========================================================
  Listen to any output of OpenFlow FeaturesRequest in versions 1.0 (v0x01) or
  1.3 (v0x04) and ensure request has actually been sent before changing state.

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow FeaturesRequest message
      'destination': <object>, # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x[0-9a-f]{2}.messages.in.hello_failed
=====================================================
  Listen to any input of OpenFlow HelloFailed in versions 1.0 (v0x01) or
  1.3 (v0x04) and close the destination connection.

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow HelloFailed message
      'destination': <object>, # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x0[14].messages.out.hello_failed
================================================
  Listen to any output of OpenFlow HelloFailed in versions 1.0 (v0x01) or
  1.3 (v0x04) and close the destination connection.

Content
-------

.. code-block:: python3

    { 'message': <object> # instance of a python-openflow HelloFailed message
      'destination': <object>, # instance of kytos.core.switch.Connection class
    }

********
Generate
********

kytos/of_core.switch.interface.modified
=======================================
Event reporting that a port was modified in the datapath.
It is dispatched after parsing a PortStatus sent by a datapath.

It is worth to say that the PortStatus message just announces that some Port
attributes were modified, but it does not state which one. The event dispatched
will hold all **current** Port attributes. If a NApp needs to know which
attribute was modified, it will need to compare the current list of attributes
with the previous one.

Content
-------

.. code-block:: python

   {
    'interface': <interface> # Instance of Interface class
   }

kytos/of_core.switch.interface.deleted
=====================================
Event reporting that a port was deleted from the datapath.
It is dispatched after parsing a PortStatus sent by a datapath.

Content
-------

.. code-block:: python

   {
    'interface': <interface> # Instance of Interface class
   }

kytos/of_core.reachable.mac
===============================
Event reporting that a mac address is reachable from a specific switch/port.
This information is retrieved from PacketIns generated sent by the switches.

Content
-------

.. code-block:: python

    { 
      'switch': <switch.id>,   # switch identification
      'port': <port.port_no>,  # port number
      'reachable_mac': <reachable_mac_address>  # string with mac address
    }

kytos/of_core.hello_failed
==========================
Send Error message and emit event upon negotiation failure.

Content
-------

.. code-block:: python3

    {
      'source': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x01.messages.out.ofpt_stats_request
===================================================
Send a StatsRequest message for request stats of flow to switches.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow StatsRequest message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x01.messages.out.ofpt_echo_request
==================================================
Send an EchoRequest to a datapath.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow EchoRequest message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x01.messages.out.ofpt_set_config
================================================
Send a SetConfig message after the Openflow handshake.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow SetConfig message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x01.messages.out.ofpt_hello
===========================================
Send back a Hello packet with the same version as the switch.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow Hello message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_multipart_request
=======================================================
Send a Port Description Request after the Features Reply.
This message will be a Multipart with the type ``OFPMP_PORT_DESC``.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow MultiPart message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_echo_request
==================================================
Send EchoRequest to a datapath.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow EchoRequest message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_set_config
================================================
Send a SetConfig message after the OpenFlow handshake.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow SetConfig message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x04.messages.out.ofpt_hello
===========================================
Send back a Hello packet with the same version as the switch.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow Hello message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x01.messages.in.{name}
======================================
Emit a KytosEvent for an incoming message containing the message
and the source.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow
      'source': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x0[14].messages.out.EchoReply
=============================================
Send an Echo Reply message to data path.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow EchoReply message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x0[14].messages.out.ofpt_error
==============================================
Send Error message and emit event upon negotiation failure.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow ErrorMsg message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }

kytos/of_core.v0x0[14].messages.out.ofpt_features_request
=========================================================
Send a feature request to the switch.

Content
-------

.. code-block:: python3

    { 'message': <object>, # instance of a python-openflow FeaturesRequest message
      'destination': <object> # instance of kytos.core.switch.Connection class
    }
