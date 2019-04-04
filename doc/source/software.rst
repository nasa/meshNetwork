Software
========

Description
^^^^^^^^^^^

Because of the full Linux development environment afforded by the BeagleBone Black used in the hardware implementations described in the following section, primary software development was performed in Python.  This afforded the developers with a flexible software development environment to quickly create, adapt, and test new features.  The software was developed with modularity in mind, so that it could be modified for use with a wide variety of radios and hardware implementations.  The software was designed using object-oriented processes allowing hardware specific code to inherit from the generic codebase.

Network configuration for a specific application is performed using a JSON-based configuration file that contains configurable parameter values used during execution of the mesh network code. Configuration parameters can also include flight vehicle specific parameters such as radio interfaces and settings. By placing configuration settings in an easily modified human-readable file, this allows for quick reconfiguration of the software without having to modify the source code.  This reconfigurability allows the network performance and behavior to be catered for specific applications, such as modifying the network to prioritize data throughput over low latency for science operations that generate a large amount of data.

For the current generation of hardware which uses an FPGA (field-programmable gate array), the Python mesh network logic was ported into VHDL (VHSIC Hardware Description Language).  This included the mesh network control itself as well as the time synchronization functions, specifically the interface to the GPS.  Initial development of a C++ implementation that would be more suitable for deployment on operational flight vehicles has also been created. 

Common Application Programming Interface (API)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The software was designed to be flexible for many applications and communication interface types.  To do this, an object-oriented design approach was used.  Base classes are defined that can then be derived from to create new classes with specific platform implementation details.

The software is divided into two main parts which also run as separate processes, NodeControl and Comm.  The NodeControl process handles logic and communication pertaining to interfacing with the main platform flight software, such as a flight computer on an aircraft or spacecraft.  The Comm process handles all Mesh Network logic.  The two processes communicate to pass commands and data from the Mesh Network to the flight computer and vice versa.    

Although the goal is to keep the API as common as possible across the different language implementations, because of different features or capabilities of a given language, the functionality of a given class, or sometimes the classes themselves, may differ between the Python and C++ versions.  The Python API documentation can be used to give a general overview of the software structure, but please refer to the individual language APIs for specific implementation details.

Interface Between Host Platform and Mesh Network
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Mesh Network logic/software is designed to operate as independently as possible from the host platform.  The interface between the host and the mesh network logic is intentionally designed to be simple and concise, so that the host is not required to monitor or control any of the internal mesh network logic.  The host provides the raw data for transmission over the network to the mesh logic which then handles everything downstream from that point to determine when and how to transmit the data over the network.  Incoming data received by the mesh network is likewise parsed and passed back to the host platform as appropriate.  This section documents how the host to mesh network interface operates.

Host To Mesh Network Interface
------------------------------
The Mesh Network receives data from the host platform and transmits it unchanged to the desired destination.  The host passes the data to mesh network using the *queueMeshMsg* method of the **TDMAComm** class.  Along with the raw data, the ID number of the desired destination node is provided to the method.  This method takes the provided data and stores it in the outgoing message queue, *meshQueueIn*.  MeshQueueIn is an array with an entry for broadcast messages, to be sent to all nodes in the network, and an entry for each individual node in the mesh network. During the transmission period for the host platform node, the mesh network logic will trasnmit a mesh packet for each non-empty entry in meshQueueIn.  These outgoing packets are then received by the other mesh network nodes and transmitted across the network to their proper destinations appropriately. 

Mesh Network to Host Interface
------------------------------
Mesh packets received by the host mesh node are received and parsed and then placed in the *hostBuffer* of **TDMAComm** for the host platform to process.  TDMAComm strips the mesh network packet structure from the data prior to placing it in the hostBuffer.  The hostBuffer contents are the raw data bytes sent by other mesh network node host platforms.  The mesh network packet structure is stripped prior to placing the data into the hostBuffer for host platform consumption.


Configuration
^^^^^^^^^^^^^
.. toctree::
   :maxdepth: 2

   config

Python
^^^^^^
.. toctree::
   :maxdepth: 2

   python

Tests
^^^^^
.. toctree::
   :maxdepth: 2

   unittests

C++
^^^
.. toctree::
   :maxdepth: 2

   cpp

VHDL
^^^^
.. toctree::
   :maxdepth: 2

   vhdl

