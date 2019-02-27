from struct import pack
from mesh.generic.slipMsg import SLIPMsg, SLIP_END, SLIP_ESC, SLIP_END_TDMA, SLIP_ESC_END, SLIP_ESC_ESC, SLIP_ESC_END_TDMA

testMsg = pack('BBB',1,2,3) + SLIP_END + SLIP_ESC + SLIP_END_TDMA + SLIP_ESC_END + SLIP_ESC_ESC + SLIP_ESC_END_TDMA + pack('BBB',4,5,6)
truthSLIPMsg = SLIP_END + pack('BBB',1,2,3) + SLIP_ESC + SLIP_ESC_END + SLIP_ESC + SLIP_ESC_ESC + SLIP_ESC + SLIP_ESC_END_TDMA + SLIP_ESC_END + SLIP_ESC_ESC + SLIP_ESC_END_TDMA + pack('BBB',4,5,6) + SLIP_END

class TestSLIPMsg:
    
    def setup_method(self, method):
        self.slipMsg = SLIPMsg(256)
        pass        
    
    def test_encodeMsg(self):
        """Test encodeMsg method of SLIPMsg."""
        self.slipMsg.encodeMsg(testMsg)
        assert(self.slipMsg.slip == truthSLIPMsg)
        pass    
    
    def test_decodeMsg(self):
        """Test decodeMsg method of SLIPMsg. Will also test decodeMsgContents."""
        # Test clearing of partial message
        self.slipMsg = SLIPMsg(256)
        self.slipMsg.msgFound = True
        self.slipMsg.msg = b'123'
        self.slipMsg.msgEnd = 5
        self.slipMsg.msgLength = 10
        self.slipMsg.decodeMsg(b'12345', 0)
        assert(self.slipMsg.msgFound == False)
        assert(self.slipMsg.msg == b'')
        assert(self.slipMsg.msgLength == 0)
        assert(self.slipMsg.msgEnd == -1)

        # Test decoding entire message contents
        self.slipMsg = SLIPMsg(256)
        self.slipMsg.encodeMsg(testMsg)
        assert(self.slipMsg.msgEnd == -1)
        self.slipMsg.decodeMsg(self.slipMsg.slip, 0)
        assert(self.slipMsg.msg == testMsg) # verify message contents
        assert(self.slipMsg.msgLength == len(testMsg)) # verify message length
        assert(self.slipMsg.msgEnd == len(truthSLIPMsg)-1) # verify message end location

        # Test decoding partial message
        self.slipMsg = SLIPMsg(256)
        self.slipMsg.encodeMsg(testMsg)
        self.slipMsg.decodeMsg(self.slipMsg.slip[:-1], 0)
        assert(self.slipMsg.msgEnd == -1) # message end not found
        self.slipMsg.decodeMsg(self.slipMsg.slip[-1:], 0) # parse remaining message
        assert(self.slipMsg.msg == testMsg) # verify message contents
        assert(self.slipMsg.msgLength == len(testMsg)) # verify message length

        # Test decoding partial message in middle of escape sequence
        self.slipMsg = SLIPMsg(256)
        msg = b'123' + SLIP_ESC + b'456'
        self.slipMsg.encodeMsg(msg)
        self.slipMsg.decodeMsg(self.slipMsg.slip[0:4], 0) # length prior to escape sequence
        msgLen = self.slipMsg.msgLength
        self.slipMsg.decodeMsg(self.slipMsg.slip[4:5],0) # parse SLIP_ESC
        assert(msgLen == self.slipMsg.msgLength) # message length should be unchanged until entire escape sequence read
        self.slipMsg.decodeMsg(self.slipMsg.slip[5:6], 0) # read entire escape sequence
        assert(self.slipMsg.msgLength == msgLen + 1)
        self.slipMsg.decodeMsg(self.slipMsg.slip[6:], 0) # test successful parsing of remainder of message
        assert(self.slipMsg.msg == msg) # verify message contents
        assert(self.slipMsg.msgLength == len(msg)) # verify message length


#testMsg = pack('BBB',1,2,3) + SLIP_END + SLIP_ESC + SLIP_END_TDMA + SLIP_ESC_END + SLIP_ESC_ESC + SLIP_ESC_END_TDMA + pack('BBB',4,5,6)
#        testMsg 
