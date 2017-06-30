.. Mesh Network Communication System documentation master file, created by
   sphinx-quickstart on Thu Apr  9 07:44:00 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Mesh Network Communication System Documentation
===============================================

The Mesh Network Communication system is a peer-to-peer communication network architecture that enables communication between network nodes of various types.  The initial primary goal of the system was to enable communication between small formations of cubesats or other small satellites, but the basic mesh architecture is applicable to data exchange between network assets of any type.  The system has been flight tested on formations of small unmanned aerial systems (sUAS) and shown to provide low latency data throughput for dynamic flight environments.  

As the use of cubesats and other small satellites continues to grow, communicating with the larger numbers of on-orbit assets will start to stress ground communications capabilities.  In addition to single satellite missions, multiple organizations have begun to develop and deploy constellations of satellites and more are planned in the near future.  To help relieve the demands being placed on ground stations and to enable communication between satellites, The network employs a TDMA-based mesh architecture that allows peer-to-peer communication without requiring a central master node or router to control the network.  This eliminates the possibility of single-point caused by the loss of the network master.  

The designed mesh network allows a small formation of satellites, aircraft, ground assets, or other network node types to collaborate and exchange data to enable their mission and reduce communication requirements to a central control center.  By exchanging data directly with other network nodes, the nodes can function more autonomously with less outside intervention required.  The communication system was designed to be reconfigurable for different applications.  Some of the driving design goals were to have low latency, to allow for addition and removal of communication nodes in the network without interruption, to relay data across the network, and to make the communication architecture hardware agnostic, not requiring it to be dependent on a specific hardware implementation. 

Documentation Contents
======================
.. toctree::
   :maxdepth: 2

   design
   software
   hardware

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


