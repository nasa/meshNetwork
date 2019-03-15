import crcmod.predefined
from mesh.generic.slipMsg import SLIPMsg
from struct import pack

def createEncodedMsg(msg):
    """Create encoded SLIP message with CRC."""
    crc16 = crcmod.predefined.mkCrcFun('crc16')
    crc = crc16(msg)
    slipMsg = SLIPMsg(256)
    slipMsg.encodeSLIPmsg(msg + pack('H',crc))
    return slipMsg.slip
