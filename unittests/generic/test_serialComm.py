import serial, time
from struct import pack
from mesh.generic.customExceptions import NoSerialConnection
from mesh.generic.nodeParams import NodeParams
from mesh.generic.serialComm import SerialComm
from mesh.generic.radio import Radio
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.commProcessor import CommProcessor
from uav.pixhawkCmdProcessor import PixhawkCmdProcessor
from mesh.generic.slipMsg import SLIPmsg
from test_SLIPmsg import truthSLIPMsg, testMsg
from mesh.generic.cmds import PixhawkCmds
from mesh.generic.nodeState import NodeState
from mesh.generic.formationClock import FormationClock
from mesh.generic.nodeHeader import packHeader
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath, testSerialPort
from unittests.testHelpers import createEncodedMsg

class TestSerialComm:
    
    def setup_method(self, method):
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        self.radio = Radio(self.serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        commProcessor = CommProcessor([PixhawkCmdProcessor], self.nodeParams)
        self.serialComm = SerialComm(commProcessor, self.radio, msgParser)
        

    def test_bufferTxMsg(self):
        """Test bufferTxMsg method of SerialComm."""
        assert(len(self.serialComm.radio.txBuffer) == 0) # confirm empty tx buffer
        self.serialComm.bufferTxMsg(testMsg)
        truthMsg = createEncodedMsg(testMsg)
        assert(self.serialComm.radio.txBuffer == truthMsg) # confirm message placed in tx buffer

    def test_sendBuffer(self):
        """Test sendBuffer method of SerialComm."""
        # Place message in tx buffer
        self.serialComm.bufferTxMsg(testMsg)
        assert(len(self.serialComm.radio.txBuffer) > 0)

        # Send message and compare received bytes to sent
        self.serialComm.sendBuffer()
        assert(len(self.serialComm.radio.txBuffer) == 0)
        time.sleep(0.1)
        self.serialComm.readBytes()
        truthMsg = createEncodedMsg(testMsg)
        serBytes = self.serialComm.radio.getRxBytes()
        assert(serBytes == truthMsg)
        
    def test_sendBytes(self):
        """Test sendBytes method of SerialComm."""
        msgBytes = b'ABCDEF'
        self.serialPort.read(100) # clear serial buffer
        self.serialComm.sendBytes(msgBytes)
        time.sleep(0.1)
        readBytes = self.serialPort.read(100)
        assert(readBytes == msgBytes)   

    def test_sendMsg(self):
        """Test sendMsg method of SerialComm."""
        # Send test message
        msgBytes = testMsg
        self.serialPort.read(100) # clear serial buffer
        self.serialComm.sendMsg(testMsg)
        time.sleep(0.1)
        readBytes = self.serialPort.read(100)

        # Encode test message and compare to bytes read
        truthMsg = createEncodedMsg(testMsg)
        assert(readBytes == truthMsg)   

    def test_parseMsgs(self):
        """Test parseMsgs method of SerialComm."""
        # Place multiple messages in rx buffer
        truthMsg = createEncodedMsg(testMsg)
        truthMsg2 = createEncodedMsg(testMsg + b'999')
        self.serialComm.radio.rxBuffer[0:len(truthMsg)] = truthMsg
        self.serialComm.radio.rxBuffer[len(truthMsg):len(truthMsg) + len(truthMsg2)] = truthMsg2
        self.serialComm.radio.bytesInRxBuffer = len(truthMsg) + len(truthMsg2)

        # Parse messages
        self.serialComm.parseMsgs()
        assert(len(self.serialComm.msgParser.parsedMsgs) == 2)
        assert(self.serialComm.msgParser.parsedMsgs[0] == testMsg) # confirm parsed message matches original
        assert(self.serialComm.msgParser.parsedMsgs[1] == testMsg + b'999') # confirm parsed message matches original

    def test_readMsgs(self):
        """Test readMsgs method of SerialComm."""
        # Send messages
        self.serialComm.sendMsg(testMsg)
        self.serialComm.sendMsg(testMsg + b'999')
        time.sleep(0.1)
        
        # Read messages
        self.serialComm.readMsgs()
        assert(len(self.serialComm.msgParser.parsedMsgs) == 2)
        assert(self.serialComm.msgParser.parsedMsgs[0] == testMsg) # confirm parsed message matches original
        assert(self.serialComm.msgParser.parsedMsgs[1] == testMsg + b'999') # confirm parsed message matches original

    def test_processMsg(self):
        """Test processMsg method of SerialComm."""

        # Create message and test processing
        nodeStatus = [NodeState(node+1) for node in range(5)]
        clock = FormationClock()
        
        cmdId = PixhawkCmds['FormationCmd']
        cmdMsg = packHeader(testCmds[cmdId].header) + testCmds[cmdId].body
        self.serialComm.processMsg(cmdMsg, args = {'logFile': [], 'nav': [], 'nodeStatus': nodeStatus, 'clock': clock, 'comm': self.serialComm})

        assert(cmdId in self.serialComm.commProcessor.cmdQueue) # Test that correct message added to cmdQueue   
        

    
