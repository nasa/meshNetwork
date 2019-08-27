import crcmod.predefined
from mesh.generic.slipMsg import SLIPMsg
from struct import pack

def createEncodedMsg(msg, msgEncoder):
    """Create encoded SLIP message with CRC."""
    crc16 = crcmod.predefined.mkCrcFun('crc16')
    crc = crc16(msg)
    msgEncoder.encodeMsg(msg + pack('H',crc))
    return msgEncoder.encoded
