Configuration
=============

Mesh network configuration parameters and other settings for a particular application are provided in a JSON (JavaScript Object Notation) configuration file that is human-readable and quickly modifiable.  The configuration file is used by both the Python and C++ implementations.

Configuration File
------------------

The configuration file is a JSON-based file that contains configurable parameter values used during execution of the mesh network code.  By putting important values in a configuration file, this allows for quick reconfiguration of the software without having to modify the source code.  The configurable parameters are listed below with descriptions, value type, and typical default values.

The configuration file is broken down into several sections for different portions of the network control logic.  Additionally, user-specified configuration sections can be added to include configuration for node platform-specific software.  The configuration file is loaded and parsed by the *NodeConfig* class which can be sub-classed to load new platform-specific configuration data.
Some parameters are specific to a particular vehicle type while others are required for all vehicles.  The list of parameters of each type are listed below including the data type.  For further descriptions of each parameter, refer to the NodeConfig class description in the source code documentation. An example node configuration file ('nodeConfig.json') is provided in the base Python directory.  For more detail on an individual configuration parameter, please see below or reference the :ref:`NodeConfig <NodeConfig>` documentation.

Node Parameters
^^^^^^^^^^^^^^^^^^^
These values are stored in the "node" array and are required in all mesh network configuration files.

* maxNumNodes (int)	
* platform (string)
* nodeUpdateTimeout (double)
* commType (string)
* parseMsgMax (int)
* rxBufferSize (int)
* nodeUpdateTimeout (float)
* FCCommWriteInterval (float)
* FCCommDevice (string)
* FCBaudrate (int)
* numMeshNetworks (int)
* meshDevices (array of strings)
* radios (array of strings)
* msgParsers (array of strings)
* meshBaudrate (int)
* cmdInterval (float)
* logInterval (float)
* gcsPresent (bool)

Interface
^^^^^^^^^
These values are stored in the "interface" array, provide configuration information for communicating between the comm and node control processes, and are required in all mesh network configuration files.

* nodeCommIntIP (string): IP address of network interface between processes.
* commRdPort (int): UDP port for incoming messages to comm process.
* commWrPort (int): UDP port for outgoing messages from comm process.

TDMA Configuration Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
These parameters are stored in the "tdmaConfig" array.  They are required for configuration of the TDMA comm protocol.

* txBaudrate (int): Radio transmission baudrate.  This value is used to compute other configuration parameters.
* enableLength (double): Length of time in seconds of enable period for starting transmit or receive slot. 
* slotGuardLength (double): Length in seconds of guard at the end of slot prior to start of new slot.
* preTxGuardLength (double): Length in seconds of guard prior to beginning of transmit period.  During this period, both the transmitting and receiving radios are on, and the receiving radios begin listening even though transmission should not begin until this guard period is over. 
* postTxGuardLength (double): Length in seconds of guard after transmit period.  During this period, the transmitting radio should have stopped transmitting and been turned off, but the receiving radios will continue listening until this guard period is over. 
* txLength (double): Length in seconds of the transmission period.  All messages must be sent by the transmitter before the end of this period.
* rxDelay (percentage): Percentage (in decimal format) of transmit time that should be delayed prior to a receiving node attempting a serial read.
* initTimeToWait (double): Time in seconds that a new node should wait and listen for messages from an existing mesh network.  If this period elapses without a message being received, the new node assumes it is the first node and establishes the mesh network.
* maxNumSlots (int): The maximum number of slots available in the TDMA cycle, i.e. the number of nodes that can join the mesh network.
* desiredDataRate (double): The desired frame rate in Hz.  For example, if it is desired for each node to have a transmission period twice per second, this value would be 2.
* initSyncBound (double): The initial maximum allowable time offset in seconds.  The node software will not begin execution until the absolute value of the time offset is below this value.
* operateSyncBound (double):  The maximum allowable time offset value in seconds during node operation.  If the absolute value of the time offset exceeds this value while the node software is executing, the node will take corrective action.
* offsetTimeout (double): Maximum time in seconds between valid offset measurements.  If the time between offset updates is greater than this value, a node will take corrective action.
* offsetTxInterval (double): Time in seconds between time offset messages.
* statusTxInterval (double): Time in seconds between mesh status messages.
* linksTxInterval (double): Time in seconds between link status messages.
* blockTxRequestTimeout (int): The length of time in frames that a node will wait for responses from other nodes after it has requested a block transfer.  If this period expires, the request is invalidated. 
* minBlockTxDelay (int): The minimum number of frames between when a block transfer is requested and when it can begin.
* maxTxBlockSize (int): Maximum number of data blocks for a block transmit request.
* fpga (bool): Flag indicating whether an FPGA is being used.
* OPTIONAL fpgaFailsafePin (string): GPIO pin for issuing failsafe to FPGA.
* OPTIONAL fpgaFifoSize (int): Size of FPGA outgoing message buffer.
* OPTIONAL: sleepPin (string): GPIO pin for sleeping the radio.
