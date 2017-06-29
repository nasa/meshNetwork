Python
======

Python is the primary development language for the Mesh Network.  New features are first developed and tested in the Python implementation before being ported to other languages. Python was chosen for its flexibility and ease of use which helps facilitate rapid software development.  Development was performed using Python3 with no backwards compatibility to Python2 explicitly included.

Execution
^^^^^^^^^

An example execution script (execute.py) is provided to run the Python implementation. This script will allow a generic node to communicate over the TDMA network using either a full software implementation of the network scheme in Python or an FPGA running the VHDL implementation.  The script should be expanded upon and modified to implement details specific to a particular node type or application.  

The node control interface is provided in the nodeControlProcess.py.  By replacing the generic Node type class instances with specific subclasses, the script can be modified for a specific use case.  Likewise the commProcess.py script controls the process that communicates over the Mesh Network.  This script should not require modification for a specific application.  Network configuration should be handled via the JSON configuration file. 

Python API
^^^^^^^^^^

.. _SerialComm:

SerialComm
----------
The **SerialComm** class is used to communicate with hardware or other software processes.  This class was created originally to pass data via serial communication, but is not restricted to communication over just serial ports. The actual communication layer is provided via the *radio* class member which is a :ref:`Radio <Radio>` object, and thus can be specialized to make use of any communication interface available.  The SerialComm class has methods for sending and receiving raw bytes or formatted messages.  The specific format of messages is controlled by the *msgParser* class member which is of type :ref:`MsgParser <MsgParser>`.

.. _Radio:

Radio
-----
The **Radio** class provides the interface to communication interfaces.  These communication interfaces can be actual hardware radios or just abstraction layers from something like a UDP connection between different software processes. By creating a subclass of Radio, any communication layer can be interfaced to using a similar API. 

NodeConfig
----------
The **NodeConfig** class stores configuration parameters loaded from the JSON configuration file.  The base class contains all the standard parameters, but it can be subclassed to add parameters specific to a particular platform or application.

NodeParams
----------
The **NodeParams** class functions as a wrapper for the node configuration and also includes certain utility functions that need to be accessed by various other portions of the Mesh Network control software.

.. _NodeController:

NodeController
--------------
The **NodeController** class provides common methods for interfacing with the other software running on the node's platform, i.e. the main flight computer software for a flight vehicle application.  Data from the flight computer and from the Mesh Network is processed by the NodeController.  For example, if the flight computer wishes to transfer some set of data over the Mesh Network, it is sent to the Node Controller which in turn packages it and passes it to the Mesh Network for transmission.  Any data received from the Mesh Network is likewise processed by the NodeController and passed to the flight computer.  

NodeExecutive
-------------
The **NodeExecutive** functions as an overseer for the :ref:`NodeController <NodeController>` and the various :ref:`SerialComm <SerialComm>` instances for interfacing with the main node software and the Mesh Network.  The NodeExecutive coordinates when to read from the comm interfaces and provides the received data to the NodeController for consumption. 

.. _CmdDict:

CmdDict
-------
The **CmdDict** class stores information on the format of all types of command messages to be passed over the Mesh Network and to the node host platform.  It has an entry for each command type that defines how to create outgoing messages and how to parse incoming messages of that type.  New command types can be defined for a specific application and added to the main CmdDict.

.. _MsgParser:

MsgParser
---------
The **MsgParser** class is used to create and parse messages from raw bytes.  A MsgParser instance is provided to a :ref:`SerialComm <SerialComm>` instance so that it knows how to process received and outgoing data. Specific message formats can be parsed by creating specialized variants such as the SLIPMsgParser that uses the `Serial Line Internet Protocol <https://en.wikipedia.org/wiki/Serial_Line_Internet_Protocol>`_. 

CommProcessor
-------------
Once the :ref:`MsgParser <MsgParser>` class parses raw received data bytes using the proper protocol, the processed bytes are then passed to the **CommProcessor** to determine how to parse the command contents.  The CommProcessor checks the command ID of each message parsed by the MsgParser and forwards the command to the proper :ref:`CmdProcessor <CmdProcessor>` to be read and formatted back into the original command data.

.. _CmdProcessor:

CmdProcessor
------------
The **CmdProcessor** has the logic for determining how to retrieve the command data from a processed stream of data bytes.  Based on the command ID of each command, it will look up the command format from the :ref:`CmdDict <CmdDict>` and parse the data bytes back into useable command data.  Specific classes can be derived from the CmdProcessor to process and parse platform specific command types.

Detailed Python API
^^^^^^^^^^^^^^^^^^^
.. toctree::
   :maxdepth: 2

   mesh

