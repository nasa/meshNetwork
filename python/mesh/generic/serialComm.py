import time
import crcmod.predefined

class SerialComm(object):
    """Serial communication wrapper class that provides for serializing data to send over serial data links.

    This class is the base class for serial communication and provides reading and writing functionality over the provided serial connection.  Messages being sent and received are relayed using a SLIP message format which provides a CRC for data quality checking.

    Attributes:
        uartNumBytesToRead: Maximum number of bytes to attempt to read from the serial connection.
        serialConn: Serial connection instance used by this class for communication.
        serMsgParser: Serial message parser that parses raw serial data and looks for valid SLIP messages.
        lastMsgSentTime: Time that the last serial message was sent over this connection.
        msgCounter: Counter of the number of messages sent over this serial connection. 
        msgOut: SLIPmsg instance used for storing messages prior to sending over serial line.
        rxBuffer: Raw serial data read from this connection.
        msgEnd: Array location of end of raw serial message decoded from read serial bytes stored in rxBuffer.
    """
 
    def __init__(self, commProcessor, radio, parser):
        self.radio = radio
        self.msgParser = parser
        self.commProcessor = commProcessor

        self.lastMsgSentTime = 0
        self.msgCounter = 0

    def readMsgs(self):
        """Reads and parses any received serial messages."""
        # Read bytes
        self.readBytes(False)
        
        # Parse messages
        self.parseMsgs()

    def parseMsgs(self): 
        # Parse messages
        self.msgParser.parseMsgs(self.radio.getRxBytes())
        
        # Clear rx buffer
        self.radio.clearRxBuffer()
        
    def readBytes(self, bufferFlag=False):
        """Reads raw bytes from radio"""
        self.radio.readBytes(bufferFlag)
    
    def sendBytes(self, msgBytes): # DEPRECATED - duplicative and not used
        """Send raw bytes without further packaging."""
        self.radio.sendMsg(msgBytes)    
    
    def sendMsg(self, msgBytes):
        """Wraps provided data into a SLIPmsg and then sends the message over the serial link
        
        Args:
            timestamp: Time of message.
            cmdId: Command message type identifier.
            msgBytes: Data bytes to be sent in serial message.
        """
        if len(msgBytes) > 0:
            self.lastMsgSentTime = time.time()
            self.msgCounter += 1            
            self.msgCounter = self.msgCounter % 256
            msgOut = self.msgParser.encodeMsg(msgBytes)
            self.radio.sendMsg(msgOut)

    def sendBuffer(self):
        """Send data in transmission buffer over serial connection."""
        self.radio.sendBuffer()

    def bufferTxMsg(self, msgBytes):
        """Add bytes to transmission buffer."""
        if msgBytes:
            msgOut = self.msgParser.encodeMsg(msgBytes)
            self.radio.bufferTxMsg(msgOut)
    
    def processMsg(self, msg, args):
        if self.commProcessor:
            self.commProcessor.processMsg(msg, args)
        
