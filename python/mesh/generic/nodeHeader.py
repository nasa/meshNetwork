from struct import pack

headers = {'NodeHeader': {'format': '=BBI', 'entries': ['cmdId', 'sourceId', 'cmdCounter']}, \
    'MinimalHeader': {'format': '=B', 'entries': ['cmdId']}, \
    'SourceHeader': {'format': '=BB', 'entries': ['cmdId', 'sourceId']}}

def createHeader(headerIn=[]):
    if not headerIn or isinstance(headerIn, list) == False:
        # Invalid input
        return []
    header = []
    header = dict()
    
    # Check for valid header type
    if headerIn[0] not in headers:
        # Invalid header type
        return []
    header['type'] = headerIn[0]

    if len(headerIn) == 2: # header contents provided so parse header
        headerData = headerIn[1]
        header['header'] = dict()
        for i in range(len(headers[header['type']]['entries'])):
            header['header'][headers[header['type']]['entries'][i]] = headerData[i]

        #if header['type'] == 'NodeHeader':
        #   header.update({'header': {'cmdId': headerData[0], 'sourceId': headerData[1], 'cmdCounter': headerData[2]}}) 
        #elif header['type'] == 'SourceHeader':
        #   header.update({'header': {'cmdId': headerData[0], 'sourceId': headerData[1]}})
        #elif header['type'] == 'MinimalHeader':
        #   header.update({'header': {'cmdId': headerData[0]}})
    return header

def packHeader(header):
    if header['type'] in headers: # Pack header
        return pack(headers[header['type']]['format'], *[header['header'][entry] for entry in headers[header['type']]['entries']])
    else: # No header defined
        return None

        
