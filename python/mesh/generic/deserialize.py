from mesh.generic.nodeHeader import headers
from mesh.generic.cmdDict import CmdDict
from mesh.generic.customExceptions import InsufficientMsgBytes
from struct import calcsize, unpack


def deserialize(msg, cmdId, element='entire'):
    # Deserialize desired msg elements
    try: 
        # Get body properties
        bodyFormat = CmdDict[cmdId].packFormat
        
        # Get header properties
        if CmdDict[cmdId].header:
            headerFormat = headers[CmdDict[cmdId].header]['format']
        else:
            headerFormat = None
        if headerFormat:
            headerSize = calcsize(headerFormat)
        if element == 'header':
            if headerFormat:
                return parseHeader(unpackBytes(headerFormat, msg), cmdId)
            else:
                raise NoCommandHeaderDefined("Command does not define a header.")
        elif element == 'body':
            if headerFormat:
                bodyBytes = msg[headerSize:]
            else:
                bodyBytes = msg
            if bodyFormat:
                return parseBody(unpackBytes(bodyFormat, bodyBytes), cmdId)
            else: # No body format so return raw bytes
                return bodyBytes

        elif element == 'entire':
            header = []
            if headerFormat: # unpack header if present
                header = parseHeader(unpackBytes(headerFormat, msg[0:headerSize]), cmdId)
                msgContents = parseBody(unpackBytes(bodyFormat, msg[headerSize:]), cmdId)
            # Unpack command body
            else:
                msgContents = unpackBytes(bodyFormat, msg)
            return header, msgContents
        #elif element == "bodyonly":
        #   if bodyFormat:
        #       return parseBody(unpack(bodyFormat, msg), cmdId)
            
    except Exception as e:
        print("Exception when deserializing message. CmdId-", cmdId, ", Exception:",e)
        raise    

def unpackBytes2(fmt, msgBytes, returnExcess=False):
    dataSize = calcsize(fmt)
    if (len(msgBytes) >= dataSize):
        unpacked = unpack(fmt, msgBytes[0:dataSize])
        if (returnExcess and len(msgBytes) > dataSize): # return extra bytes
            return [unpacked, msgBytes[dataSize:]]
        else:
            return unpacked
    else: # insufficient bytes
        raise InsufficientMsgBytes("Message format exceeds raw message byte length.")

def unpackBytes(fmt, msgBytes):
    dataSize = calcsize(fmt)
    if (len(msgBytes) >= dataSize):
        return unpack(fmt, msgBytes[0:dataSize])
    else: # insufficient bytes
        raise InsufficientMsgBytes("Message format exceeds raw message byte length.")

def parseHeader(rawHeader, cmdId):
    header = dict()
    if cmdId not in CmdDict:
        return rawHeader
    
    for i in range(len(headers[CmdDict[cmdId].header]['entries'])):
        header[headers[CmdDict[cmdId].header]['entries'][i]] = rawHeader[i]             
    return header
    
def parseBody(rawBody, cmdId):
    body = dict()
    if cmdId not in CmdDict:
        return rawBody
    
    # Parse message contents and create dictionary
    #if (CmdDict[cmdId].packFormat[0] == '='):
    #    packFormat = CmdDict[cmdId].packFormat[1:]
    #else:
    #    packFormat = CmdDict[cmdId].packFormat
    for i in range(len(CmdDict[cmdId].messageFormat)):
        body[CmdDict[cmdId].messageFormat[i]] = rawBody[i]
    
    return body 
