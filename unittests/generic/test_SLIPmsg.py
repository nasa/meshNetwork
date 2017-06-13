from struct import pack
from mesh.generic.slipMsg import SLIPmsg, SLIP_END, SLIP_ESC, SLIP_END_TDMA, SLIP_ESC_END, SLIP_ESC_ESC, SLIP_ESC_END_TDMA

testMsg = pack('BBB',1,2,3) + SLIP_END + SLIP_ESC + SLIP_END_TDMA + SLIP_ESC_END + SLIP_ESC_ESC + SLIP_ESC_END_TDMA + pack('BBB',4,5,6)
truthSLIPMsg = SLIP_END + pack('BBB',1,2,3) + SLIP_ESC + SLIP_ESC_END + SLIP_ESC + SLIP_ESC_ESC + SLIP_ESC + SLIP_ESC_END_TDMA + SLIP_ESC_END + SLIP_ESC_ESC + SLIP_ESC_END_TDMA + pack('BBB',4,5,6) + SLIP_END

class TestSLIPmsg:
    
    def setup_method(self, method):
        self.slipMsg = SLIPmsg(256)
        pass        
    
    def test_encodeSLIPmsg(self):
        """Test encodeSLIPmsg method of SLIPmsg."""
        self.slipMsg.encodeSLIPmsg(testMsg)
        assert(self.slipMsg.slip == truthSLIPMsg)
        pass    
    
    def test_decodeSLIPmsg(self):
        """Test decodeSLIPmsg method of SLIPmsg. Will also test decodeSLIPmsgContents."""
        # Test clearing of partial message
        self.slipMsg = SLIPmsg(256)
        self.slipMsg.msgFound = True
        self.slipMsg.msg = b'123'
        self.slipMsg.msgEnd = 5
        self.slipMsg.msgLength = 10
        self.slipMsg.decodeSLIPmsg(b'12345', 0)
        assert(self.slipMsg.msgFound == False)
        assert(self.slipMsg.msg == b'')
        assert(self.slipMsg.msgLength == 0)
        assert(self.slipMsg.msgEnd == -1)

        # Test decoding entire message contents
        self.slipMsg = SLIPmsg(256)
        self.slipMsg.encodeSLIPmsg(testMsg)
        assert(self.slipMsg.msgEnd == -1)
        self.slipMsg.decodeSLIPmsg(self.slipMsg.slip, 0)
        assert(self.slipMsg.msg == testMsg) # verify message contents
        assert(self.slipMsg.msgLength == len(testMsg)) # verify message length
        assert(self.slipMsg.msgEnd == len(truthSLIPMsg)-1) # verify message end location

        # Test decoding partial message
        self.slipMsg = SLIPmsg(256)
        self.slipMsg.encodeSLIPmsg(testMsg)
        self.slipMsg.decodeSLIPmsg(self.slipMsg.slip[:-5], 0)
        assert(self.slipMsg.msgLength < len(testMsg)) # check that partial message decoded
        assert(self.slipMsg.msgEnd == -1) # message end not found
