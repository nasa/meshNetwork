from struct import pack
from mesh.generic.hdlcMsg import HDLCMsg, HDLC_END, HDLC_ESC, HDLC_END_SHIFTED, HDLC_ESC_SHIFTED

testMsg = pack('BBB',1,2,3) + HDLC_END + HDLC_ESC + pack('BBB',4,5,6)
truthHDLCMsg = HDLC_END + pack('BBB',1,2,3) + HDLC_ESC + HDLC_END_SHIFTED + HDLC_ESC + HDLC_ESC_SHIFTED + pack('BBB',4,5,6) + HDLC_END

class TestHDLCMsg:
    
    def setup_method(self, method):
        self.hdlcMsg = HDLCMsg(256)
        pass        
    
    def test_encodeMsg(self):
        """Test encodeMsg method of HDLCMsg."""
        self.hdlcMsg.encodeMsg(testMsg)
        assert(self.hdlcMsg.hdlc == truthHDLCMsg)
    
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

        # Test decoding entire message contents
        self.hdlcMsg = HDLCMsg(256)
        self.hdlcMsg.encodeMsg(testMsg)
        assert(self.hdlcMsg.msgEnd == -1)
        self.hdlcMsg.decodeMsg(self.hdlcMsg.hdlc, 0)
        assert(self.hdlcMsg.msg == testMsg) # verify message contents
        assert(self.hdlcMsg.msgLength == len(testMsg)) # verify message length
        assert(self.hdlcMsg.msgEnd == len(truthHDLCMsg)-1) # verify message end location

        # Test decoding partial message
        self.hdlcMsg = HDLCMsg(256)
        self.hdlcMsg.encodeMsg(testMsg)
        self.hdlcMsg.decodeMsg(self.hdlcMsg.hdlc[:-1], 0)
        assert(self.hdlcMsg.msgEnd == -1) # message end not found
        self.hdlcMsg.decodeMsg(self.hdlcMsg.hdlc[-1:], 0) # parse remaining message
        assert(self.hdlcMsg.msg == testMsg) # verify message contents
        assert(self.hdlcMsg.msgLength == len(testMsg)) # verify message length

        # Test decoding partial message in middle of escape sequence
        self.hdlcMsg = HDLCMsg(256)
        msg = b'123' + HDLC_ESC + b'456'
        self.hdlcMsg.encodeMsg(msg)
        self.hdlcMsg.decodeMsg(self.hdlcMsg.hdlc[0:4], 0) # length prior to escape sequence
        msgLen = self.hdlcMsg.msgLength
        self.hdlcMsg.decodeMsg(self.hdlcMsg.hdlc[4:5],0) # parse HDLC_ESC
        assert(msgLen == self.hdlcMsg.msgLength) # message length should be unchanged until entire escape sequence read
        self.hdlcMsg.decodeMsg(self.hdlcMsg.hdlc[5:6], 0) # read entire escape sequence
        assert(self.hdlcMsg.msgLength == msgLen + 1)
        self.hdlcMsg.decodeMsg(self.hdlcMsg.hdlc[6:], 0) # test successful parsing of remainder of message
        assert(self.hdlcMsg.msg == msg) # verify message contents
        assert(self.hdlcMsg.msgLength == len(msg)) # verify message length

