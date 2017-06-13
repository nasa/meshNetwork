from mesh.generic.commandMsg import CommandMsg
from mesh.generic.command import Command
from mesh.generic.cmds import NodeCmds
from mesh.generic.cmdDict import CmdDict
from struct import calcsize
from mesh.generic.nodeHeader import headers

class TestCommand:
    
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
        """Test serialization of command."""
        command = Command(self.cmdId, self.cmdData, self.header)
        
        serMsg = command.serialize(0)
        assert(len(serMsg) == (calcsize(headers[CmdDict[self.cmdId].header]['format']) + calcsize(CmdDict[self.cmdId].packFormat))) # serial message the correct length
            
