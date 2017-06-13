from mesh.generic.commandMsg import CommandMsg
from mesh.generic.command import Command
from mesh.generic.cmds import NodeCmds, PixhawkCmds, TDMACmds
from mesh.generic.cmdDict import CmdDict
from struct import calcsize
from mesh.generic.nodeHeader import headers
from unittests.testCmds import testCmds

cmdsToTest = [NodeCmds['GCSCmd'], NodeCmds['ConfigRequest'], NodeCmds['ParamUpdate'], PixhawkCmds['FormationCmd'], 
PixhawkCmds['NodeStateUpdate'], PixhawkCmds['PosCmd'], PixhawkCmds['StateUpdate'], PixhawkCmds['TargetUpdate'], 
TDMACmds['MeshStatus'], TDMACmds['TimeOffset'], TDMACmds['TimeOffsetSummary']]
class TestCmdDict:
    """Tests all command dictionaries."""   
    def setup_method(self, method):
        self.cmdId = NodeCmds['GCSCmd'] # test command
        self.cmdData = {'cmd': CommandMsg(self.cmdId, [5, 3])}
        self.header = [NodeCmds['GCSCmd'], 0, 10] # NodeHeader
        pass        

    def test_init(self):
        """Test creation of Command instance."""
        # Test creation without header
        command = Command(self.cmdId, self.cmdData)
        assert(command.cmdId == self.cmdId)
        assert(command.cmdData == self.cmdData)

        # Test creation with header
        command = Command(self.cmdId, self.cmdData, self.header)
        assert(isinstance(command.header, dict) == True) # header created as dict
        assert(len(command.header['header']) == len(self.header)) # header has same number of entries as provided header data

    def test_serialize(self):
        """Test serialization of all NodeCmds."""
        for cmdId in cmdsToTest:
            print("Testing serializing:", cmdId)
            serMsg = CmdDict[cmdId].serialize(testCmds[cmdId].cmdData, 0)
            print(testCmds[cmdId].body,serMsg)
            assert(serMsg == testCmds[cmdId].body) # check that output matches truth command
            
