C++
===



Coming soon!

C++ API
^^^^^^^^^^

.. _SerialComm:

SerialComm
----------
The **SerialComm** class is used to communicate with hardware or other software processes.  This class was created originally to pass data via serial communication, but is not restricted to communication over just serial ports. The actual communication layer is provided via the *radio* class member which is a :ref:`Radio <Radio>` object, and thus can be specialized to make use of any communication interface available.  The SerialComm class has methods for sending and receiving raw bytes or formatted messages.  The specific format of messages is controlled by the *msgParser* class member which is of type :ref:`MsgParser <MsgParser>`.

.. _Radio:
