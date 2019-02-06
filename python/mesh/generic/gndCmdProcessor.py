from switch import switch
from mesh.generic.cmds import GndCmds
from mesh.generic.cmdDict import CmdDict
from struct import unpack, calcsize
from mesh.generic.nodeHeader import headers
from mesh.generic.deserialize import deserialize
from mesh.generic.cmdProcessor import processHeader

# Processor method
def processMsg(self, cmdId, msg, args):
        nodeStatus = args['nodeStatus'] 
        comm = args['comm']
        clock = args['clock']
        
        if len(msg) > 0:
            # Parse command header
            header = deserialize(msg, cmdId, 'header')
            if (processHeader(self, header, msg, nodeStatus, clock, comm) == False): # stale command
                return 

            # Parse message contents
            if cmdId not in [GndCmds['TimeOffsetSummary'], GndCmds['LinkStatusSummary']]:
                try: 
                    msgContents = deserialize(msg, cmdId, 'body')       
                    if msgContents == None:
                        return
                except KeyError:
                    print("Invalid command ID.")
                    return
            
            # Process message by command id
            for case in switch(cmdId):
                if case(GndCmds['TimeOffsetSummary']): # Compiled table of time offsets from all nodes
                    # Calculate header size
                    headerSize = calcsize(headers[CmdDict[cmdId].header]['format'])
                    # Unpack message
                    msgSize = calcsize(CmdDict[cmdId].packFormat)
                    timeOffsetFormatSize = calcsize(CmdDict['TimeOffsetSummaryContents'].packFormat)
                    numNodes = unpack(CmdDict[cmdId].packFormat, msg[headerSize:headerSize + msgSize])[0]
                    if (len(msg) != (numNodes*timeOffsetFormatSize) + headerSize + msgSize):
                        print("Serial message length incorrect length:", str(len(msg)))
                        break
                    
                    for i in range(numNodes): # Extract time offset of all nodes
                        msgContents = deserialize(msg[i*timeOffsetFormatSize + headerSize + msgSize:i*timeOffsetFormatSize+(timeOffsetFormatSize + headerSize + msgSize)], 'TimeOffsetSummaryContents', 'body')
                        if msgContents == None:
                            return
                        nodeStatus[i].timeOffset = msgContents['offset']/100.0
                    break

                if case(GndCmds['LinkStatusSummary']): # Complete table of links between nodes
                    msgSize = self.nodeParams.config.maxNumNodes
                    headerSize = calcsize(headers[CmdDict[cmdId].header]['format'])
                    linkTable = unpack('=' + msgSize*msgSize*CmdDict['LinkStatusSummaryContents'].packFormat, msg[headerSize:])
                    # Place received data into link status array
                    for i in range(msgSize):
                        for j in range(msgSize):
                            self.nodeParams.linkStatus[i][j] = linkTable[i*msgSize + j]
                    break

# Ground command processor
GndCmdProcessor = {'cmdList': GndCmds, 'msgProcessor': processMsg}
