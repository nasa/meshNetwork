import struct
from mesh.generic.radio import Radio
from mesh.generic.slipMsg import SLIP_END
from mesh.generic.cmds import FPGACmds
import crcmod.predefined

class FPGARadio(Radio):

    def __init__(self, serial, config):
        Radio.__init__(self, serial, config)
        
        self.crc16 = crcmod.predefined.mkCrcFun('crc16')
   
    def sendMsg(self, msgBytes):
        """Package message to send to FPGA."""
        #print("outgoing message:", SLIP_END + struct.pack('=BH',FPGACmds['FPGAMsgStart'], len(msgBytes)) + msgBytes + struct.pack("H", self.crc16(msgBytes)))
        self.sendBytes(SLIP_END + struct.pack('=BH',FPGACmds['FPGAMsgStart'], len(msgBytes)) + msgBytes + struct.pack("H", self.crc16(msgBytes)))
         
