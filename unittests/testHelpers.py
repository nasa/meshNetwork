import crcmod.predefined
from mesh.generic.slipMsg import SLIPmsg
from struct import pack

def createEncodedMsg(msg):
    """Create encoded SLIP message with CRC."""
    crc16 = crcmod.predefined.mkCrcFun('crc16')
    crc = crc16(msg)
    slipMsg = SLIPmsg(256)
    slipMsg.encodeSLIPmsg(msg + pack('H',crc))
    return slipMsg.slip
