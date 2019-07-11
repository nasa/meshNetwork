
class MsgParser:
    """This class is responsible for taking raw serial bytes and searching them for valid SLIP messages.

    Attributes:
        parsedMsgs: Valid serial messages stored in this variable upon confirmation of valid CRC.
        parseMsgMax: Maximum attempts at parsing messages from the raw receive buffer.
    """

    def __init__(self, config, msg=[]):
        self.parsedMsgs = []
        self.parseMsgMax = config['parseMsgMax']
        self.msg = msg
        

    # Parsing methods
    def parseSerialMsg(self, msgBytes, msgStart):
        """Searches raw serial data for messages and then parses them using the specified message format. Valid parsed messages are then stored for processing."""
        if len(msgBytes) > 0:
            if (self.msg): # message format specified
                parsedMsg = self.msg.parseMsg(msgBytes, msgStart)
                if (parsedMsg): # message parsed successfully
                    self.parsedMsgs.append(parsedMsg)
                    return self.msg.msgEnd
            else: # no format so store all received bytes
                self.parsedMsgs.append(msgBytes[msgStart:])
        return len(msgBytes)
    
    def parseMsgs(self, rxBuffer):
        """Parse read serial data."""
        msgEnd = -1
        for loopCtr in range(self.parseMsgMax): # Continuing looping until end of buffer reached or max loop iterations
            if msgEnd < len(rxBuffer): # More bytes in buffer to parse
                msgEnd = self.parseSerialMsg(rxBuffer, msgEnd+1)
            else: # end of buffer reached
                break

        # Message creation methods
    
    def encodeMsg(self, msg):
        if msg: # non-zero length message:
            if self.msg: # Package using message protocol
                self.msg.encodeMsg(msg)
                return self.msg.encoded
            else: # default to returning input bytes
                return msg 
        else: # no message
            return []

