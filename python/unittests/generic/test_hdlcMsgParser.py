from mesh.generic.msgParser import MsgParser
from mesh.generic.hdlcMsg import HDLCMsg
from test_HDLCMsg import truthHDLCMsg, testMsg
from mesh.generic.utilities import packData

class TestHDLCMsgParser:
    
    def setup_method(self, method):
        # Create HDLCMsgParser instance
        self.msgParser = MsgParser({'parseMsgMax': 10}, HDLCMsg(256))
    
    def test_parseSerialMsg(self):
        """Test parseSerialMessage method of HDLCMsgParser."""
        # Check rejection of message with invalid CRC
        self.msgParser.parseSerialMsg(truthHDLCMsg, 0)
        assert(self.msgParser.msg.msgFound == True) # hdlc msg found
        assert(self.msgParser.msg.msgEnd != 1) # message end found
        assert(self.msgParser.parsedMsgs == []) # message rejected      

        # Check acceptance of message with valid CRC    
        crc = self.msgParser.msg.crc(testMsg)
        hdlcMsg = HDLCMsg(256)
        hdlcMsg.encodeMsg(testMsg)
        self.msgParser.parseSerialMsg(hdlcMsg.encoded, 0)
        assert(self.msgParser.msg.msgFound == True) # hdlc msg found
        assert(self.msgParser.msg.msgEnd != 1) # message end found
        assert(self.msgParser.parsedMsgs[0] == testMsg) # message accepted  
        
        # Check that proper message end position is returned
        self.msgParser.parsedMsgs = []
        paddedMsg = hdlcMsg.encoded + b'989898'
        msgEnd = self.msgParser.parseSerialMsg(paddedMsg, 0)
        assert(self.msgParser.parsedMsgs[0] == testMsg)
        assert(msgEnd == len(hdlcMsg.encoded)-1)
        
    def test_encodeMsg(self):
        """Test encodeMsg method of HDLCMsgParser."""
        hdlcMsg = HDLCMsg(256)
        hdlcMsg.encodeMsg(testMsg)
        encodedMsg = self.msgParser.encodeMsg(testMsg)
        assert(encodedMsg == hdlcMsg.encoded)
