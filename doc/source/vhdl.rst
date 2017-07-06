VHDL
====

For the FPGA implementation of the Mesh Network, VHDL logic was created to control a Microsemi ProAsic3 FPGA.  The VHDL logic is responsible for controlling the TDMA Frame and Cycle, interfacing with the GPS for clock synchronization, interfacing with the mesh radio, and relaying data between the main node computer and the network.  While the logic may not be directly transferrable to another platform, the logic is provided as a starting point for development. 

API
^^^

.. _tdmaCtrl:

tdmaCtrl
--------
The **tdmaCtrl** entity processes and outputs TDMA control messages such as the TDMA MeshStatus messages.  During Mesh Network initialization by a node, tdmaCtrl uses the :ref:`dataParser <dataParser>` to monitor the radio for any existing network traffic to determine whether a network already exists.  If a MeshStatus message is received, the network initialization time is passed to tdmaCtrl and used for initialization of the node into the network.  If no status message is received prior to the init timer elapsing, the node will assume no existing network and start a new one.  Once an initialization time is determined, tdmaCtrl will create outgoing MeshStatus messages for transmission by the node.

tdma
----
The **tdma** entity is responsible for controlling the current TDMA mode for a network node.  tdma monitors the current Frame and Cycle time and toggles the mode between *transmit*, *receive*, and *sleep* appropriately. tdma also interfaces with the :ref:`radio <vhdl_radio>` entity to tell it when to change modes.

.. _memController:

memController
-------------
The **memController** entity controls all access to the FRAM memory.  All memory reads and writes requested by other entities are performed via the memController. The memController's internal logic handles the proper sequences to interface with the memory.

memInterface
------------
The **memInterface** entity is responsible for partitioning the FRAM memory into the desired portions and maintaining the current read and write locations for each partition.  Other entities requesting memory access to a particular partition make a request via the memInterface which handles deconflicting simultaneous requests.  Data requests to the memInterface are passed by it to the :ref:`memController <memController>`.

uart
----
The **uart** entity implements a standard RS-232 UART communication interface.  The uart entity can be instantiated to communicate with any RS-232 compatible device.    

userInterface
-------------
The **userInterface** handles control of LEDs and pins on the hardware to provide a human user interface.  Pin values associated with switches are read by the userInterface and LEDs can be illuminated to return status to the user.

clockTime
---------
The **clockTime** entity is responsible for maintaining an accurate clock for the TDMA network.  High precision time is maintained by parsing GPS time messages from an attached GPS receiver.  An absolute clock second count is maintained with the start of each second conditioned by the GPS PPS signal and the current fraction of the second incremented by the FPGA's clock frequency.

dataProcessor
-------------
The **dataProcessor** coordinates reading and writing from the interfaces with the radio and the main node computer.  Outgoing data from the node is stored in the memory until the node's TDMA received slot and is then retrieved by the dataProcessor for transmission over the radio.  Likewise data received from the mesh network is stored in memory prior to processing and transmission to the node computer. The dataProcessor also interfaces with :ref:`tdmaCtrl <tdmaCtrl>` for handling of TDMA control messages.

.. _dataParser:

dataParser
----------
The **dataParser** is used to parse commands and messages from raw received bytes.  Most mesh network traffic is passed directly through to the node computer, but the dataParser will monitor traffic to parse TDMA control messages.

.. _vhdl_radio:

radio
-----
The **radio** entity provides the interface to control the radio hardware. Currently it is used only to control when the radio is on for transmission and reception or off to conserve power.  
