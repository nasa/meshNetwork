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
def processMsg(self, cmdId, header, msg, args):
            nodeStatus = args['nodeStatus'] 
            comm = args['comm']
            clock = args['clock']

            cmdStatus = False
 
            # Parse message contents
            #if cmdId not in [TDMACmds['BlockData'], TDMACmds['LinkStatus']]:
            if cmdId not in [TDMACmds['BlockData']]:
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
                    if not comm.networkConfigConfirmed: # accept value if configuration not yet confirmed
                        comm.commStartTime = msgContents['commStartTimeSec'] # store comm start time
                        comm.networkConfigConfirmed = self.nodeParams.config.calculateHash() == msgContents['configHash'] # compare configurations
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

                if case(TDMACmds['CurrentConfig']): # Current mesh network configuration
                    if ((msgContents['configLength'] + msgContents['hashLength']) == len(msgContents['raw']) and comm.networkConfigConfirmed == False):
                        config = msgContents['raw'][0:msgContents['configLength']]
                        hashValue = msgContents['raw'][msgContents['configLength']:msgContents['configLength'] + msgContents['hashLength']]
                        [cmdStatus, newConfig] = self.nodeParams.loadConfig(config, hashValue)
                        if (cmdStatus == True):
                            self.nodeParams.newConfig = newConfig # stage config for update 
                        print(str(self.nodeParams.config.nodeId) + " - CurrentConfig message received.")
                        
                        comm.networkConfigRcvd = True                    

                    else: # insufficient message bytes
                        break

                    break
                if case(TDMACmds['ConfigUpdate']):
                    #if (msgContents['destId'] in [self.nodeParams.config.nodeId, 0]): # command for this node or global
                        if ((msgContents['configLength'] + msgContents['hashLength']) == len(msgContents['raw'])):
                            config = msgContents['raw'][0:msgContents['configLength']]
                            hashValue = msgContents['raw'][msgContents['configLength']:msgContents['configLength'] + msgContents['hashLength']]

                            # Validate configuration
                            [cmdStatus, config] = self.nodeParams.loadConfig(config, hashValue)

                            # Store command response for transmission
                            #self.nodeParams.cmdResponse.append({'cmdId': NodeCmds['ConfigUpdate'], 'cmdResponse': int(cmdStatus), 'sourceId': header['sourceId']}) 

                            # Add to network message queue for polling
                            print(str(self.nodeParams.config.nodeId) + " - ConfigUpdate message received.")
                            comm.networkMsgQueue.append({"header": header, "msgContents": {'config': config, 'destId': msgContents['destId'], 'valid': cmdStatus}})
                        else: # insufficient message bytes
                            pass
                        break

                if case(TDMACmds['NetworkRestart']): # Network restart command
                    #if (msgContents['destId'] == 0 or msgContents['destId'] == self.nodeParams.config.nodeId): # 
                        if (msgContents['restartTime'] > self.nodeParams.clock.getTime()): # restart time is in the future
                            # Add to network message queue
                            comm.networkMsgQueue.append({"header": header, "msgContents": msgContents})
                            cmdStatus = True
                            
                        #self.nodeParams.cmdResponse.append({'cmdId': TDMACmds['NetworkRestart'], 'cmdCounter': header['cmdCounter'], 'cmdResponse': int(cmdStatus), 'sourceId': header['sourceId']}) 

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
