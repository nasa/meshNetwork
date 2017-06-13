import time
import struct
from collections import namedtuple
from mesh.generic.tdmaState import TDMAStatus
from mesh.generic.cmdDict import CmdDict
from mesh.generic.cmds import NodeCmds, PixhawkCmds, TDMACmds, PixhawkFCCmds
from mesh.generic.commandMsg import CommandMsg
from mesh.generic.navigation import convertLatLonAlt
from mesh.generic.nodeHeader import createHeader
from mesh.generic.nodeParams import NodeParams
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
# NodeCmds['GCSCmd']
cmdId = NodeCmds['GCSCmd']
cmdData = [0, 1]
body = struct.pack(CmdDict[cmdId].packFormat, *cmdData)
header = createHeader([CmdDict[cmdId].header, [cmdId, 0, cmdCounter]])
testCmds.update({cmdId: TestCmd({'cmd': CommandMsg(cmdId, cmdData)}, body, header)})

# NodeCmds['ConfigRequest']
cmdId = NodeCmds['ConfigRequest']
cmdData = nodeParams.config.calculateHash()
header = createHeader([CmdDict[cmdId].header, [cmdId, nodeId, cmdCounter]])
testCmds.update({cmdId: TestCmd({'configHash': cmdData}, cmdData, header)})

# NodeCmds['ParamUpdate']
cmdId = NodeCmds['ParamUpdate']
cmdData = {'paramId': 100, 'paramValue': b'123'}
header = createHeader([CmdDict[cmdId].header, [cmdId, nodeId, cmdCounter]])
body = struct.pack(CmdDict[cmdId].packFormat, cmdData['paramId']) + cmdData['paramValue']
testCmds.update({cmdId: TestCmd(cmdData, body, header)})

### PixhawkCmds
# PixhawkCmds['FormationCmd']
cmdId = PixhawkCmds['FormationCmd']
cmdData = [10, 3, 34.1234567, -86.7654321, 20.0, 0]
msgData = [10, 3] + convertLatLonAlt(cmdData[2:5]) + [0]
body = struct.pack(CmdDict[cmdId].packFormat, *msgData)
header = createHeader([CmdDict[cmdId].header, [cmdId, nodeId]])
testCmds.update({cmdId: TestCmd({'cmd': CommandMsg(cmdId, cmdData)}, body, header)})

# PixhawkCmds['NodeStateUpdate']
from mesh.generic.nodeState import NodeState
from uav.pixhawkNavigation import PixhawkNavigation
cmdId = PixhawkCmds['NodeStateUpdate']
nav = PixhawkNavigation()
nav.state = [34.1234567, -86.7654321, 20.0]
nav.timestamp = 0
nodeStatus = [NodeState(i) for i in range(2)]
nodeStatus[nodeId].state = nav.state
nodeStatus[nodeId].timestamp = nav.timestamp
for i in range(2):
    nodeStatus[i].present = True
    nodeStatus[i].updating = True

# This node
precision = [1000000,1]
state = convertLatLonAlt([nav.state[0], nav.state[1], nav.state[2]], precision=precision)
msgData = [nodeId] + state + [0, nodeStatus[nodeId-1].formationMode, nodeStatus[nodeId-1].status]
body = struct.pack(CmdDict['NodeStateUpdateContents'].packFormat, *msgData)
# Other nodes
msgData[0] = nodeId + 1
body = struct.pack(CmdDict[cmdId].packFormat, 2) + body + struct.pack(CmdDict['NodeStateUpdateContents'].packFormat, *msgData)
header = createHeader([CmdDict[cmdId].header, [cmdId, nodeId]])
testCmds.update({cmdId: TestCmd({'nodeStatus': nodeStatus, 'nodeId': nodeId, 'nav': nav}, body, header)})

# PixhawkCmds['PosCmd']
cmdId = PixhawkCmds['PosCmd']
cmdData = [34.1234567, -86.7654321, 20.0, 3]
msgData = cmdData[3:] + convertLatLonAlt(cmdData[0:3])
body = struct.pack(CmdDict[cmdId].packFormat, *msgData)
header = createHeader([CmdDict[cmdId].header, [cmdId]])
testCmds.update({cmdId: TestCmd({'formationMode': cmdData[3], 'formCmd': cmdData[0:3]}, body, header)})

