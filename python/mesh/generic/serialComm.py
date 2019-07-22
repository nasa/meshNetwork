from collections import OrderedDict
from mesh.generic.msgParser import MsgParser
from mesh.generic.customExceptions import InvalidRadio
from mesh.generic.radio import Radio
from mesh.generic.deserialize import deserialize
from mesh.generic.cmdProcessor import processHeader
from struct import unpack

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
 
    def __init__(self, msgProcessors, nodeParams, radio, parser=None):
        self.radio = radio
        if (parser):
            self.msgParser = parser
        else: # use default parser
            self.msgParser = MsgParser({'parseMsgMax': 10})

        self.lastMsgSentTime = 0
        self.msgCounter = 0
        
        # Message processing
        self.cmdQueue = OrderedDict()   
        self.msgProcessors = msgProcessors
        self.nodeParams = nodeParams
        
        # Command buffers (external commands from node host)
        self.cmdBuffer = dict()
        self.cmdRelayBuffer = bytearray() # data relay

    @property
    def radio(self):
        return self.__radio

    @radio.setter
    def radio(self, radio):
        if (isinstance(radio, Radio)):
            self.__radio = radio
        else:
            raise InvalidRadio("Invalid Radio input provided to SerialComm.")

    def readMsgs(self):
        """Reads and parses any received serial messages."""
        # Read bytes
        self.readBytes(False)
        
        # Parse messages
        self.parseMsgs()

    def parseMsgs(self): 
        # Parse messages
        bytesRead = self.radio.getRxBytes()
        
        #if (len(bytesRead) > 0):
            #print("Node " + str(self.nodeParams.config.nodeId) + " - Number of bytes read: " + str(len(bytesRead)))
        
        self.msgParser.parseMsgs(bytesRead)
        
        #print(str(self.nodeParams.config.nodeId) + " - " + str(self.radio.bytesInRxBuffer)) 

        # Clear rx buffer
        self.radio.clearRxBuffer()
        
    def readBytes(self, bufferFlag=False):
        """Reads raw bytes from radio"""
        self.radio.readBytes(bufferFlag)
    
    def sendBytes(self, msgBytes): 
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
            self.lastMsgSentTime = self.nodeParams.clock.getTime()
            self.msgCounter = (self.msgCounter + 1) % 256            
            msgOut = self.msgParser.encodeMsg(msgBytes)
            self.sendBytes(msgOut)

    def sendBuffer(self):
        """Send data in transmission buffer over serial connection."""
        return self.radio.sendBuffer()
            
    def processBuffers(self):
        if self.cmdBuffer: # command buffer
            #noRepeatCmds = []
            for key in self.cmdBuffer:
                self.bufferTxMsg(self.cmdBuffer[key]['bytes'])
                #if self.cmdBuffer[key]['txInterval'] == 0: # no repeat
                #    noRepeatCmds.append(key)
            #for key in noRepeatCmds: # remove non-repeat commands
            #    self.cmdBuffer.pop(key)
            self.cmdBuffer = dict()
                
        if self.cmdRelayBuffer: # Add commands to tx buffer and clear relay buffer
            #for cmd in cmdRelayBuffer:
            #    self.bufferTxMsg(cmd)
            self.radio.bufferTxMsg(self.cmdRelayBuffer)
            self.cmdRelayBuffer = bytearray()
                
    def bufferTxMsg(self, msgBytes):
        """Add bytes to transmission buffer."""
        if msgBytes:
            msgOut = self.msgParser.encodeMsg(msgBytes)
            self.radio.bufferTxMsg(msgOut)
    
    def execute(self):
        """Execute communication cycle."""
        pass
        
    def processMsgs(self, args=[]):
        """Read and process any received messages."""
        self.readMsgs()
        if self.msgParser.parsedMsgs:
            for i in range(len(self.msgParser.parsedMsgs)):
                self.processMsg(self.msgParser.parsedMsgs.pop(0), args)
    
    def processMsg(self, msg, args):
        """Processes parsed serial messages.
        Args:
            msg: Serial message to be processed.
            args: Other arguments needed for processing serial message.
        """
        if len(msg) > 0:
            nodeStatus = args['nodeStatus']
            comm = args['comm']
            clock = args['clock']
    
            # Parse command header
            cmdId = unpack('B',msg[0:1])[0]
            header = deserialize(msg, cmdId, 'header')
            if (processHeader(self, header, msg, nodeStatus, clock, comm) == False): # stale command
                return False

            # Parse command id

            # Pass command to proper processor
            for processor in self.msgProcessors:
                if cmdId in processor['cmdList'].values():
                    return processor['msgProcessor'](self, cmdId, header, msg, args)
                    break

        return False
            
