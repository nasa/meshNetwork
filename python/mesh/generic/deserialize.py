from mesh.generic.nodeHeader import headers
from mesh.generic.cmdDict import CmdDict
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
                return parseHeader(unpack(headerFormat, msg[0:headerSize]), cmdId)
            else:
                raise NoCommandHeaderDefined("Command does not define a header.")
        elif element == 'body':
            if headerFormat:
                bodyBytes = msg[headerSize:]
            else:
                bodyBytes = msg
            if bodyFormat:
                return parseBody(unpack(bodyFormat, bodyBytes), cmdId)
            else: # No body format so return raw bytes
                return bodyBytes

        elif element == 'entire':
            header = []
            if headerFormat: # unpack header if present
                header = parseHeader(unpack(headerFormat, msg[0:headerSize]), cmdId)
                msgContents = parseBody(unpack(bodyFormat, msg[headerSize:]), cmdId)
            # Unpack command body
            else:
                msgContents = unpack(bodyFormat, msg)
            return header, msgContents
        #elif element == "bodyonly":
        #   if bodyFormat:
        #       return parseBody(unpack(bodyFormat, msg), cmdId)
            
    except Exception as e:
            print("Exception when deserializing message. CmdId-", cmdId, ", Exception:",e)
            

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
    if (CmdDict[cmdId].packFormat[0] == '='):
        packFormat = CmdDict[cmdId].packFormat[1:]
    else:
        packFormat = CmdDict[cmdId].packFormat
    for i in range(len(packFormat)):
        body[CmdDict[cmdId].messageFormat[i]] = rawBody[i]
    
    return body 
