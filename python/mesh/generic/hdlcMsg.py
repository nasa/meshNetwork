from struct import pack
from mesh.generic.utilities import packData
import crcmod

HDLC_END = pack('=B', 0x7E)
HDLC_ESC = pack('=B', 0x7D)
HDLC_END_TDMA = pack('<B', 222)
HDLC_END_SHIFTED = pack('<B', 0x7E ^ (1 << 5))
HDLC_ESC_SHIFTED = pack('<B', 0x7D ^ (1 << 5))
HDLC_END_TDMA_SHIFTED = pack('<B', 222 ^ (1 << 5))

class HDLCMsg:
    """An implementation of High-level Data Link Control (HDLC).
    
    HDLC messages provide a structure for serial messages with special byte values that define the beginning and end of serial messages.  These values allow for easily parsing individual serial messages from raw serial bytes.

    Attributes:
        msg: Decoded HDLC message with HDLC characters removed.
        msgFound: Boolean flag to indicate whether an HDLC message has been found in the provided raw serial byte data.
        msgMaxLength: Maximum length of valid HDLC messages.
        msgEnd: Location of end of HDLC message found in provided raw serial data array. 
        msgLength: Length of HDLC message.
        encoded: Encoded HDLC message for transmission.

    """

    def __init__(self, maxLength):
        self.msgMaxLength = maxLength
        self.msgFound = False   
        self.msgEnd = -1
        self.msgLength = 0
        self.msg = b''
        self.encoded = b''
        self.buffer = b''   
        self.crc = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, xorOut=0, rev=False) # CRC-16
        self.crcLength = 2
 
    def parseMsg(self, msgBytes, msgStart):
        if len(msgBytes) > 0:
            # Process serial message
            self.decodeMsg(msgBytes,msgStart)
        
            if self.msgFound == True: # Message start found
                if self.msgEnd != -1: # entire msg found
                    # Check msg CRC
                    crc = self.crc(self.msg[:-self.crcLength])
                    if self.msg[-self.crcLength:] == packData(crc, self.crcLength): # CRC matches - valid message
                        #print("CRC matches")
                        return self.msg[:-self.crcLength]
                    
        return [] # no message found  
                    
    def encodeMsg(self, inputMsg):
        """Encodes provided serial data into an HDLC message.

        Args:
            inputMsg: Serial bytes to be encoded into HDLC message.
        """
        
        if not inputMsg: # Check for empty msg
            return
        
        # Create crc
        crc = self.crc(inputMsg)
        inputMsg = inputMsg + packData(crc, self.crcLength)
 
        outMsg = bytearray() 
        outMsg += HDLC_END # start message
    
        for i in range(len(inputMsg)):
            byte = inputMsg[i:i+1]
            if (byte == HDLC_END): # Replace END character
                outMsg += HDLC_ESC
                outMsg += HDLC_END_SHIFTED
            elif (byte == HDLC_ESC): # Replace ESC character
                outMsg += HDLC_ESC
                outMsg += HDLC_ESC_SHIFTED
            elif (byte == HDLC_END_TDMA): # Replace TDMA END character
                outMsg += HDLC_ESC
                outMsg += HDLC_END_TDMA_SHIFTED
            else: # Insert raw message byte
                outMsg += byte
    
        outMsg += HDLC_END # end message
    
        self.encoded = outMsg

    def decodeMsg(self, byteList, msgStart=0):
        """Searches provided raw serial bytes to locate any HDLC messages.
        
        Args:
            byteList: Raw serial byte array.
            msgStart: Array location to begin searching for HDLC messages in raw serial data.
        """
        # Check for existing partial message
        if (self.msgFound):
            if (self.msgEnd != -1): # Discard results and restart search
                # Reset message parameters
                self.msg = b''
                self.msgLength = 0
                self.msgFound = False
                self.msgEnd = -1
                self.buffer = b''
            else: # continue parsing partial message
                # Look for buffer contents
                if (self.buffer):
                    byteList = self.buffer + byteList
                    self.buffer = b''
                self.decodeMsgContents(byteList, msgStart)
                return

        # Parse bytes
        for i in range(msgStart, len(byteList)):
            byte = byteList[i:i+1]
            if byte == HDLC_END: # message start found
                self.msgFound = True
                pos = i + 1
                self.decodeMsgContents(byteList, pos)
                break
    
    def decodeMsgContents(self, rawBytes, msgPos):
        """Helper function to strip special HDLC bytes from identified HDLC message.

        Args:
            byteList: Raw serial data array.
            pos: Array position of start of HDLC message in raw serial data.
        """

        while msgPos < len(rawBytes) and len(self.msg) < self.msgMaxLength: # iterate over message bytes
        #for i in range(msgPos, len(rawBytes)):
            byte = rawBytes[msgPos:msgPos+1]
            if byte != HDLC_END: # continue parsing message contents 
                #for j in range(currentPos + 1, len(rawBytes)):
                if (byte == HDLC_ESC): # escape sequence found
                    if ((msgPos + 1) < len(rawBytes)): # bytes available to parse
                        if (rawBytes[msgPos+1:msgPos+2] == HDLC_END_SHIFTED):
                            self.msg += HDLC_END
                        elif (rawBytes[msgPos+1:msgPos+2] == HDLC_END_TDMA_SHIFTED):
                            self.msg += HDLC_END_TDMA
                        else: # ESC byte
                            self.msg += HDLC_ESC
                             
                        msgPos += 2 # update current read position by 2 bytes read
                        self.msgLength += 1
                    else: # not enough bytes
                        # Exit and wait for remaining message bytes
                        self.buffer += byte
                        break
                else: # insert raw message byte
                    self.msg += byte
                    msgPos += 1
                    self.msgLength += 1
                 
        
            else: # end of message found
                if (self.msgLength > 0): # guards against finding messages of zero length between 2 END characters
                    self.msgEnd = msgPos
                    return True
                else: # no message
                    return False
            
