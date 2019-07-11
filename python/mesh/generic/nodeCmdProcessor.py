from struct import calcsize
from switch import switch
from mesh.generic.cmds import NodeCmds
from mesh.generic.deserialize import deserialize, unpackBytes
from mesh.generic.cmdProcessor import processHeader
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeHeader import headers
from mesh.generic.nodeConfig import ParamId

# Processor method
def processMsg(self, cmdId, header, msg, args):
        nodeStatus = args['nodeStatus']
        comm = args['comm']
        clock = args['clock']
    
        cmdStatus = False
    
        # Deserialize message contents
        try:
            msgContents = deserialize(msg, cmdId, 'body')
                        
            if msgContents == None:
                return False
        except Exception as e:
            print("Exception occurred while deserializing message:", e)
            return False
            
        # Process message by command id
        for case in switch(cmdId):
            if case(NodeCmds['NoOp']): 
                self.cmdQueue[cmdId] = None # place dummy command into queue
                cmdStatus = True
                break
    
            if case(NodeCmds['GCSCmd']): # Queue command for processing
                self.cmdQueue[cmdId] = msgContents
                cmdStatus = True
                break
       
            if case(NodeCmds['CmdResponse']): # Add command response to buffer

                # Add command response to queue
                self.nodeParams.addCmdResponse(msgContents['cmdCounter'], msgContents['cmdResponse'], header['sourceId'])
                cmdStatus = True
                break
 
            if case(NodeCmds['ParamUpdate']): 
                if (msgContents['destId'] == self.nodeParams.config.nodeId):
                    # Unpack and update new parameter value
                    paramStart = calcsize(headers[CmdDict[cmdId].header]['format']) + calcsize(CmdDict[cmdId].packFormat)
                    cmdStatus = unpackParameter(msgContents['paramId'], msgContents['dataLength'], msg[paramStart:], self.nodeParams)
                    
                break

            if case(NodeCmds['ConfigRequest']):
                if (len(msgContents['configHash']) != self.nodeParams.config.hashSize): # invalid config hash
                    print("Config hash in request is invalid length:", str(len(msgContents['configHash'])))
                    break
                    
                #configHash = msg[calcsize(headers[CmdDict[cmdId].header]['format']):]
                configHash = self.nodeParams.config.calculateHash()
                if configHash == msgContents['configHash']:
                    self.nodeParams.configConfirmed = True
                else:
                    self.nodeParams.configConfirmed = False    
                
                #self.cmdQueue[NodeCmds['ConfigRequest']] = msgContents
                cmdStatus = True
                break   

        return cmdStatus
            
def unpackParameter(paramId, dataLength, msg, nodeParams):
    for case in switch(paramId):
        if case(ParamId.nodeId):
            if (dataLength == 1):
                value = unpackBytes('=B', msg)[0][0]
                return nodeParams.config.updateParameter(paramId, value)
            break
        if case(ParamId.parseMsgMax):
            if (dataLength == 2):
                value = unpackBytes('=H', msg)[0][0]
                return nodeParams.config.updateParameter(paramId, value)
            break
        else:
            return False
        
# Node command processor
NodeCmdProcessor = {'cmdList': NodeCmds, 'msgProcessor': processMsg}
