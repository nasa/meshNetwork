import pytest
from mesh.generic.deserialize import deserialize, parseHeader, parseBody, unpackBytes
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeHeader import packHeader, headers
from mesh.generic.cmds import NodeCmds
from mesh.generic.customExceptions import InsufficientMsgBytes
from unittests.testCmds import testCmds
from struct import calcsize

class TestDeserialize:
    
    def setup_method(self, method):
        # Test command
        self.cmdId = NodeCmds['GCSCmd']
        self.command = testCmds[self.cmdId]
        self.bodyFormat = CmdDict[self.cmdId].packFormat
        self.headerBytes = self.command.packHeader()
        self.headerFormat = headers[CmdDict[self.cmdId].header]['format']
        self.msgBytes = self.command.serialize()

    def test_unpackBytes(self):
        """Test unpackBytes method."""
        # Test processing of equal size message
        msg = b'12345'
        fmt = '=BBBBB'
        out = unpackBytes(fmt, msg)
        assert(len(out[0]) == calcsize(fmt))
        assert(len(out[1]) == 0) # no excess bytes

        # Test processing of short message
        fmt = '=BBBBBB'
        with pytest.raises(InsufficientMsgBytes) as e:
            out = unpackBytes(fmt, msg)

        # Test processing of long message
        fmt = '=BBBB'
        out = unpackBytes(fmt, msg)
        assert(len(out[0]) == calcsize(fmt))
        assert(out[1] == msg[calcsize(fmt):])

    def test_parseHeader(self):
        """Test parsing header from serial message bytes."""
        headerEntries = unpackBytes(self.headerFormat, self.msgBytes[0:len(self.headerBytes)])
        #header = parseHeader([self.msgBytes[0:len(self.headerBytes)],[]], self.cmdId)
        header = parseHeader(headerEntries, self.cmdId)
        self.checkHeaderEntries(header)

    def test_parseBody(self):
        """Test parsing body from serial message bytes."""
        bodyEntries = unpackBytes(self.bodyFormat, self.msgBytes[len(self.headerBytes):])
        body = parseBody(bodyEntries, self.cmdId)
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

    def checkBodyEntries(self, body):
        for entry in CmdDict[self.cmdId].messageFormat:
            print("Testing", "\'" + entry + "\'", "in body.")
            assert(entry in body)

    def checkHeaderEntries(self, header):
        assert(header == self.command.header['header'])

