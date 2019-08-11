from mesh.generic.cmds import TDMACmds
from mesh.generic.commandType import CommandType
from struct import pack
from mesh.generic.nodeHeader import headers
from mesh.generic.nodeConfig import configHashSize

# Serialize methods
    
def serialize_TDMACmds_MeshStatus(cmdData, timestamp):
    return pack(TDMACmdDict[TDMACmds['MeshStatus']].packFormat, cmdData['commStartTimeSec'], cmdData['status'], cmdData['configHash'])

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

def serialize_TDMACmds_CurrentConfig(cmdData, timestamp):
    msgBytes = pack(TDMACmdDict[TDMACmds['CurrentConfig']].packFormat, cmdData['configLength'], cmdData['hashLength'])
    return msgBytes + cmdData['config'] + cmdData['configHash']

def serialize_TDMACmds_ConfigUpdate(cmdData, timestamp):
    """Method for serializing NodeCmds['ConfigUpdate'] command for serial transmission."""
    msgBytes = pack(TDMACmdDict[TDMACmds['ConfigUpdate']].packFormat, cmdData['destId'], cmdData['configLength'], cmdData['hashLength'])
    return msgBytes + cmdData['config'] + cmdData['configHash']
       
def serialize_TDMACmds_NetworkRestart(cmdData, timestamp):
    msgBytes = pack(TDMACmdDict[TDMACmds['NetworkRestart']].packFormat, cmdData['destId'], cmdData['restartTime'])
    return msgBytes

def serialize_TDMACmds_BlockTxRequest(cmdData, timestamp):
    # Block transmit request command (includes transfer session ID, start time for block transfer, length of block transfer, and a status byte (1 to start, 0 to end))
    return pack(TDMACmdDict[TDMACmds['BlockTxRequest']].packFormat, cmdData['blockReqId'], cmdData['destId'], cmdData['startTime'], cmdData['length'], cmdData['status'])

def serialize_TDMACmds_BlockTxPacketReceipt(cmdData, timestamp):
    # Confirmation of block transmit packet receipt
    return pack(TDMACmdDict[TDMACmds['BlockTxPacketReceipt']].packFormat, cmdData['blockReqId'], cmdData['packetNum'])

def serialize_TDMACmds_BlockTxStatus(cmdData, timestamp):
    # Block transmit status message sent by receiving nodes (includes block transfer session ID and transfer statistics)
    return pack(TDMACmdDict[TDMACmds['BlockTxStatus']].packFormat, cmdData['blockReqId'], cmdData['numPacketsRcvd'])

def serialize_TDMACmds_BlockData(cmdData, timestamp):
    # Block transmit data block message to send block data (includes transfer ID, sequential transfer packet number, data length, and raw data)
    msgBytes = pack(TDMACmdDict[TDMACmds['BlockData']].packFormat, cmdData['blockReqId'], cmdData['packetNum'], cmdData['dataLength'])
    return msgBytes + cmdData['data']

TDMACmdDict = {TDMACmds['MeshStatus']: CommandType('=IB' + str(configHashSize) + 's', serialize_TDMACmds_MeshStatus, ['commStartTimeSec', 'status', 'configHash'], header='SourceHeader'), \
       TDMACmds['TimeOffset']: CommandType('=H', serialize_TDMACmds_TimeOffset, ['timeOffset'], header='SourceHeader'), \
       TDMACmds['TimeOffsetSummary']: CommandType('', serialize_TDMACmds_TimeOffsetSummary, ['numNodes'], header='MinimalHeader'), \
       'TimeOffsetSummaryContents': CommandType('=H', [], ['offset'], None), \
       TDMACmds['LinkStatus']: CommandType('', serialize_TDMACmds_LinkStatus, [], header='SourceHeader'), \
       'LinkStatusContents': CommandType('B', [], ['linkStatus'], None), \
       TDMACmds['LinkStatusSummary']: CommandType('', serialize_TDMACmds_LinkStatusSummary, [], header='MinimalHeader'), \
       'LinkStatusSummaryContents': CommandType('=B', [], ['linkStatus'], None), \
       TDMACmds['CurrentConfig']: CommandType('<BB', serialize_TDMACmds_CurrentConfig, ['configLength', 'hashLength'], header='SourceHeader'), \
       TDMACmds['ConfigUpdate']: CommandType('=BHB', serialize_TDMACmds_ConfigUpdate, ['destId', 'configLength', 'hashLength'], header='NodeHeader'), \
       TDMACmds['NetworkRestart']: CommandType('<BI', serialize_TDMACmds_NetworkRestart, ['destId', 'restartTime'], header='NodeHeader'), \
       TDMACmds['BlockTxPacketReceipt']: CommandType('=BH', serialize_TDMACmds_BlockTxPacketReceipt, ['blockReqId', 'packetNum'],  header='SourceHeader'), \
       TDMACmds['BlockTxStatus']: CommandType('=BH', serialize_TDMACmds_BlockTxStatus, ['blockReqId', 'numPacketsRcvd'],  header='NodeHeader'), \
       TDMACmds['BlockTxRequest']: CommandType('=BBIHB', serialize_TDMACmds_BlockTxRequest, ['blockReqId', 'destId', 'startTime', 'length', 'status'],  header='NodeHeader'), \
       TDMACmds['BlockData']: CommandType('=BHH', serialize_TDMACmds_BlockData, ['blockReqId', 'packetNum', 'dataLength'], header='SourceHeader')} 

