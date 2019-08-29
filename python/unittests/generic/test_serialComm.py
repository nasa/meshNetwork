import serial, time
from struct import pack
from mesh.generic.nodeParams import NodeParams
from mesh.generic.serialComm import SerialComm
from mesh.generic.radio import Radio
from mesh.generic.nodeCmdProcessor import NodeCmdProcessor
from mesh.generic.slipMsg import SLIPMsg
from test_SLIPMsg import truthSLIPMsg, testMsg
from mesh.generic.nodeState import NodeState
from mesh.generic.formationClock import FormationClock
from mesh.generic.nodeHeader import packHeader
from mesh.generic.cmds import NodeCmds
from mesh.generic.command import Command
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath, testSerialPort

class TestSerialComm:
    
    def setup_method(self, method):
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        self.radio = Radio(self.serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        self.serialComm = SerialComm([NodeCmdProcessor], self.nodeParams, self.radio, [])
        
    def test_readBytes(self):
        """Test receiving bytes."""
        self.serialPort.write(b'12345')
        time.sleep(0.1)
        self.serialComm.readBytes(False)
        assert(self.serialComm.radio.getRxBytes() == b'12345')
    
    def test_sendBytes(self):
        """Test sendBytes method of SerialComm."""
        msgBytes = b'ABCDEF'
        self.serialPort.read(100) # clear serial buffer
        self.serialComm.sendBytes(msgBytes)
        time.sleep(0.1)
        self.serialComm.readBytes()
        assert(self.serialComm.radio.getRxBytes() == msgBytes)   
    
    def test_parseMsgs(self):
        """Test parseMsgs method of SerialComm."""
        # Test parsing of messages
        msgBytes = b'ABCDEF'
        self.serialComm.radio.bufferRxMsg(msgBytes, False) # put test bytes into radio rx buffer
        self.serialComm.parseMsgs()
        assert(len(self.serialComm.msgParser.parsedMsgs) == 1)
        assert(self.serialComm.msgParser.parsedMsgs[0] == b'ABCDEF')

        # Check that radio buffer was cleared
        assert(len(self.serialComm.radio.getRxBytes()) == 0)

    def test_readMsgs(self):
        """Test readMsgs method of SerialComm."""
        # Send message
        msgBytes = b'12345'
        self.serialComm.sendMsg(msgBytes)
        time.sleep(0.1)
        
        # Read messages
        self.serialComm.readMsgs()
        assert(len(self.serialComm.msgParser.parsedMsgs) == 1)
        assert(self.serialComm.msgParser.parsedMsgs[0] == msgBytes) # confirm parsed message matches original

    def test_sendMsg(self):
        """Test sendMsg method of SerialComm."""
        # Create message parser for testing purposes
        msg = SLIPMsg(self.nodeParams.config.parseMsgMax)
        self.serialComm.msgParser.msg = msg

        # Send test message
        msgBytes = b'12345'
        self.serialPort.read(100) # clear serial buffer
        self.serialComm.sendMsg(msgBytes)
        time.sleep(0.1)

        # Read message back and compare
        readBytes = self.serialComm.readMsgs()
        assert(len(self.serialComm.msgParser.parsedMsgs) == 1)
        assert(self.serialComm.msgParser.parsedMsgs[0] == msgBytes)
    
    def test_bufferTxMsg(self):
        """Test bufferTxMsg method of SerialComm."""
        # Create message parser for testing purposes
        msg = SLIPMsg(self.nodeParams.config.parseMsgMax)
        self.serialComm.msgParser.msg = msg
        
        # Test that encoded message buffered
        msgBytes = b'ZYXWVU'
        assert(len(self.serialComm.radio.txBuffer) == 0) # confirm empty tx buffer
        self.serialComm.bufferTxMsg(msgBytes)
        encoder = SLIPMsg(256)
        encoder.encodeMsg(msgBytes)
        truthMsg = encoder.encoded
        assert(self.serialComm.radio.txBuffer == truthMsg) # confirm encoded message placed in tx buffer

    def test_sendBuffer(self):
        """Test sendBuffer method of SerialComm."""
        # Place message in tx buffer
        msgBytes = b'1122334455'
        self.serialComm.bufferTxMsg(msgBytes)
        assert(self.serialComm.radio.txBuffer == msgBytes)

        # Send message and compare received bytes to sent
        assert(self.serialComm.sendBuffer() == len(msgBytes))
        time.sleep(0.1)
        assert(len(self.serialComm.radio.txBuffer) == 0)
        self.serialComm.readBytes()
        assert(self.serialComm.radio.getRxBytes() == msgBytes)

    def test_processMsg(self):
        """Test processMsg method of SerialComm."""
        # Create message and test processing
        nodeStatus = [NodeState(node+1) for node in range(5)]
        clock = FormationClock()
        
        cmdId = NodeCmds['NoOp']
        cmdMsg = Command(cmdId, None, [cmdId, 1, 200]).serialize()
        assert(self.serialComm.processMsg(cmdMsg, args = {'logFile': [], 'nav': [], 'nodeStatus': nodeStatus, 'clock': clock, 'comm': self.serialComm}) == True)

        assert(cmdId in self.serialComm.cmdQueue) # Test that correct message added to cmdQueue   
        
        # Confirm proper return when no message processed successfully
        assert(self.serialComm.processMsg(b'12345', args = {'logFile': [], 'nav': [], 'nodeStatus': nodeStatus, 'clock': clock, 'comm': self.serialComm}) == False)


    def test_processMsgs(self):
        """Test processMsgs method of SerialComm."""
        # Create message parser for testing purposes
        msg = SLIPMsg(self.nodeParams.config.parseMsgMax)
        self.serialComm.msgParser.msg = msg
        
        # Create and send test messages
        nodeStatus = [NodeState(node+1) for node in range(5)]
        clock = FormationClock()
        
        cmdId1 = NodeCmds['NoOp'] # No op command
        cmdMsg1 = Command(cmdId1, None, [cmdId1, 1, 200]).serialize()
        cmdId2 = NodeCmds['GCSCmd'] # GCS command
        cmdMsg2 = Command(cmdId2, {'destId': 1, 'mode': 2}, [cmdId2, 1, 201]).serialize()
        self.serialComm.sendMsg(cmdMsg1)
        self.serialComm.sendMsg(cmdMsg2)
        time.sleep(0.1)

        # Test processing
        self.serialComm.processMsgs(args = {'logFile': [], 'nav': [], 'nodeStatus': nodeStatus, 'clock': clock, 'comm': self.serialComm})

        assert(cmdId1 in self.serialComm.cmdQueue) # Test that correct message added to cmdQueue   
        assert(cmdId2 in self.serialComm.cmdQueue) # Test that correct message added to cmdQueue   

    def test_processBuffers(self):
        """Test processBuffers method of SerialComm."""
        # Test command relay buffer
        testMsg = b'1234567890'
        self.serialComm.cmdRelayBuffer = testMsg
        self.serialComm.processBuffers()
        assert(len(self.serialComm.cmdRelayBuffer) == 0) # buffer flushed
        assert(self.serialComm.radio.txBuffer == testMsg)
        self.serialComm.radio.txBuffer = bytearray()    
 
        # Test command buffer
        testCmd = {'bytes': b'12345'}
        self.serialComm.cmdBuffer['key1'] = testCmd
        assert(self.serialComm.processBuffers() == len(testCmd['bytes']))
        assert(len(self.serialComm.cmdBuffer) == 0) # buffer flushed
        assert(self.serialComm.radio.txBuffer == testCmd['bytes'])
    
