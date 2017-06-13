from switch import switch
from mesh.generic.cmds import TDMACmds
from mesh.generic.cmdDict import CmdDict
from struct import unpack, calcsize
from mesh.generic.nodeHeader import headers
from mesh.generic.deserialize import deserialize
from mesh.generic.cmdProcessor import checkCmdCounter, updateNodeMsgRcvdStatus
from mesh.generic.tdmaState import TDMABlockTxStatus
from mesh.generic.command import Command

# Processor method
def processMsg(self, cmdId, msg, args):
        nodeStatus = args['nodeStatus'] 
        comm = args['comm']
        clock = args['clock']
        
        if len(msg) > 0:
            # Parse command header
            header = deserialize(msg, cmdId, 'header')
            if header != None:
                updateNodeMsgRcvdStatus(nodeStatus, header, clock)
                # Check for command counter
                cmdStatus = checkCmdCounter(self, header, msg, comm)
                if cmdStatus == False: # old command counter
                    return
            
            # Parse message contents
            if cmdId not in [TDMACmds['TimeOffsetSummary'], TDMACmds['BlockData'], TDMACmds['LinkStatus'], TDMACmds['LinkStatusSummary']]:
                try: 
                    msgContents = deserialize(msg, cmdId, 'body')       
                    if msgContents == None:
                        return
                except KeyError:
                    print("Invalid command ID.")
                    return
            
            # Process message by command id
            for case in switch(cmdId):
                if case(TDMACmds['TimeOffset']):
                    if nodeStatus:
                        nodeStatus[header['sourceId']-1].timeOffset = msgContents['timeOffset']/100.0
                    break
                    
                if case(TDMACmds['MeshStatus']):
                    if self.nodeParams.commStartTime == []: # accept value if one not already present
                        self.nodeParams.commStartTime = msgContents['commStartTimeSec'] # store comm start time

                    break

                if case(TDMACmds['TimeOffsetSummary']): # Compiled table of time offsets from all nodes
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

                if case(TDMACmds['LinkStatus']): # Status of links to other nodes
                    msgSize = self.nodeParams.config.maxNumNodes
                    headerSize = calcsize(headers[CmdDict[cmdId].header]['format'])
                    linkData = unpack('=' + msgSize*CmdDict['LinkStatusContents'].packFormat, msg[headerSize:])
       
                    # Determine sending node array index
                    node =  header['sourceId'] - 1

                    # Place received data into appropriate link status subarray
                    for i in range(msgSize):
                       self.nodeParams.linkStatus[node][i] = linkData[i]
                    break

                if case(TDMACmds['LinkStatusSummary']): # Complete table of links between nodes
                    msgSize = self.nodeParams.config.maxNumNodes
                    headerSize = calcsize(headers[CmdDict[cmdId].header]['format'])
                    linkTable = unpack('=' + msgSize*msgSize*CmdDict['LinkStatusSummaryContents'].packFormat, msg[headerSize:])
                    # Place received data into link status array
                    for i in range(msgSize):
                        for j in range(msgSize):
                            self.nodeParams.linkStatus[i][j] = linkTable[i*msgSize + j]
                    break
                if case(TDMACmds['BlockTxRequest']): # Request for a block of transmit time
                    blockTxResponse = False
                    if comm.blockTxStatus['status'] == TDMABlockTxStatus.false: # no current block tx active
                        # Check block transmit constraints
                        if validateBlockTxRequest(msgContents, header, self.nodeParams):        
                            # Store pending request parameters
                            comm.blockTxStatus['blockReqID'] = msgContents['blockReqID']
                            comm.blockTxStatus['status'] = TDMABlockTxStatus.pending # set to pending status and wait for start
                            comm.blockTxStatus['startTime'] = msgContents['startTime'] # store time of request
                            comm.blockTxStatus['txNode'] = header['sourceId'] # store requesting node's ID
                            comm.blockTxStatus['length'] = msgContents['length'] # transmit block length

                            blockTxResponse = True # set response to request

                    elif comm.blockTxStatus['status'] == TDMABlockTxStatus.pending:
                        if comm.blockTxStatus['blockReqID'] == msgContents['blockReqId'] and header['sourceId'] == comm.blockTxStatus['txNode']: # repeat positive response
                            blockTxResponse = True  
                            
                    # Send response
                    responseCmd = Command(TDMACmds['BlockTxRequestResponse'], {'blockReqID': msgContents['blockReqID'], 'accept': blockTxResponse}, [TDMACmds['BlockTxRequestResponse'], self.nodeParams.config.nodeId, self.nodeParams.get_cmdCounter()])
                    comm.radio.bufferTxMsg(responseCmd.serialize(self.nodeParams.clock.getTime()))
            
                    break           

                if case(TDMACmds['BlockTxConfirmed']): # Transmit block confirmation
                    if comm.blockTxStatus['status'] == TDMABlockTxStatus.pending: # pending block transmit
                        if comm.blockTxStatus['blockReqID'] == msgContents['blockReqID'] and comm.blockTxStatus['txNode'] == header['sourceId']: # confirmation received correct node with correct block ID
                            comm.blockTxStatus['status'] = TDMABlockTxStatus.confirmed              
                    break        

                if case(TDMACmds['BlockTxRequestResponse']): 
                    if comm.blockTxStatus['status'] == TDMABlockTxStatus.pending and comm.blockTxStatus['txNode'] == self.nodeParams.config.nodeId: # Block Tx previously requested by this node
                        if header['sourceId'] in comm.blockTxStatus['blockResponseList']: # this node in response list
                            comm.blockTxStatus['blockResponseList'][header['sourceId']] = msgContents['accept']
                    break

                if case(TDMACmds['BlockTxStatus']):
                    updateStatus = False
                    if comm.blockTxStatus['status'] == TDMABlockTxStatus.false: # receiving node not aware of block transmit    
                        updateStatus = True
                        
                    elif comm.blockTxStatus['status'] == TDMABlockTxStatus.pending:
                        if msgContents['blockReqID'] == comm.blockTxStatus['blockReqID']: # may have missed confirm message
                            updateStatus = True

                    if updateStatus:
                        # Update block transmit status
                        comm.blockTxStatus['blockReqID'] = msgContents['blockReqID']
                        comm.blockTxStatus['status'] = TDMABlockTxStatus.confirmed # jump to confirmed status
                        comm.blockTxStatus['startTime'] = msgContents['startTime'] # store time of request
                        comm.blockTxStatus['txNode'] = header['sourceId'] # store requesting node's ID
                        comm.blockTxStatus['length'] = msgContents['length'] # transmit block length

                    break

                if case(TDMACmds['BlockData']): # raw block data
                    headerSize = calcsize(headers[CmdDict[cmdId].header]['format'])
                    blockData = msg[headerSize:]
                    print("Block data received:", blockData)
                    
                    

def validateBlockTxRequest(msgContents, header, nodeParams):
    """Check for valid block transmit request."""
    if msgContents['startTime'] < int(nodeParams.clock.getTime()): # start time elapsed 
        return False
    elif msgContents['length'] > nodeParams.config.commConfig['maxTxBlockSize']: # block too large
        return False
    else:
        return True


# TDMA command processor
TDMACmdProcessor = {'cmdList': TDMACmds, 'msgProcessor': processMsg}
