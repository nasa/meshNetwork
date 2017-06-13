from mesh.generic.commProcessor import CommProcessor
from mesh.generic.nodeParams import NodeParams
from uav.pixhawkCmdProcessor import PixhawkCmdProcessor
from mesh.generic.cmds import PixhawkCmds
from mesh.generic.nodeState import NodeState
from mesh.generic.formationClock import FormationClock
from unittests.testCmds import testCmds
from mesh.generic.nodeHeader import packHeader
from mesh.generic.serialComm import SerialComm
from unittests.testConfig import configFilePath

class TestCommProcessor:
    
    def setup_method(self, method):
        # Create CommProcessor instance
        nodeParams = NodeParams(configFile=configFilePath)
        self.commProcessor = CommProcessor([PixhawkCmdProcessor], nodeParams)
        self.serialComm = SerialComm([], [], nodeParams.config)

        # Truth data
        self.crcLength = 2

    def test_processMsg(self):
        """Test that valid message is processed."""
        
        nodeStatus = [NodeState(node+1) for node in range(5)]
        clock = FormationClock()
        
        cmdId = PixhawkCmds['FormationCmd']
        cmdMsg = packHeader(testCmds[cmdId].header) + testCmds[cmdId].body
        self.commProcessor.processMsg(cmdMsg, args = {'logFile': [], 'nav': [], 'nodeStatus': nodeStatus, 'clock': clock, 'comm': self.serialComm})

        assert(cmdId in self.commProcessor.cmdQueue) # Test that correct message added to cmdQueue  
