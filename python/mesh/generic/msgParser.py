
class MsgParser:
    """This class is responsible for taking raw serial bytes and searching them for valid SLIP messages.

    Attributes:
        parsedMsgs: Valid serial messages stored in this variable upon confirmation of valid CRC.
        parseMsgMax: Maximum attempts at parsing messages from the raw receive buffer.
    """

    def __init__(self, config):
        self.parsedMsgs = []
        self.parseMsgMax = config['parseMsgMax']

    # Parsing methods
    def parseSerialMsg(self, msgBytes, msgStart):
        """Default parsing just stores all bytes received."""
        if len(msgBytes) > 0:
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
        """Default encoding is none."""
        return msg

