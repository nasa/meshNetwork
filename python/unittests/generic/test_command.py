from mesh.generic.commandMsg import CommandMsg
from mesh.generic.command import Command
from mesh.generic.cmds import NodeCmds
from mesh.generic.cmdDict import CmdDict
from mesh.generic.customExceptions import CommandIdNotFound
from struct import calcsize
from mesh.generic.nodeHeader import headers, packHeader
import pytest

class TestCommand:
    
    def setup_method(self, method):
        self.cmdId = NodeCmds['GCSCmd'] # test command
        self.cmdData = {'destId': 5, 'mode': 3}
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

        # Test with invalid command Id
        with pytest.raises (CommandIdNotFound) as e:
            command = Command(7000, self.cmdData, self.header)

    def test_packBody(self):
        """Test packBody method of Command class."""
        command = Command(self.cmdId, self.cmdData)

        # Test with serialize method
        body = command.packBody()
        assert(len(body) == calcsize(CmdDict[self.cmdId].packFormat))
        assert(body == CmdDict[self.cmdId].serialize(command.cmdData, 0))

        # Test without serialize method
        command.serializeMethod = []
        body = command.packBody()
        assert(len(body) == 0)

    def test_packHeader(self):
        """Test packHeader method of Command class."""
        command = Command(self.cmdId, self.cmdData, self.header)
       
        # Test with header
        header = command.packHeader()
        assert(header == packHeader(command.header))

        # Test without header
        command.header = []
        header = command.packHeader()
        assert(len(header) == 0)

    def test_serialize(self):
        """Test serialization of command."""
        command = Command(self.cmdId, self.cmdData, self.header)
        
        serMsg = command.serialize(0)
        assert(len(serMsg) == (calcsize(headers[CmdDict[self.cmdId].header]['format']) + calcsize(CmdDict[self.cmdId].packFormat))) # serial message the correct length
            