# PixhawkCmds['StateUpdate']
cmdId = PixhawkCmds['StateUpdate']
cmdData = [34.1234567, -86.7654321, 20.0, 2, 1700, 3456789]
msgData = convertLatLonAlt(cmdData[0:3]) + cmdData[3:]
body = struct.pack(CmdDict[cmdId].packFormat, *msgData)
header = createHeader([CmdDict[cmdId].header, [cmdId]])
testCmds.update({cmdId: TestCmd({'cmd': CommandMsg(cmdId, cmdData)}, body, header)})

# PixhawkCmds['TargetUpdate']
cmdId = PixhawkCmds['TargetUpdate']
cmdData = [34.1234567, -86.7654321, 20.0]
msgData = convertLatLonAlt(cmdData)
body = struct.pack(CmdDict[cmdId].packFormat, *msgData)
header = createHeader([CmdDict[cmdId].header, [cmdId]])
testCmds.update({cmdId: TestCmd({'cmd': CommandMsg(cmdId, cmdData)}, body, header)})

### TDMACmds
# TDMACmds['MeshStatus']
cmdId = TDMACmds['MeshStatus']
cmdData = [int(time.time()), TDMAStatus.nominal]
body = struct.pack(CmdDict[cmdId].packFormat, *cmdData)
header = createHeader([CmdDict[cmdId].header, [cmdId, nodeId]])
testCmds.update({cmdId: TestCmd({'commStartTimeSec': cmdData[0], 'status': TDMAStatus.nominal}, body, header)})

# TDMACmds['TimeOffset']
cmdId = TDMACmds['TimeOffset']
nodeState = NodeState(1)
nodeState.timeOffset = 0.40
body = struct.pack(CmdDict[cmdId].packFormat, int(nodeState.timeOffset*100))
header = createHeader([CmdDict[cmdId].header, [cmdId, nodeId]])
testCmds.update({cmdId: TestCmd({'nodeStatus': nodeState}, body, header)})

# TDMACmds['TimeOffsetSummary']
cmdId = TDMACmds['TimeOffsetSummary']
nodeStatus = [NodeState(i) for i in range(2)]
nodeStatus[0].timeOffset = 0.40
nodeStatus[1].timeOffset = 0.50
body = struct.pack(CmdDict[cmdId].packFormat + 'HH', len(nodeStatus), int(nodeStatus[0].timeOffset*100), int(nodeStatus[1].timeOffset*100))
header = createHeader([CmdDict[cmdId].header, [cmdId]])
testCmds.update({cmdId: TestCmd({'nodeStatus': nodeStatus}, body, header)})

### PixhawkFCCmds
# PixhawkFCCmds['ModeChange']
cmdId = PixhawkFCCmds['ModeChange']
cmdData = [1]
body = struct.pack(CmdDict[cmdId].packFormat, *cmdData)
header = createHeader([CmdDict[cmdId].header, [cmdId]])
testCmds.update({cmdId: TestCmd({'cmd': CommandMsg(cmdId, cmdData)}, body, header)})

# PixhawkFCCmds['ArmCommand']
cmdId = PixhawkFCCmds['ArmCommand']
cmdData = [1]
body = struct.pack(CmdDict[cmdId].packFormat, *cmdData)
header = createHeader([CmdDict[cmdId].header, [cmdId]])
testCmds.update({cmdId: TestCmd({'cmd': CommandMsg(cmdId, cmdData)}, body, header)})

# PixhawkFCCmds['VehicleStatus']
cmdId = PixhawkFCCmds['VehicleStatus']
cmdData = [1, 0, 34.1234567, -86.7654321, 20.0, 0.5]
state = convertLatLonAlt(cmdData[2:5])
msgData = cmdData[0:2] + state + [int(cmdData[5]*100)]
body = struct.pack(CmdDict[cmdId].packFormat, *msgData)
header = createHeader([CmdDict[cmdId].header, [cmdId]])
testCmds.update({cmdId: TestCmd({'cmd': CommandMsg(cmdId, cmdData)}, body, header)})
