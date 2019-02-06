from struct import unpack, calcsize
from mesh.generic.nodeCmdProcessor import NodeCmdProcessor
from mesh.generic.cmds import NodeCmds
from mesh.generic.command import Command
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeParams import NodeParams
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.radio import Radio
from mesh.generic.nodeState import NodeState
from mesh.generic.tdmaComm import SerialComm
from mesh.generic.nodeHeader import packHeader, headers, createHeader
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath

cmdsToTest = [NodeCmds['NoOp'], NodeCmds['GCSCmd'], NodeCmds['ParamUpdate'], NodeCmds['ConfigRequest']]

class TestNodeCmdProcessor:
    
    def setup_method(self, method):
        self.nodeStatus = [NodeState(i+1) for i in range(5)]
        self.nodeParams = NodeParams(configFile=configFilePath)
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        radio = Radio([], {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        self.comm = SerialComm([NodeCmdProcessor], self.nodeParams, radio, msgParser)
    
    def test_processMsg(self):
        """Test processMsg method of NodeCmdProcessor."""
    
        # Test processing of all NodeCmds
        for cmdId in cmdsToTest:    
            cmdMsg = testCmds[cmdId].serialize()
            assert(self.comm.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
            if cmdId == NodeCmds['NoOp']:
                pass
            elif cmdId == NodeCmds['ParamUpdate']:
                assert(self.nodeParams.config.parseMsgMax == unpack('=H', testCmds[cmdId].cmdData['paramValue'])[0])   

    def test_malformedCmd(self):
        # Test command with improper message contents
        badMsg = packHeader(createHeader([CmdDict[NodeCmds['GCSCmd']].header, [NodeCmds['GCSCmd'], 0, self.nodeParams.get_cmdCounter()]])) # header only
        assert(self.comm.processMsg(badMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == False)
