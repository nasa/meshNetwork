from mesh.generic.cmds import TDMACmds
from mesh.generic.commandType import CommandType
from struct import pack
from mesh.generic.nodeHeader import headers

# Serialize methods
    
def serialize_TDMACmds_MeshStatus(cmdData, timestamp):
    return pack(TDMACmdDict[TDMACmds['MeshStatus']].packFormat, cmdData['commStartTimeSec'], cmdData['status'])

def serialize_TDMACmds_TimeOffset(cmdData, timestamp):
    return pack(TDMACmdDict[TDMACmds['TimeOffset']].packFormat, int(cmdData['nodeStatus'].timeOffset*100))

def serialize_TDMACmds_TimeOffsetSummary(cmdData, timestamp):
    nodeStatus = cmdData['nodeStatus']

    # Assemble message
    #msg = pack(TDMACmdDict[TDMACmds['TimeOffsetSummary']].packFormat, len(nodeStatus))
    msg = bytearray()
    packFormat = TDMACmdDict['TimeOffsetSummaryContents'].packFormat
    for status in nodeStatus:
        msg += pack(packFormat, int(status.timeOffset*100))

    return msg  

def serialize_TDMACmds_LinkStatus(cmdData, timestamp):
    linkStatus = cmdData['linkStatus']
    nodeId = cmdData['nodeId']
    
    # Pack link status to all nodes
    msg = pack('=' + len(linkStatus)*TDMACmdDict['LinkStatusContents'].packFormat,*linkStatus[nodeId-1])
    
    return msg

def serialize_TDMACmds_LinkStatusSummary(cmdData, timestamp):
    linkStatus = cmdData['linkStatus']
    
    # Assemble message
    msg = bytearray()
    for i in range(len(linkStatus)):
        for j in range(len(linkStatus[i])):
            msg += pack('=' + TDMACmdDict['LinkStatusSummaryContents'].packFormat, int(linkStatus[i][j]))

    return msg  

def serialize_TDMACmds_BlockTxRequest(cmdData, timestamp):
    return pack(TDMACmdDict[TDMACmds['BlockTxRequest']].packFormat, cmdData['blockReqID'], cmdData['startTime'], cmdData['length'])

def serialize_TDMACmds_BlockTxStatus(cmdData, timestamp):
    return pack(TDMACmdDict[TDMACmds['BlockTxStatus']].packFormat, cmdData['blockReqID'], cmdData['startTime'], cmdData['length'])

def serialize_TDMACmds_BlockTxConfirmed(cmdData, timestamp):
    return pack(TDMACmdDict[TDMACmds['BlockTxConfirmed']].packFormat, cmdData['blockReqID'])

def serialize_TDMACmds_BlockTxRequestResponse(cmdData, timestamp):
    return pack(TDMACmdDict[TDMACmds['BlockTxRequestResponse']].packFormat, cmdData['blockReqID'], cmdData['accept'])

def serialize_TDMACmds_BlockData(cmdData, timestamp):
    return cmdData['data']

#TDMACmdDict = {TDMACmds['MeshStatus']: CommandType('=iB', serialize_TDMACmds_MeshStatus, ['commStartTime', 'cmdCounter'], header='MinimalHeader'), \
TDMACmdDict = {TDMACmds['MeshStatus']: CommandType('=IB', serialize_TDMACmds_MeshStatus, ['commStartTimeSec', 'status'], header='SourceHeader'), \
       TDMACmds['TimeOffset']: CommandType('=H', serialize_TDMACmds_TimeOffset, ['timeOffset'], header='SourceHeader'), \
       TDMACmds['TimeOffsetSummary']: CommandType('', serialize_TDMACmds_TimeOffsetSummary, ['numNodes'], header='MinimalHeader'), \
       'TimeOffsetSummaryContents': CommandType('=H', [], ['offset'], None), \
       TDMACmds['LinkStatus']: CommandType('', serialize_TDMACmds_LinkStatus, [], header='SourceHeader'), \
       'LinkStatusContents': CommandType('B', [], ['linkStatus'], None), \
       TDMACmds['LinkStatusSummary']: CommandType('', serialize_TDMACmds_LinkStatusSummary, [], header='MinimalHeader'), \
       'LinkStatusSummaryContents': CommandType('=B', [], ['linkStatus'], None), \
       TDMACmds['BlockTxStatus']: CommandType('=BiB', serialize_TDMACmds_BlockTxStatus, ['blockReqID', 'startTime', 'length'],  header='NodeHeader'), \
       TDMACmds['BlockTxRequest']: CommandType('=BiB', serialize_TDMACmds_BlockTxRequest, ['blockReqID', 'startTime', 'length'],  header='NodeHeader'), \
       TDMACmds['BlockTxConfirmed']: CommandType('=B', serialize_TDMACmds_BlockTxConfirmed, ['blockReqID'], header='NodeHeader'), \
       TDMACmds['BlockTxRequestResponse']: CommandType('=BB', serialize_TDMACmds_BlockTxRequestResponse, ['blockReqID', 'accept'], header='NodeHeader'), \
       TDMACmds['BlockData']: CommandType('', serialize_TDMACmds_BlockData, ['data'], header='SourceHeader')} 

