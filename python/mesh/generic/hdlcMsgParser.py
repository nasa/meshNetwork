#import crcmod.predefined # crc
import crcmod
from mesh.generic.msgParser import MsgParser
from mesh.generic.hdlcMsg import HDLCMsg
from mesh.generic.utilities import packData

class HDLCMsgParser(MsgParser):
    """This class is responsible for taking raw serial bytes and searching them for valid SLIP messages.

    Attributes:
        crc: CRC calculator.
        msg: Parsed HDLC message with HDLC bytes extracted.
    """

    def __init__(self, config):
        MsgParser.__init__(self, config)

        self.crc = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, xorOut=0, rev=False) # CRC-16
        self.crcLength = 2
        self.msg = HDLCMsg(2058)

    def parseSerialMsg(self, msgBytes, msgStart):
        """Searches raw serial data for HDLC messages and then validates message integrity by comparing a computed CRC to the CRC found in the message.  Valid messages are then stored for processing.
        
        Args:
            msgBytes: Raw serial data to be parsed.
            msgStart: Start location to begin looking for serial message in msgBytes data array.
        """
        if len(msgBytes) > 0:
            # Process serial message
            self.msg.decodeMsg(msgBytes,msgStart)
            if self.msg.msgFound == True: # Message start found
                if self.msg.msgEnd != -1: # entire msg found
                    # Check msg CRC
                    crc = self.crc(self.msg.msg[:-self.crcLength])
                    if self.msg.msg[-self.crcLength:] == packData(crc, self.crcLength): # CRC matches - valid message
                        #print("CRC matches")
                        self.parsedMsgs.append(self.msg.msg[:-self.crcLength])
                    return self.msg.msgEnd  
                                
                else: # partial msg found
                    pass
            
            else: # No message found
                pass
            
            return len(msgBytes) # all bytes parsed so return length of input message

                
        else:
            return 0


    def encodeMsg(self, msgBytes):
        if msgBytes: # Add CRC
            crc = self.crc(msgBytes)
            msgBytes = msgBytes + packData(crc, self.crcLength)
            self.msg.encodeMsg(msgBytes)
            return self.msg.hdlc

        return msgBytes 
