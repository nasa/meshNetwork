from struct import pack
from switch import switch

SLIP_END = pack('B',192)
SLIP_ESC = pack('B',219)
SLIP_END_TDMA = pack('B', 193)
SLIP_ESC_END = pack('B',220)
SLIP_ESC_ESC = pack('B',221)        
SLIP_ESC_END_TDMA = pack('B',222)

class SLIPmsg:
    """An implementation of the Serial Line Internet Protocol (SLIP).
    
    SLIP messages provide a structure for serial messages with special byte values that define the beginning and end of serial messages.  These values allow for easily parsing individual serial messages from raw serial bytes.

    Attributes:
        msg: Decoded SLIP message with SLIP characters removed.
        msgFound: Boolean flag to indicate whether a SLIP message has been found in the provided raw serial byte data.
        msgMaxLength: Maximum length of valid SLIP messages.
        msgEnd: Location of end of SLIP message found in provided raw serial data array. 
        msgLength: Length of SLIP message.
        slip: Encoded SLIP message for transmission.

    """

    def __init__(self, maxLength):
        self.msgMaxLength = maxLength
        self.msgFound = False   
        self.msgEnd = -1
        self.msgLength = 0
        self.msg = b''
        self.slip = b''
    
    def decodeSLIPmsg(self, byteList, msgStart):
        """Searches provided raw serial bytes to locate any SLIP messages.
        
        Args:
            byteList: Raw serial byte array.
            msgStart: Array location to begin searching for SLIP messages in raw serial data.
        """
        # Check for existing partial message
        if self.msgFound and self.msgEnd != -1: # Discard results and restart search
            # Reset message parameters
            self.msg = b''
            self.msgLength = 0
            self.msgFound = False
            self.msgEnd = -1
        for i in range(msgStart, len(byteList)):
            byte = byteList[i:i+1]
            if self.msgFound and self.msgEnd == -1: # existing partial message
                pos = i
                self.decodeSLIPmsgContents(byteList, pos)
                break # exit loop to process message search results 
            if byte == SLIP_END: # message start found
                self.msgFound = True
                pos = i + 1
                self.decodeSLIPmsgContents(byteList, pos)
                break
    
    def decodeSLIPmsgContents(self, byteList, pos):
        """Helper function to strip special SLIP bytes from identified SLIP message.

        Args:
            byteList: Raw serial data array.
            pos: Array position of start of SLIP message in raw serial data.
        """ 
        while pos < len(byteList) and len(self.msg) < self.msgMaxLength:
            byte = byteList[pos:pos+1]
            if byte != SLIP_END: # parse msg contents
                if byte == SLIP_ESC and (pos + 1) < len(byteList): # SLIP ESC character found (second condition guards against overflowing msg buffer)
                    byte = byteList[pos+1:pos+2]
                    if byte == SLIP_ESC_END: # replace ESC sequence with END character
                        self.msg = self.msg + SLIP_END
                    elif byte == SLIP_ESC_END_TDMA: # replace ESC sequence with TDMA END character
                        self.msg = self.msg + SLIP_END_TDMA
                    else: # replace ESC sequence with ESC character
                        self.msg = self.msg + SLIP_ESC
                    pos += 1
                else: # insert raw SLIP msg byte into buffer
                    self.msg = self.msg + byte

                self.msgLength += 1
            else: # message end found
                if(self.msgLength > 0): # guards against falsely identifying a message of zero length between two END characters
                    self.msgEnd = pos
                    break
                #return msgBuffer

            pos += 1


    def encodeSLIPmsg(self, byteList):
        """Encodes provided serial data into a SLIP message.

        Args:
            byteList: Serial bytes to be encoded into SLIP message.
        """
        if not byteList: # Check for empty msg
            return

        self.slip = b''
        self.slip += SLIP_END
        for i in range(len(byteList)):
            byte = byteList[i:i+1]
            if byte == SLIP_END: # Replace END character
                self.slip += SLIP_ESC + SLIP_ESC_END
            elif byte == SLIP_ESC: # Replace ESC character
                self.slip += SLIP_ESC + SLIP_ESC_ESC
            elif byte == SLIP_END_TDMA: # Replace TDMA END character
                self.slip += SLIP_ESC + SLIP_ESC_END_TDMA
            else: # Insert raw byte into message
                self.slip += byte
        self.slip += SLIP_END

