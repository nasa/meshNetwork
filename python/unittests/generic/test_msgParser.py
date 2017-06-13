from mesh.generic.msgParser import MsgParser
from struct import pack

class TestMsgParser:
    
    def setup_method(self, method):
        # Create SerialMsgParser instance
        self.msgParser = MsgParser({'parseMsgMax': 10})
    
    def test_parseSerialMsg(self):
        """Test parseSerialMsg method of MsgParser."""
        msg = b'12345'
        msgStart = 1
        self.msgParser.parseSerialMsg(msg, msgStart)
        assert(len(self.msgParser.parsedMsgs) == 1)
        assert(self.msgParser.parsedMsgs[0] == msg[msgStart:])

    def test_encodeMsg(self):
        """Test encode passthrough of message."""
        msg = b'12345'
        assert(self.msgParser.encodeMsg(msg) == msg)

    def test_parseMsgs(self):
        """Test parseMsgs method of MsgParser."""
        msg = b'12345'
        msg = b'12345'
        msg2 = b'6789'
        self.msgParser.parseMsgs(msg)
        self.msgParser.parseMsgs(msg2)
        assert(len(self.msgParser.parsedMsgs) == 2)
        assert(self.msgParser.parsedMsgs[0] == msg)
        assert(self.msgParser.parsedMsgs[1] == msg2)
        
