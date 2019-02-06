from mesh.generic.commandMsg import CommandMsg
from mesh.generic.command import Command
from mesh.generic.cmds import NodeCmds, PixhawkCmds, TDMACmds
from mesh.generic.cmdDict import CmdDict
from struct import calcsize
from mesh.generic.nodeHeader import headers
from unittests.testCmds import testCmds

cmdsToTest = [NodeCmds['GCSCmd'], NodeCmds['ConfigRequest'], NodeCmds['ParamUpdate'],  TDMACmds['MeshStatus'], TDMACmds['TimeOffset'], TDMACmds['TimeOffsetSummary']]
class TestCmdDict:
    """Tests all command dictionaries."""   
    def setup_method(self, method):
        pass        

    def test_serialize(self):
        """Test serialization of all NodeCmds."""
        for cmdId in cmdsToTest:
            print("Testing serializing:", cmdId)
            serMsg = CmdDict[cmdId].serialize(testCmds[cmdId].cmdData, 0)
            print(testCmds[cmdId].body,serMsg)
            assert(serMsg == testCmds[cmdId].body) # check that output matches truth command
            
