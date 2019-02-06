import serial, math
from collections import deque
from mesh.generic.nodeState import NodeState
from mesh.generic.nodeParams import NodeParams
from mesh.generic.radio import Radio
from mesh.generic.serialComm import SerialComm
from mesh.generic.cmdProcessor import checkCmdCounter, updateNodeMsgRcvdStatus, processHeader
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.cmds import NodeCmds
from mesh.generic.nodeHeader import packHeader
from unittests.testHelpers import createEncodedMsg
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath, testSerialPort

class TestCmdProcessor:
    
    def setup_method(self, method):
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        self.radio = Radio(self.serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        self.comm = SerialComm([], self.nodeParams, self.radio, msgParser)
        #self.comm = TDMAComm([], [], [], self.nodeParams)
    
 
    def test_checkCmdCounter(self):
        """Test checkCmdCounter method."""

        # Check that command relay buffer is empty
        assert(self.comm.cmdRelayBuffer == bytearray())

        ### Test method with command that includes a command counter
        checkCmdCounter(self.comm, testCmds[NodeCmds['GCSCmd']].header['header'], testCmds[NodeCmds['GCSCmd']].serialize(), self.comm)
        encodedMsg = createEncodedMsg(testCmds[NodeCmds['GCSCmd']].serialize())
        assert(self.comm.cmdRelayBuffer == encodedMsg)
 
        # Resend with new counter to check cmd is appended to buffer
        #cmdCounter = testCmds[NodeCmds['GCSCmd']].header['header']['cmdCounter'] 
        #header, cmdMsg = self.updateCmdCounterValue(cmdCounter+1, deepcopy(testCmds[NodeCmds['GCSCmd']].header), testCmds[NodeCmds['GCSCmd']].body)
        testCmds[NodeCmds['GCSCmd']].header['header']['cmdCounter'] += 1
        checkCmdCounter(self.comm, testCmds[NodeCmds['GCSCmd']].header['header'], testCmds[NodeCmds['GCSCmd']].serialize(), self.comm)
        #checkCmdCounter(self.comm, header['header'], cmdMsg, self.comm)
        encodedMsg2 = createEncodedMsg(testCmds[NodeCmds['GCSCmd']].serialize())
        assert(self.comm.cmdRelayBuffer == encodedMsg + encodedMsg2)
    
        ## Test various counter values to test acceptance behavior
        # Command counter == 1, stored counter == 0
        self.comm.cmdRelayBuffer = bytearray()
        self.nodeParams.cmdHistory.append(0) # place known cmd counter value in history
        testCmds[NodeCmds['GCSCmd']].header['header']['cmdCounter'] = 1
        checkCmdCounter(self.comm, testCmds[NodeCmds['GCSCmd']].header['header'], testCmds[NodeCmds['GCSCmd']].serialize(), self.comm)
        assert(len(self.comm.cmdRelayBuffer) > 0) # cmd put in relay buffer 

        # Command counter == 1, stored counter == 1
        self.comm.cmdRelayBuffer = bytearray()
        checkCmdCounter(self.comm, testCmds[NodeCmds['GCSCmd']].header['header'], testCmds[NodeCmds['GCSCmd']].serialize(), self.comm)
        assert(len(self.comm.cmdRelayBuffer) == 0) # cmd not put in relay buffer    
        
        ### Send command that should not be relayed
        self.comm.cmdRelayBuffer = bytearray()
        self.nodeParams.cmdHistory = deque(maxlen=50) # clear command history
        checkCmdCounter(self.comm, testCmds[NodeCmds['NoOp']].header['header'], testCmds[NodeCmds['NoOp']].serialize(), self.comm)
        assert(len(self.comm.cmdRelayBuffer) == 0) # cmd not put in relay buffer    
        
    def test_updateNodeMsgRcvdStatus(self):
        """Test updateNodeMsgRcvdStatus method."""
        nodeStatus = [NodeState(node+1) for node in range(5)]

        ## Test that node status updated
        testHeader = {'sourceId': 1, 'cmdId': NodeCmds['NoOp']}
        # Pre-test conditions
        assert(nodeStatus[0].present == False)
        assert(nodeStatus[0].lastMsgRcvdTime < self.nodeParams.clock.getTime())
        updateNodeMsgRcvdStatus(nodeStatus, testHeader, self.nodeParams.clock)
        # Post-test conditions
        assert(nodeStatus[0].present == True)
        assert(math.fabs(nodeStatus[0].lastMsgRcvdTime - self.nodeParams.clock.getTime()) <= 0.1)
        
        ## Test that node status not updated for relayed cmds    
        nodeStatus = [NodeState(node+1) for node in range(5)]
        testHeader = {'sourceId': 1, 'cmdId': NodeCmds['GCSCmd']}
        # Pre-test conditions
        assert(nodeStatus[0].present == False)
        assert(nodeStatus[0].lastMsgRcvdTime < self.nodeParams.clock.getTime())
        updateNodeMsgRcvdStatus(nodeStatus, testHeader, self.nodeParams.clock)
        # Post-test conditions
        assert(nodeStatus[0].present == False)
        assert(nodeStatus[0].lastMsgRcvdTime < self.nodeParams.clock.getTime())

    def test_processHeader(self):
        """Test processHeader method."""
        # Test that node status and command history updated
        nodeStatus = [NodeState(node+1) for node in range(5)]
        assert(processHeader(self.comm, testCmds[NodeCmds['NoOp']].header['header'], testCmds[NodeCmds['NoOp']].serialize(), nodeStatus, self.nodeParams.clock, self.comm) == True)
        assert((testCmds[NodeCmds['NoOp']].header['header']['cmdCounter'] in self.nodeParams.cmdHistory) == True)
        sourceId = testCmds[NodeCmds['NoOp']].header['header']['sourceId']
        assert(math.fabs(nodeStatus[sourceId-1].lastMsgRcvdTime - self.nodeParams.clock.getTime()) <= 0.1)

        # Test for stale command counter indication
        assert(processHeader(self.comm, testCmds[NodeCmds['NoOp']].header['header'], testCmds[NodeCmds['NoOp']].serialize(), nodeStatus, self.nodeParams.clock, self.comm) == False)
         
         
    #def updateCmdCounterValue(self, newCounter, header, body):
        #header['header']['cmdCounter'] = newCounter
        #return header, packHeader(header) + body
        
