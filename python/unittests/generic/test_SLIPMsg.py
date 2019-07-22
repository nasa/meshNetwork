from struct import pack
from mesh.generic.slipMsg import SLIPMsg, SLIP_END, SLIP_ESC, SLIP_ESC_END, SLIP_ESC_ESC
from mesh.generic.utilities import packData

testMsg = pack('BBB',1,2,3) + SLIP_END + SLIP_ESC + SLIP_ESC_END + SLIP_ESC_ESC + pack('BBB',4,5,6)
truthSLIPMsg = SLIP_END + pack('BBB',1,2,3) + SLIP_ESC + SLIP_ESC_END + SLIP_ESC + SLIP_ESC_ESC + SLIP_ESC_END + SLIP_ESC_ESC + pack('BBB',4,5,6) + SLIP_END

class TestSLIPMsg:
    
    def setup_method(self, method):
        self.slipMsg = SLIPMsg(256)
        self.truthCRC = packData(self.slipMsg.crc(testMsg), self.slipMsg.crcLength)
        pass        
    
    def test_encodeMsg(self):
        """Test encodeMsg method of SLIPMsg."""
        self.slipMsg.encodeMsg(testMsg)
        minLength = len(truthSLIPMsg + self.truthCRC)
        assert(len(self.slipMsg.encoded) >= minLength) # length should be at least length of encoded raw bytes plus crc (could be longer if CRC included reserved bytes)
        if (len(self.slipMsg.encoded) == minLength): # no reserved bytes in CRC
            assert(self.slipMsg.encoded == truthSLIPMsg[:-1] + self.truthCRC + truthSLIPMsg[-1:])
        else: # CRC contained reserved bytes:
            assert(self.slipMsg.encoded[:-(self.slipMsg.crcLength+1)] == truthSLIPMsg[:-1]) # skip over CRC
        assert(self.slipMsg.encoded[-1] == truthSLIPMsg[-1])
    
    def test_parseMsg(self):
        """Test parseMsg method of SLIPMsg."""
        
        self.slipMsg.encodeMsg(testMsg) # encode messaging for parsing
        
        # Parse message from encoded message
        parsedMsg = self.slipMsg.parseMsg(self.slipMsg.encoded, 0)
        assert(parsedMsg == testMsg)

        # Parse message with surrounding bytes
        inputMsg = b'9876' + self.slipMsg.encoded + b'1234'
        parsedMsg = self.slipMsg.parseMsg(inputMsg, 0)
        assert(parsedMsg == testMsg)
        
        # Parse partial message    
        self.slipMsg = SLIPMsg(256)
        self.slipMsg.encodeMsg(testMsg)
        self.slipMsg.parseMsg(self.slipMsg.encoded[:-1], 0)
        assert(self.slipMsg.msgEnd == -1) # message end not found
        parsedMsg = self.slipMsg.parseMsg(self.slipMsg.encoded[-1:], 0) # parse remaining message
        assert(parsedMsg == testMsg) # verify message contents
        assert(len(parsedMsg) == len(testMsg)) # verify message length
        
        # Test parsing partial message in middle of escape sequence
        self.slipMsg = SLIPMsg(256)
        msg = b'123' + SLIP_ESC + b'456'
        self.slipMsg.encodeMsg(msg)
        self.slipMsg.parseMsg(self.slipMsg.encoded[0:4], 0) # length prior to escape sequence
        msgLen = self.slipMsg.msgLength
        self.slipMsg.parseMsg(self.slipMsg.encoded[4:5],0) # parse SLIP_ESC
        assert(msgLen == self.slipMsg.msgLength) # message length should be unchanged until entire escape sequence read
        self.slipMsg.parseMsg(self.slipMsg.encoded[5:6], 0) # read entire escape sequence
        assert(self.slipMsg.msgLength == msgLen + 1)
        parsedMsg = self.slipMsg.parseMsg(self.slipMsg.encoded[6:], 0) # test successful parsing of remainder of message
        assert(parsedMsg == msg) # verify message contents
        assert(len(parsedMsg) == len(msg)) # verify message length

