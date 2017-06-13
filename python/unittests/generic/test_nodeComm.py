import serial, time
from mesh.generic.nodeParams import NodeParams
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.radio import Radio
from mesh.generic.slipMsgParser import SLIPMsgParser
from uav.pixhawkCmdProcessor import PixhawkCmdProcessor
from mesh.generic.nodeComm import NodeComm
from mesh.generic.cmds import PixhawkCmds
from mesh.generic.nodeHeader import packHeader
from mesh.generic.nodeState import NodeState
from mesh.generic.formationClock import FormationClock
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath
from unittests.testConfig import testSerialPort

class TestNodeComm:
    
    def setup_method(self, method):
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        commProcessor = CommProcessor([PixhawkCmdProcessor], self.nodeParams)
        radio = Radio(self.serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        self.nodeComm = NodeComm(commProcessor, radio, msgParser, self.nodeParams)
        pass        
    
    def test_processMsgs(self):
        """Test processMsgs method of NodeComm."""
        # Create messages
        cmdId1 = PixhawkCmds['FormationCmd']
        cmdMsg1 = packHeader(testCmds[cmdId1].header) + testCmds[cmdId1].body
        cmdId2 = PixhawkCmds['GCSCmd']
        testCmds[cmdId2].header['header']['sourceId'] = self.nodeParams.config.gcsNodeId # reset source Id to 0 so that command will be accepted
        cmdMsg2 = packHeader(testCmds[cmdId2].header) + testCmds[cmdId2].body
        self.nodeParams.config.nodeId       
        # Send messages
        self.nodeComm.sendMsg(cmdMsg1)  
        self.nodeComm.sendMsg(cmdMsg2)
        time.sleep(0.1) 

        # Process messages
        nodeStatus = [NodeState(node+1) for node in range(5)]
        clock = FormationClock()
        self.nodeComm.processMsgs(args = {'logFile': [], 'nav': [], 'nodeStatus': nodeStatus, 'clock': clock, 'comm': self.nodeComm})
        print(self.nodeComm.commProcessor.cmdQueue)
        assert(cmdId1 in self.nodeComm.commProcessor.cmdQueue) # Test that correct message added to cmdQueue    
        assert(cmdId2 in self.nodeComm.commProcessor.cmdQueue) # Test that correct message added to cmdQueue    
        
