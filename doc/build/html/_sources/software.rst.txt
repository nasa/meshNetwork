Software
========

Description
-----------

Because of the full Linux development environment afforded by the BeagleBone Black used in the hardware implementations described in the following section, primary software development was performed in Python.  This afforded the developers with a flexible software development environment to quickly create, adapt, and test new features.  The software was developed with modularity in mind, so that it could be modified for use with a wide variety of radios and hardware implementations.  The software was designed using object-oriented processes allowing hardware specific code to inherit from the generic codebase.

Network configuration for a specific application is performed using a JSON-based configuration file that contains configurable parameter values used during execution of the mesh network code. Configuration parameters can also include flight vehicle specific parameters such as radio interfaces and settings. By placing configuration settings in an easily modified human-readable file, this allows for quick reconfiguration of the software without having to modify the source code.  This reconfigurability allows the network performance and behavior to be catered for specific applications, such as modifying the network to prioritize data throughput over low latency for science operations that generate a large amount of data.

For the current generation of hardware which uses an FPGA (field-programmable gate array), the Python mesh network logic was ported into VHDL (VHSIC Hardware Description Language).  This included the mesh network control itself as well as the time synchronization functions, specifically the interface to the GPS.  Initial development of a C++ implementation that would be more suitable for deployment on operational flight vehicles has also been created. 

Common Application Programming Interface (API)
----------------------------------------------

The software was designed to be flexible for many applications and communication interface types.  To do this, an object-oriented design approach was used.  Base classes are defined that can then be derived from to create new classes with specific platform implementation details.

The software is divided into two main parts which also run as separate processes, NodeControl and Comm.  The NodeControl process handles logic and communication pertaining to interfacing with the main platform flight software, such as a flight computer on an aircraft or spacecraft.  The Comm process handles all Mesh Network logic.  The two processes communicate to pass commands and data from the Mesh Network to the flight computer and vice versa.    

Although the goal is to keep the API as common as possible across the different language implementations, because of different features or capabilities of a given language, the functionality of a given class, or sometimes the classes themselves, may differ between the Python and C++ versions.  The Python API documentation can be used to give a general overview of the software structure, but please refer to the individual language APIs for specific implementation details.

Configuration
-------------
.. toctree::
   :maxdepth: 2

   config

Python
------
.. toctree::
   :maxdepth: 2

   python

Tests
^^^^^
.. toctree::
   :maxdepth: 2

   unittests

C++
---
.. toctree::
   :maxdepth: 2

   cpp

VHDL
----
.. toctree::
   :maxdepth: 2

   vhdl

