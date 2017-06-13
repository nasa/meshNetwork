import crcmod.predefined # crc
from mesh.generic.msgParser import MsgParser
from mesh.generic.slipMsg import SLIPmsg
from struct import pack

class SLIPMsgParser(MsgParser):
    """This class is responsible for taking raw serial bytes and searching them for valid SLIP messages.

    Attributes:
        crc16: 16-bit CRC calculator.
        slipMsg: Parsed SLIP message with SLIP bytes extracted.
        parsedMsg: Valid serial message stored in this variable upon confirmation of valid CRC.
    """

    def __init__(self, config):
        MsgParser.__init__(self, config)

        self.crc16 = crcmod.predefined.mkCrcFun('crc16')
        self.slipMsg = SLIPmsg(256)

    def parseSerialMsg(self, msgBytes, msgStart):
        """Searches raw serial data for SLIP messages and then validates message integrity by comparing a computed CRC to the CRC found in the message.  Valid messages are then stored for processing.
        
        Args:
            msgBytes: Raw serial data to be parsed.
            msgStart: Start location to begin looking for serial message in msgBytes data array.
        """
        if len(msgBytes) > 0:
            # Process serial message
            self.slipMsg.decodeSLIPmsg(msgBytes,msgStart)
            if self.slipMsg.msgFound == True: # Message start found
                if self.slipMsg.msgEnd != -1: # entire msg found
                    # Check msg CRC
                    crc = self.crc16(self.slipMsg.msg[:-2])
                    if self.slipMsg.msg[-2:] == pack('H',crc): # CRC matches - valid message
                        #print("CRC matches")
                        self.parsedMsgs.append(self.slipMsg.msg[:-2])
                    return self.slipMsg.msgEnd  
                                
                else: # partial msg found
                    pass
            
            else: # No message found
                pass
            
            return len(msgBytes) # all bytes parsed so return length of input message

                
        else:
            return 0


    def encodeMsg(self, msgBytes):
        if msgBytes: # Add CRC
            crc = self.crc16(msgBytes)
            msgBytes = msgBytes + pack('H',crc)
            self.slipMsg.encodeSLIPmsg(msgBytes)
            return self.slipMsg.slip

        return msgBytes 
