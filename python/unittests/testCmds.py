import time
import struct
from collections import namedtuple
from mesh.generic.tdmaState import TDMAStatus
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeConfig import ParamId
from mesh.generic.cmds import NodeCmds, TDMACmds, GndCmds
from mesh.generic.commandMsg import CommandMsg
from mesh.generic.command import Command
from mesh.generic.nodeHeader import createHeader
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeState import NodeState, LinkStatus
from unittests.testConfig import configFilePath

nodeParams = NodeParams(configFile=configFilePath)

# TestCmd type
TestCmd = namedtuple('TestCmd', ['cmdData', 'body', 'header'])

# Node configuration    
nodeId = 1
cmdCounter = 11 

# Test commands dictionary
testCmds = dict()



### NodeCmds
# NodeCmds['NoOp']
cmdId = NodeCmds['NoOp']
cmdData = {}
cmd = Command(cmdId, cmdData, [cmdId, nodeId, nodeParams.get_cmdCounter()])
testCmds.update({cmdId: cmd})

# NodeCmds['GCSCmd']
cmdId = NodeCmds['GCSCmd']
cmdData = {'destId': 0, 'mode': 1}
cmd = Command(cmdId, cmdData, [cmdId, 0, nodeParams.get_cmdCounter()])
testCmds.update({cmdId: cmd})

# NodeCmds['ConfigRequest']
cmdId = NodeCmds['ConfigRequest']
cmdData = {'configHash': nodeParams.config.calculateHash()}
cmd = Command(cmdId, cmdData, [cmdId, 0, nodeParams.get_cmdCounter()])
testCmds.update({cmdId: cmd})

# NodeCmds['ParamUpdate']
cmdId = NodeCmds['ParamUpdate']
cmdData = {'destId': nodeParams.config.nodeId, 'paramId': ParamId.parseMsgMax, 'dataLength': 2, 'paramValue': struct.pack('=H', 500)}
cmd = Command(cmdId, cmdData, [cmdId, nodeId, nodeParams.get_cmdCounter()])
testCmds.update({cmdId: cmd})

### TDMACmds
# TDMACmds['MeshStatus']
cmdId = TDMACmds['MeshStatus']
cmdData = {'commStartTimeSec': int(time.time()), 'status': TDMAStatus.nominal}
cmd = Command(cmdId, cmdData, [cmdId, nodeId])
testCmds.update({cmdId: cmd})

# TDMACmds['TimeOffset']
cmdId = TDMACmds['TimeOffset']
nodeState = NodeState(1)
nodeState.timeOffset = 0.40
cmdData = {'nodeStatus': nodeState}
cmd = Command(cmdId, cmdData, [cmdId, nodeId])
testCmds.update({cmdId: cmd})

# TDMACmds['LinkStatus']
cmdId = TDMACmds['LinkStatus']
linkStatus = [[LinkStatus.NoLink for i in range(nodeParams.config.maxNumNodes)] for j in range(nodeParams.config.maxNumNodes)]
linkStatus[nodeId-1] = [LinkStatus.IndirectLink]*nodeParams.config.maxNumNodes
cmdData = {'linkStatus': linkStatus, 'nodeId': 1}
cmd = Command(cmdId, cmdData, [cmdId, nodeId])
testCmds.update({cmdId: cmd})

### GndCmds
# GndCmds['TimeOffsetSummary']
cmdId = GndCmds['TimeOffsetSummary']
nodeStatus = [NodeState(i) for i in range(2)]
nodeStatus[0].timeOffset = 0.40
nodeStatus[1].timeOffset = 0.50
cmdData = {'nodeStatus': nodeStatus}
cmd = Command(cmdId, cmdData, [cmdId])
testCmds.update({cmdId: cmd})

# GndCmds['LinkStatusSummary']
cmdId = GndCmds['LinkStatusSummary']
linkStatus = [[LinkStatus.NoLink for i in range(nodeParams.config.maxNumNodes)] for j in range(nodeParams.config.maxNumNodes)]
linkStatus[nodeId-1] = [LinkStatus.IndirectLink]*nodeParams.config.maxNumNodes
cmdData = {'linkStatus': linkStatus, 'nodeId': 1}
cmd = Command(cmdId, cmdData, [cmdId, nodeId])
testCmds.update({cmdId: cmd})

