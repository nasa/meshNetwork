import struct

def packData(data, length, endianness='little'):
    packFormat = ''

    # Determine endianness for packing
    if (endianness == 'little'):
        packFormat += '<'
    else:
        packFormat += '>'

    # Pack provided data
    try:
        if (length == 1):
            return struct.pack(packFormat + 'B', data)
        elif (length == 2):
            return struct.pack(packFormat + 'H', data) 
        elif (length == 4):
            return struct.pack(packFormat + 'I', data) 
        elif (length == 8):
            return struct.pack(packFormat + 'Q', data) 
    except Exception as e:
        raise e

def unpackData(data, length, endianness='little'):
    packFormat = ''

    # Determine endianness for unpacking
    if (endianness == 'little'):
        packFormat += '<'
    else:
        packFormat += '>'

    # Pack provided data
    try:
        if (length == 1):
            return struct.unpack(packFormat + 'B', data)[0]
        elif (length == 2):
            return struct.unpack(packFormat + 'H', data)[0] 
        elif (length == 4):
            return struct.unpack(packFormat + 'I', data)[0] 
        elif (length == 8):
            return struct.unpack(packFormat + 'Q', data)[0] 
    except Exception as e:
        raise e
    
def truncateFloat(floatIn, numDigits):
    formatStr = '%.' + str(numDigits) + 'f'
    return float(formatStr%(floatIn))

