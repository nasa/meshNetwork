from struct import calcsize
from mesh.generic.gndCmdProcessor import GndCmdProcessor
from mesh.generic.cmds import GndCmds
from mesh.generic.command import Command
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeState import NodeState
from mesh.generic.nodeHeader import packHeader, headers
from mesh.generic.radio import Radio
from mesh.generic.serialComm import SerialComm
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath

cmdsToTest = [GndCmds['TimeOffsetSummary'], GndCmds['LinkStatusSummary']]

class TestGndCmdProcessor:
    
    def setup_method(self, method):
        self.nodeStatus = [NodeState(i+1) for i in range(5)]
        self.nodeParams = NodeParams(configFile=configFilePath)
        radio = Radio([], {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        self.comm = SerialComm([GndCmdProcessor], self.nodeParams, radio, [])
    
    def test_processMsg(self):
        """Test processMsg method of GndCmdProcessor."""
    
        # Test processing of all GndCmds
        for cmdId in cmdsToTest:    
            self.comm.processMsg(testCmds[cmdId].serialize(), args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
            if cmdId == GndCmds['TimeOffsetSummary']:
                for i in range(len(testCmds[cmdId].cmdData['nodeStatus'])):
                    assert(self.nodeStatus[i].timeOffset == testCmds[cmdId].cmdData['nodeStatus'][i].timeOffset) # offset pulled from summary message and stored   
            elif cmdId == GndCmds['LinkStatusSummary']:
                msgNodeId = testCmds[cmdId].cmdData['nodeId']
                for i in range(0, self.nodeParams.config.maxNumNodes):
                    for j in range(0, self.nodeParams.config.maxNumNodes):
                        assert(self.nodeParams.linkStatus[i][i] == testCmds[cmdId].cmdData['linkStatus'][i][j])
