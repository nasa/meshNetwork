import serial, time
from mesh.generic.nodeParams import NodeParams
from mesh.generic.serialComm import SerialComm
from mesh.generic.nodeExecutive import NodeExecutive
from mesh.generic.nodeState import NodeState, LinkStatus
from mesh.generic.radio import Radio
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.formationClock import FormationClock
from unittests.testConfig import configFilePath, testSerialPort, testSerialPort2

class TestNodeExecutive:
    
    def setup_method(self, method):
        self.nodeParams = NodeParams(configFile=configFilePath)
        
        # Setup comms
        self.serialConfig = {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': self.nodeParams.config.rxBufferSize}
        self.serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        radio = Radio(self.serialPort, self.serialConfig)
        nodeComm = SerialComm([], radio, [])
        
        #self.FCSerialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        #radio = Radio(self.FCSerialPort, serialConfig)
        FCComm = SerialComm([], radio, [])        

        # Create executive
        self.nodeExecutive = NodeExecutive(self.nodeParams, None, [nodeComm], FCComm, [])

    def test_processNodeMsg(self):
        """Test processNodeMsg method of NodeExecutive."""
        # Create a message parser to test parsing of multiple messages
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        self.nodeExecutive.nodeComm[0].msgParser = msgParser
        
        # Confirm that messages correctly read
        testMsg1 = b'ABCDE'
        testMsg2 = b'FGHJI'
        self.nodeExecutive.nodeComm[0].sendMsg(testMsg1)
        self.nodeExecutive.nodeComm[0].sendMsg(testMsg2)
        time.sleep(0.1)       
 
        self.nodeExecutive.processNodeMsg(self.nodeExecutive.nodeComm[0])
        assert(len(self.nodeExecutive.nodeComm[0].msgParser.parsedMsgs) == 2)
        assert(self.nodeExecutive.nodeComm[0].msgParser.parsedMsgs[0] == testMsg1)
        assert(self.nodeExecutive.nodeComm[0].msgParser.parsedMsgs[1] == testMsg2)

    def test_processFCMsg(self):
        """Test processFCMsg method of NodeExecutive."""
        # Create a message parser to test parsing of multiple messages
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        self.nodeExecutive.FCComm.msgParser = msgParser
        
        # Confirm that messages correctly read
        testMsg1 = b'ABCDE'
        testMsg2 = b'FGHJI'
        self.nodeExecutive.FCComm.sendMsg(testMsg1)
        self.nodeExecutive.FCComm.sendMsg(testMsg2)
        time.sleep(0.1)       
 
        self.nodeExecutive.processFCMsg()
        assert(len(self.nodeExecutive.FCComm.msgParser.parsedMsgs) == 2)
        assert(self.nodeExecutive.FCComm.msgParser.parsedMsgs[0] == testMsg1)
        assert(self.nodeExecutive.FCComm.msgParser.parsedMsgs[1] == testMsg2)

    def test_sendFCCmds(self):
        """Test sendFCCmds method of NodeExecutive."""
        # Verify that buffered data is sent
        testMsg = b'12345'
        self.nodeExecutive.FCComm.bufferTxMsg(testMsg)

        assert(self.nodeExecutive.FCComm.radio.txBuffer == testMsg)
        self.nodeExecutive.sendFCCmds()
        time.sleep(0.1)
        assert(len(self.nodeExecutive.FCComm.radio.txBuffer) == 0)
        self.nodeExecutive.FCComm.readBytes()
        assert(self.nodeExecutive.FCComm.radio.rxBuffer[0:self.nodeExecutive.FCComm.radio.bytesInRxBuffer] == testMsg) # check that transmitted bytes received via loopback

    def test_sendNodeCmds(self):
        """Test sendNodeCmds method of NodeExecutive."""
        # Verify that buffered data is sent
        testMsg = b'ABCDE'
        self.nodeExecutive.nodeComm[0].bufferTxMsg(testMsg)

        assert(self.nodeExecutive.nodeComm[0].radio.txBuffer == testMsg)
        self.nodeExecutive.sendNodeCmds()
        time.sleep(0.1)
        assert(len(self.nodeExecutive.nodeComm[0].radio.txBuffer) == 0)
        self.nodeExecutive.nodeComm[0].readBytes()
        assert(self.nodeExecutive.nodeComm[0].radio.rxBuffer[0:self.nodeExecutive.nodeComm[0].radio.bytesInRxBuffer] == testMsg) # check that transmitted bytes received via loopback

    def test_executeNodeSoftware(self):
        """Test executeNodeSoftware method of NodeExecutive."""
        # Populate comm instances for test
        FCSerialPort = serial.Serial(port=testSerialPort2, baudrate=57600, timeout=0)
        radio = Radio(FCSerialPort, self.serialConfig)
        self.nodeExecutive.FCComm.radio = radio
        FCCommOutMsg = b'12345'
        FCCommInMsg = b'67890'
        self.nodeExecutive.FCComm.sendMsg(FCCommInMsg)        
        self.nodeExecutive.FCComm.bufferTxMsg(FCCommOutMsg)

        nodeCommOutMsg = b'ABCDE'
        nodeCommInMsg = b'FGHIJ'
        self.nodeExecutive.nodeComm[0].sendMsg(nodeCommInMsg)        
        self.nodeExecutive.nodeComm[0].bufferTxMsg(nodeCommOutMsg)
            
        # Execute method and check for message transmission and reception 
        time.sleep(0.1)
        self.nodeExecutive.executeNodeSoftware()
        time.sleep(0.1)
        assert(self.nodeExecutive.FCComm.msgParser.parsedMsgs[0] == FCCommInMsg) # test incoming message received
        self.nodeExecutive.FCComm.readBytes()
        assert(self.nodeExecutive.FCComm.radio.rxBuffer[0:self.nodeExecutive.FCComm.radio.bytesInRxBuffer] == FCCommOutMsg) # check that transmitted bytes received via loopback
        assert(self.nodeExecutive.nodeComm[0].msgParser.parsedMsgs[0] == nodeCommInMsg)
        self.nodeExecutive.FCComm.readBytes()
        assert(self.nodeExecutive.nodeComm[0].radio.rxBuffer[0:self.nodeExecutive.nodeComm[0].radio.bytesInRxBuffer] == nodeCommOutMsg) # check that transmitted bytes received via loopback

