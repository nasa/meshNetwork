from mesh.generic.commandMsg import CommandMsg
from mesh.generic.cmds import NodeCmds
from mesh.generic.cmdDict import CmdDict

class TestCommandMsg:
    
    def setup_method(self, method):
        pass        

    def test_parseCommand(self):
        """Test parsing command message contents."""
        # Test parsing message based on cmdId   
        cmdId = NodeCmds['GCSCmd'] # test command
        cmdData = [5, 3]
        msg = CommandMsg(cmdId, cmdData)
        for i in range(len(CmdDict[cmdId].messageFormat)):
            entry = CmdDict[cmdId].messageFormat[i]
            assert(entry in msg.cmdData)
            assert(msg.cmdData[entry] == cmdData[i])
    
        # Test creating message parsing without cmdId
        msg = CommandMsg(cmdData=cmdData)
        assert(msg.cmdData == cmdData)
