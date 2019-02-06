from mesh.generic.cmds import cmdsToRelay
from struct import pack

# Process command header 
def processHeader(self, header, msg, nodeStatus, clock, comm):
    cmdStatus = True
    if header != None:
        updateNodeMsgRcvdStatus(nodeStatus, header, clock)
        
        # Check for command counter
        cmdStatus = checkCmdCounter(self, header, msg, comm)
        
    return cmdStatus
 

# Command counter check
def checkCmdCounter(self, header, msg, comm):
    """Helper function to check command counter."""

    if 'cmdCounter' in list(header.keys()):
        cmdCounterValue = header['cmdCounter']
        #currentCmdCounter = self.nodeParams.get_cmdCounter()
        if cmdCounterValue not in self.nodeParams.cmdHistory: # new command 
        #if cmdCounterValue > currentCmdCounter or (currentCmdCounter == 255 and cmdCounterValue > 0 and cmdCounterValue <= self.nodeParams.cmdCounterThreshold): # new command, second check is for when command counter wraps around 
            self.nodeParams.cmdHistory.append(cmdCounterValue)
            #self.nodeParams.set_cmdCounter(cmdCounterValue)
            if header['cmdId'] in cmdsToRelay:
                if 'cmdRelayBuffer' in comm.__dict__: # command relay buffer
                    print("Relaying:", msg)
                    msgOut = comm.msgParser.encodeMsg(msg)
                    comm.cmdRelayBuffer += msgOut
            return True # new command so process
        else: # old command
            print("Old command. Cmd counter value:", cmdCounterValue)
            return False    
    else:
        return True # no command counter so process command

# Node message received status 
def updateNodeMsgRcvdStatus(nodeStatus, header, clock):
    """Updates the time of the last message received directly from a given node. Also sets presence flag to true if this is the first message from a node.
        
    Args:
        nodeStatus: NodeStatus instance.
        clock: Formation clock.
    """
                
    if 'sourceId' in header and 'cmdId' in header: 
        if header['cmdId'] not in cmdsToRelay: # relayed commands will have sourceId of original sender, not necessarily the direct sender
            # Update message received status for source node
            source = header['sourceId'] - 1
            if nodeStatus[source].present == False:
                nodeStatus[source].present = True # First message received from this node   
            nodeStatus[source].lastMsgRcvdTime = clock.getTime()
