mesh package
============

The **mesh** package contains all of the network management and control logic for the Python implementation of the Mesh Network.  This package has two subpackages: *generic* and *interface*. The generic package contains the actual mesh network control code, while the interface package is used to provide interprocess communication between the communication control process and the node control process, which serves as the interface between the mesh network control and the rest of the host platform's computing logic.  In the case of a flight vehicle, the node control process would interface with the vehicle's flight computer.  The interface package makes use of the Google Protocol Buffer API to serialize and exchange data between processes.

Subpackages
-----------

.. toctree::

    mesh.generic
    mesh.interface

Module contents
---------------

.. automodule:: mesh
    :members:
    :undoc-members:
    :show-inheritance:
