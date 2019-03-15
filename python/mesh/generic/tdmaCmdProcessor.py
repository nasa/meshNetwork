from switch import switch
from mesh.generic.cmds import TDMACmds
from mesh.generic.cmdDict import CmdDict
from struct import unpack, calcsize
from mesh.generic.nodeHeader import headers
from mesh.generic.deserialize import deserialize
from mesh.generic.cmdProcessor import processHeader
from mesh.generic.tdmaState import TDMABlockTxStatus
from mesh.generic.command import Command

# Processor method
def processMsg(self, cmdId, msg, args):
        nodeStatus = args['nodeStatus'] 
        comm = args['comm']
        clock = args['clock']

        cmdStatus = False
 
        if len(msg) > 0:
            # Parse command header
            header = deserialize(msg, cmdId, 'header')
            if (processHeader(self, header, msg, nodeStatus, clock, comm) == False): # stale command
                return False

            # Parse message contents
            if cmdId not in [TDMACmds['BlockData'], TDMACmds['LinkStatus']]:
                try: 
                    msgContents = deserialize(msg, cmdId, 'body')       
                    if msgContents == None:
                        return False
                except Exception as e:
                    print("Exception occurred while deserializing message:", e)
                    return False
            
            # Process message by command id
            for case in switch(cmdId):
                if case(TDMACmds['TimeOffset']):
                    if nodeStatus and len(nodeStatus) >= header['sourceId']:
                        nodeStatus[header['sourceId']-1].timeOffset = msgContents['timeOffset']/100.0
                    cmdStatus = True
                    break
                    
                if case(TDMACmds['MeshStatus']):
                    if not comm.commStartTime: # accept value if one not already present
                        comm.commStartTime = msgContents['commStartTimeSec'] # store comm start time
                    cmdStatus = True

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
                    cmdStatus = True
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
                    
        return cmdStatus                    

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
