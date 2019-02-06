from struct import pack
from mesh.generic.commandType import CommandType
from mesh.generic.cmds import NodeCmds
from mesh.generic.tdmaCmdDict import TDMACmdDict
from mesh.generic.gndCmdDict import GndCmdDict
#from mesh.generic.testCmdDict import TestCmdDict

# Serialize methods
def serialize_NodeCmds_GCSCmd(cmdData, timestamp):
    """Method for serializing NodeCmds['GCSCmd'] command for serial transmission."""
    #gcsCmd = cmdData['cmd']
    return pack(NodeCmdDict[NodeCmds['GCSCmd']].packFormat, cmdData['destId'], cmdData['mode']) 

def serialize_NodeCmds_ConfigRequest(cmdData, timestamp):
    """Method for serializing NodeCmds['GCSConfigRequest'] command for serial transmission."""
    configHash = cmdData['configHash']
    #msgBytes = pack(NodeCmdDict[NodeCmds['ConfigRequest']].packFormat, NodeCmds['ConfigRequest'], cmdData['nodeId'])
    #return msgBytes + configHash
    return configHash   

def serialize_NodeCmds_ParamUpdate(cmdData, timestamp):
    """Method for serializing NodeCmds['ParamUpdate'] command for serial transmission."""
    paramValue = cmdData['paramValue'] # already converted for transmission
    msgBytes = pack(NodeCmdDict[NodeCmds['ParamUpdate']].packFormat, cmdData['destId'], cmdData['paramId'], cmdData['dataLength'])
    return msgBytes + paramValue

NodeCmdDict = {NodeCmds['NoOp']: CommandType('', [], [], header='NodeHeader'), \
       NodeCmds['GCSCmd']: CommandType('=BB', serialize_NodeCmds_GCSCmd, ['destId', 'mode'], header='NodeHeader'), \
       NodeCmds['ConfigRequest']: CommandType('', serialize_NodeCmds_ConfigRequest, [], header='NodeHeader'), \
       NodeCmds['ParamUpdate']: CommandType('=BBB', serialize_NodeCmds_ParamUpdate, ['destId', 'paramId', 'dataLength'], header='NodeHeader')}

CmdDict = dict()
CmdDict.update(NodeCmdDict)
CmdDict.update(TDMACmdDict)
CmdDict.update(GndCmdDict)
#CmdDict.update(TestCmdDict)
