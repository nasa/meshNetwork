from mesh.generic.cmds import GndCmds
from mesh.generic.commandType import CommandType
from struct import pack
from mesh.generic.nodeHeader import headers

# Serialize methods
    
def serialize_GndCmds_TimeOffsetSummary(cmdData, timestamp):
    nodeStatus = cmdData['nodeStatus']

    # Assemble message
    msg = pack(GndCmdDict[GndCmds['TimeOffsetSummary']].packFormat, len(nodeStatus))
    packFormat = GndCmdDict['TimeOffsetSummaryContents'].packFormat
    for status in nodeStatus:
        msg += pack(packFormat, int(status.timeOffset*100))

    return msg  

def serialize_GndCmds_LinkStatusSummary(cmdData, timestamp):
    linkStatus = cmdData['linkStatus']
    
    # Assemble message
    msg = bytearray()
    for i in range(len(linkStatus)):
        for j in range(len(linkStatus[i])):
            msg += pack('=' + GndCmdDict['LinkStatusSummaryContents'].packFormat, int(linkStatus[i][j]))

    return msg  

GndCmdDict = {GndCmds['TimeOffsetSummary']: CommandType('=B', serialize_GndCmds_TimeOffsetSummary, ['numNodes'], header='MinimalHeader'), \
       'TimeOffsetSummaryContents': CommandType('=H', [], ['offset'], None), \
       GndCmds['LinkStatusSummary']: CommandType('', serialize_GndCmds_LinkStatusSummary, [], header='MinimalHeader'), \
       'LinkStatusSummaryContents': CommandType('B', [], ['linkStatus'], None)}
