from struct import pack
from mesh.generic.hdlcMsg import HDLCMsg, HDLC_END, HDLC_ESC, HDLC_END_SHIFTED, HDLC_ESC_SHIFTED
from mesh.generic.utilities import packData

testMsg = pack('BBB',1,2,3) + HDLC_END + HDLC_ESC + pack('BBB',4,5,6)
truthHDLCMsg = HDLC_END + pack('BBB',1,2,3) + HDLC_ESC + HDLC_END_SHIFTED + HDLC_ESC + HDLC_ESC_SHIFTED + pack('BBB',4,5,6) + HDLC_END

class TestHDLCMsg:
    
    def setup_method(self, method):
        self.hdlcMsg = HDLCMsg(256)
        self.truthCRC = packData(self.hdlcMsg.crc(testMsg), self.hdlcMsg.crcLength)
        pass        
    
    def test_encodeMsg(self):
        """Test encodeMsg method of HDLCMsg."""
        self.hdlcMsg.encodeMsg(testMsg)
#        assert(self.hdlcMsg.encoded == truthHDLCMsg + self.truthCRC)
        minLength = len(truthHDLCMsg + self.truthCRC)
        assert(len(self.hdlcMsg.encoded) >= minLength) # length should be at least length of encoded raw bytes plus crc (could be longer if CRC included reserved bytes)
        if (len(self.hdlcMsg.encoded) == minLength): # no reserved bytes in CRC
            assert(self.hdlcMsg.encoded == (truthHDLCMsg[:-1] + self.truthCRC + truthHDLCMsg[-1:]))
        else: # CRC contained reserved bytes
            assert(self.hdlcMsg.encoded[:-(self.hdlcMsg.crcLength+1)] == truthHDLCMsg[:-1]) # skip over CRC
            assert(self.hdlcMsg.encoded[-1] == truthHDLCMsg[-1])
    
    def test_decodeMsg(self):
        """Test decodeMsg method of HDLCMsg. Will also test decodeMsgContents."""
        # Test clearing of partial message
        self.hdlcMsg = HDLCMsg(256)
        self.hdlcMsg.msgFound = True
        self.hdlcMsg.msg = b'123'
        self.hdlcMsg.msgEnd = 5
        self.hdlcMsg.msgLength = 10
        self.hdlcMsg.decodeMsg(b'12345', 0)
        assert(self.hdlcMsg.msgFound == False)
        assert(self.hdlcMsg.msg == b'')
        assert(self.hdlcMsg.msgLength == 0)
        assert(self.hdlcMsg.msgEnd == -1)

    def test_parseMsg(self):
        """Test parseMsg method of HLDCMsg."""
        
        self.hdlcMsg.encodeMsg(testMsg) # encode messaging for parsing
        
        # Parse message from encoded message
        parsedMsg = self.hdlcMsg.parseMsg(self.hdlcMsg.encoded, 0)
        assert(parsedMsg == testMsg)

        # Parse message with surrounding bytes
        inputMsg = b'9876' + self.hdlcMsg.encoded + b'1234'
        parsedMsg = self.hdlcMsg.parseMsg(inputMsg, 0)
        assert(parsedMsg == testMsg)
        
        # Parse partial message    
        self.hdlcMsg = HDLCMsg(256)
        self.hdlcMsg.encodeMsg(testMsg)
        self.hdlcMsg.parseMsg(self.hdlcMsg.encoded[:-1], 0)
        assert(self.hdlcMsg.msgEnd == -1) # message end not found
        parsedMsg = self.hdlcMsg.parseMsg(self.hdlcMsg.encoded[-1:], 0) # parse remaining message
        assert(parsedMsg == testMsg) # verify message contents
        assert(len(parsedMsg) == len(testMsg)) # verify message length
        
        # Test parsing partial message in middle of escape sequence
        self.hdlcMsg = HDLCMsg(256)
        msg = b'123' + HDLC_ESC + b'456'
        self.hdlcMsg.encodeMsg(msg)
        self.hdlcMsg.parseMsg(self.hdlcMsg.encoded[0:4], 0) # length prior to escape sequence
        msgLen = self.hdlcMsg.msgLength
        self.hdlcMsg.parseMsg(self.hdlcMsg.encoded[4:5],0) # parse HDLC_ESC
        assert(msgLen == self.hdlcMsg.msgLength) # message length should be unchanged until entire escape sequence read
        self.hdlcMsg.parseMsg(self.hdlcMsg.encoded[5:6], 0) # read entire escape sequence
        assert(self.hdlcMsg.msgLength == msgLen + 1)
        parsedMsg = self.hdlcMsg.parseMsg(self.hdlcMsg.encoded[6:], 0) # test successful parsing of remainder of message
        assert(parsedMsg == msg) # verify message contents
        assert(len(parsedMsg) == len(msg)) # verify message length
