from mesh.generic.deserialize import deserialize, parseHeader, parseBody
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeHeader import packHeader
from mesh.generic.cmds import PixhawkCmds
from unittests.testCmds import testCmds
class TestDeserialize:
    
    def setup_method(self, method):
        # Test command
        self.cmdId = PixhawkCmds['FormationCmd']
        self.command = testCmds[self.cmdId]
        self.headerBytes = packHeader(self.command.header)
        self.msgBytes = self.headerBytes + self.command.body

    def test_parseHeader(self):
        """Test parsing header from serial message bytes."""
        header = parseHeader(self.msgBytes[0:len(self.headerBytes)], self.cmdId)
        self.checkHeaderEntries(header)

    def test_parseBody(self):
        """Test parsing body from serial message bytes."""
        body = parseBody(self.msgBytes[len(self.headerBytes):], self.cmdId)
        self.checkBodyEntries(body)

    def test_deserializeBody(self):
        """Test deserializing body from serial message bytes."""
        body = deserialize(self.msgBytes, self.cmdId, element="body")
        self.checkBodyEntries(body)     

    def test_deserializeHeader(self):
        """Test deserializing header from serial message bytes."""
        header = deserialize(self.msgBytes, self.cmdId, element="header")
        self.checkHeaderEntries(header)

    def test_deserializeMsg(self):
        """Test deserializing entire message from serial message bytes."""
        header, body = deserialize(self.msgBytes, self.cmdId, element="entire")
        self.checkHeaderEntries(header)
        self.checkBodyEntries(body)     
        pass

    def test_deserialize(self):
        """Test serialization of all NodeCmds."""
#       for cmdId in cmdsToTest:
#           print("Testing deserializing body:", cmdId)
#           msg = deserialize(testCmds[cmdId].body, cmdId, 'bodyonly')
#           print(msg)
        #assert(msg == testCmds[cmdId].) # check that output matches truth command
        pass            
    
    def checkBodyEntries(self, body):
        for entry in CmdDict[self.cmdId].messageFormat:
            print("Testing", "\'" + entry + "\'", "in body.")
            assert(entry in body)

    def checkHeaderEntries(self, header):
        assert(header == self.command.header['header'])

