from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.slipMsg import SLIPmsg
from test_SLIPmsg import truthSLIPMsg, testMsg
from struct import pack

class TestSLIPMsgParser:
    
    def setup_method(self, method):
        # Create SLIPMsgParser instance
        self.msgParser = SLIPMsgParser({'parseMsgMax': 10})
    
    def test_parseSerialMsg(self):
        """Test parseSerialMessage method of SLIPMsgParser."""
        # Check rejection of message with invalid CRC
        self.msgParser.parseSerialMsg(truthSLIPMsg, 0)
        assert(self.msgParser.slipMsg.msgFound == True) # slip msg found
        assert(self.msgParser.slipMsg.msgEnd != 1) # message end found
        assert(self.msgParser.parsedMsgs == []) # message rejected      

        # Check acceptance of message with valid CRC    
        crc = self.msgParser.crc(testMsg)
        slipMsg = SLIPmsg(256)
        slipMsg.encodeSLIPmsg(testMsg + pack('H',crc)) # re-encode slip with CRC
        self.msgParser.parseSerialMsg(slipMsg.slip, 0)
        assert(self.msgParser.slipMsg.msgFound == True) # slip msg found
        assert(self.msgParser.slipMsg.msgEnd != 1) # message end found
        assert(self.msgParser.parsedMsgs[0] == testMsg) # message rejected  
        
        # Check that proper message end position is returned
        self.msgParser.parsedMsgs = []
        paddedMsg = slipMsg.slip + b'989898'
        msgEnd = self.msgParser.parseSerialMsg(paddedMsg, 0)
        assert(self.msgParser.parsedMsgs[0] == testMsg)
        assert(msgEnd == len(slipMsg.slip)-1)
        
    def test_encodeMsg(self):
        """Test encodeMsg method of SLIPMsgParser."""
        crc = self.msgParser.crc(testMsg)
        slipMsg = SLIPmsg(256)
        slipMsg.encodeSLIPmsg(testMsg + pack('H',crc))
        encodedMsg = self.msgParser.encodeMsg(testMsg)
        assert(encodedMsg == slipMsg.slip)
