from enum import IntEnum
from collections import namedtuple
from mesh.generic.cmds import NodeCmds, TDMACmds
from mesh.generic.command import Command
import math

class NetworkVote(IntEnum):
    NotReceived = 0
    Yes = 1
    No = 2
    Excluded = 3

class VoteDecision(IntEnum):
    Undecided = 0
    Yes = 1
    No = 2

class MeshMsgType(IntEnum):
    CmdResponse = 0
    MsgBytes = 1
    BlockData = 2

class NetworkPoll(object):
    def __init__(self, sourceId, cmdId, cmdCounter, cmd, votes, exclusions, startTime):
        self.sourceId = sourceId
        self.cmdId = cmdId
        self.cmdCounter = cmdCounter
        self.cmd = cmd
        self.votes = votes
        self.exclusions = exclusions
        self.startTime = startTime # wait time before clearing uncompleted poll
        self.decision = VoteDecision.Undecided
        self.voteSent = False

class MeshTxMsg(object):
    def __init__(self, destId, msgBytes):
        self.destId = destId
        self.msgBytes = msgBytes

class MeshMsg(object):
    def __init__(self, msgType, cmdId=None, status=None, msgBytes=None):
        self.msgType = msgType
        self.cmdId = cmdId
        self.status = status
        self.msgBytes = msgBytes

#NetworkPoll = namedtuple('NetworkPoll', ['cmdId', 'cmdCounter', 'votes', 'exclusions', 'decision', 'voteSent'])

class MeshController(object):   
    """Generic node controller to subtype for specific vehicle types.

    Attributes:
        logFile: File object for logging node data.
        logTime: Time of last write to log file.
        nodeConfig: NodeConfig instance that stores configuration data for this node.
    """

    def __init__(self, nodeParams, comm):
        self.comm = comm   

        # Network polling
        self.networkPolls = []
 
        # Block transmit
        self.blockReqIdCounter = 0
        self.blockTx = None
        self.blockTxData = None
        self.blockTxAccepted = False

        # Node configuration
        self.nodeParams = nodeParams

        # Mesh messages
        self.meshMsgs = []

    def execute(self):
        """Executes any processing logic required by this node."""
     
        # Check status of mesh network
        self.monitorNetworkStatus()
        
        # Update node status
        self.nodeParams.updateStatus()

        # Execute comm
        self.comm.execute()

    def monitorNodeUpdates(self):
        """Monitors time since last state update from other nodes."""
        
        # Check that other nodes' states are updating
        for node in range(0, self.nodeParams.config.maxNumNodes):
            if (self.comm.meshPaths[node]): # path exists so node is present and updating
                self.nodeParams.nodeStatus[node].updating = True
            else:
                self.nodeParams.nodeStatus[node].updating = False
                
    def monitorNetworkStatus(self):
        """Monitors status of nodes to determine their current status."""

        # Monitor mesh network init (including loading received configuration)
        if (self.comm.networkConfigConfirmed == False and self.comm.networkConfigRcvd == True): # load new config
            print("Loading received configuration")
            print("Node number: " + str(self.nodeParams.config.nodeId))
            self.nodeParams.updateConfig()
            self.comm.reinit(self.nodeParams)

        # Monitor for network restart
        if (self.nodeParams.restartRequested):
            if (self.nodeParams.clock.getTime() >= self.nodeParams.restartTime): # restart node
                print("Restarting node " + str(self.nodeParams.config.nodeId)) 
                self.nodeParams.updateConfig() # use any pending configuration update
                self.comm.reinit(self.nodeParams, (self.nodeParams.config.nodeId-1) * 2.0)
                self.nodeParams.initNodeStatus()               
 
                # Clear restart status
                self.nodeParams.restartRequested = False
                self.nodeParams.restartTime = None

        # Monitor block transmit
        if (self.blockTxAccepted):
            if (self.nodeParams.clock.getTime() >= self.blockTx['startTime']): # start block transmit
                # Start block transmit
                self.comm.startBlockTx(self.blockTx['blockReqId'], self.blockTx['destId'], self.blockTx['sourceId'], self.blockTx['startTime'], self.blockTx['length'], self.blockTxData)

                # Clear block transmit status
                self.blockTx = None
                self.blockTxData = None
                self.blockTxAccepted = False

        #if (self.nodeParams.restartRequested):
         #   if (self.nodeParams.restartConfirmed): # Trigger restart at requested time
          #      if (self.nodeParams.clock.getTime() >= self.nodeParams.restartTime):
           #         self.comm.reinit(self.nodeParams)

            #elif (self.nodeParams.clock.getTime() < self.nodeParams.restartTime): # timer not yet lapsed
                # Check for unanimous positive response from active nodes
             #   restartConfirmed = True
              #  for node in self.nodeParams.nodeStatus:
               #     if (node.present and node.restartConfirmed == False):
                #        restartConfirmed = False
                 #       break
            
                #self.nodeParams.restartConfirmed = restartConfirmed    

            #else: # Restart time passed without confirmation
            #    self.nodeParams.restartTime = None
            #    self.nodeParams.restartRequested = False
                #self.nodeParams.restartConfirmed = False
                
                # Clear restart confirmed status
                #for node in self.nodeParams.nodeStatus:
                #    node.restartConfirmed = False

        
        # Check update status
        self.monitorNodeUpdates()

        # Check node links
        self.nodeParams.checkNodeLinks()
  
        # Process messages
        self.processNetworkMsgs()
 
        # Check network polls
        self.checkPolling()

    def processNetworkMsgs(self):
        # Process pending network messages
        for msg in self.comm.networkMsgQueue:
            
            # Create new poll to monitor command acceptance
            if ('destId' in msg['msgContents'] and msg['msgContents']['destId'] != 0): # populate exclusion list
                exclusions = [msg['msgContents']['destId']] # destination node is excluded from polling
            else:
                exclusions = []
            newPoll = NetworkPoll(msg['header']['sourceId'], msg['header']['cmdId'], msg['header']['cmdCounter'], msg['msgContents'], [NetworkVote.NotReceived]*self.nodeParams.config.maxNumNodes, exclusions, self.nodeParams.clock.getTime())
            newPoll.votes[msg['header']['sourceId']-1] = NetworkVote.Yes # source of command is automatic yes vote
            self.networkPolls.append(newPoll)
            #print("New poll created for " + str(msg['header']['cmdCounter']))

        # Clear network message queue
        self.comm.networkMsgQueue = []

    def checkPolling(self):

        # Update poll status
        for poll in self.networkPolls:
            # Respond to poll
            if (poll.voteSent == False): # respond to poll
                if (poll.cmdId == TDMACmds['ConfigUpdate']):   
                    if (poll.cmd['valid'] == True):
                        poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.Yes
                    else: # invalid config
                        poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.No
                elif (poll.cmdId == TDMACmds['NetworkRestart']):
                    # TODO - Hardcode positive response for now
                    poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.Yes
                elif (poll.cmdId == TDMACmds['BlockTxRequest']):
                    if (self.blockTxAccepted or self.comm.blockTxInProgress): # reject new request
                        poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.No
                    else: # accept request
                        poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.Yes
        
                # Send poll response
                print("Node " + str(self.nodeParams.config.nodeId) + ": Sending command response")
                        
                self.comm.tdmaCmds[NodeCmds['CmdResponse']] = Command(NodeCmds['CmdResponse'], {'cmdId': poll.cmdId, 'cmdCounter': poll.cmdCounter, 'cmdResponse': True}, [NodeCmds['CmdResponse'], self.nodeParams.config.nodeId])
                poll.voteSent = True            

            # Process any pending command responses
            if (poll.cmdCounter in self.nodeParams.cmdResponse):
                for key in self.nodeParams.cmdResponse[poll.cmdCounter]:
                    if (self.nodeParams.cmdResponse[poll.cmdCounter][key] == 1):
                        poll.votes[key-1] = NetworkVote.Yes
                    elif (self.nodeParams.cmdResponse[poll.cmdCounter][key] == 0):
                        poll.votes[key-1] = NetworkVote.No
    
                del self.nodeParams.cmdResponse[poll.cmdCounter] 

            # Check for poll decision
            yesVotes = 0
            for node in range(0, self.nodeParams.config.maxNumNodes):
                if (node+1 in poll.exclusions or self.nodeParams.nodeStatus[node].updating == False): # node vote excluded
                    poll.votes[node] = NetworkVote.Excluded
                elif (poll.votes[node] == NetworkVote.No): # node voted no
                    poll.decision = VoteDecision.No
                    print("Node " + str(self.nodeParams.config.nodeId) + ": Vote failed - " + poll.cmdId, poll.cmdCounter)
                elif (poll.votes[node] == NetworkVote.Yes): # node voted yes
                    yesVotes += 1
                
            if (yesVotes == (self.nodeParams.config.maxNumNodes - len(poll.exclusions))): # all present and not excluded notes have concurred
                poll.decision = VoteDecision.Yes
                print("Node " + str(self.nodeParams.config.nodeId) + ": Vote succeeded - ", poll.cmdId, poll.cmdCounter)
 
        # Update poll status
        updatedPolls = []
        for poll in self.networkPolls:
            if (poll.decision == VoteDecision.Undecided): 
                # Check expiration on undecided polls
                if (self.nodeParams.clock.getTime() <= (poll.startTime + self.nodeParams.config.commConfig['pollTimeout'])): # poll has not yet expired
                    updatedPolls.append(poll)
                else:
                    print("Node " + str(self.nodeParams.config.nodeId) + ": Clearing poll")
                    
            else: # take action on completed poll
                self.executeNetworkAction(poll)
        self.networkPolls = updatedPolls

    def executeNetworkAction(self, poll):
        # Perform action from accepted poll
        if (poll.cmdId == TDMACmds['NetworkRestart']):
            if (poll.decision == VoteDecision.Yes and (poll.cmd['destId'] == 0 or poll.cmd['destId'] == self.nodeParams.config.nodeId)): # global or restart for this node
                self.nodeParams.restartRequested = True
                self.nodeParams.restartTime = poll.cmd['restartTime']
                print("Node " + str(self.nodeParams.config.nodeId) + " - Executing network restart.")               
                return True

        elif (poll.cmdId == TDMACmds['ConfigUpdate']):
            if (poll.decision == VoteDecision.Yes and (poll.cmd['destId'] == 0 or poll.cmd['destId'] == self.nodeParams.config.nodeId)): # load configuration for update
                self.nodeParams.newConfig = poll.cmd['config']
                print("Node " + str(self.nodeParams.config.nodeId) + " - Storing new config for update.")               
            else: # no action further action on rejected update
               pass
            return True        

        elif (poll.cmdId == TDMACmds['BlockTxRequest']):
            # Notify host of block transmit status
            if (poll.sourceId == self.nodeParams.config.nodeId):
                self.meshMsgs.append(MeshMsg(MeshMsgType.CmdResponse, cmdId=TDMACmds['BlockTxRequest'], status=poll.decision))

            if (poll.decision == VoteDecision.Yes): # Initiate block transmit
                # Store pending block transmit status
                self.blockTxAccepted = True
                self.blockTxStartTime = poll.cmd['startTime']
                self.blockTx = poll.cmd
                self.blockTx['blockData'] = self.blockTxData
                self.blockTx['sourceId'] = poll.sourceId
            
            return True

        else: # Unimplemented command
            print("Not an implemented command id")
            return False
 
    def sendMsg(self, destId, msg):
        """This function receives messages to be sent over the mesh network and queues them for transmission."""
        
        # Place message in appropriate position in outgoing queue (broadcast messages are stored in the zero position) 

        if (len(msg) <= self.nodeParams.config.commConfig['msgPayloadMaxLength']): # message meets size requirements
            self.comm.meshQueueIn.append(MeshTxMsg(destId, msg))
            return True
        else:
            return False

    def getMsgs(self):
        msgs = []

        # Output pending command responses
        for msg in self.meshMsgs:
            msgs.append(msg)
        self.meshMsgs = [] # clear messages


        # Output received network data bytes and block transfers
        if (self.comm.hostBuffer):
            msgs.append(MeshMsg(MeshMsgType.MsgBytes, msgBytes=self.comm.hostBuffer))
            self.comm.hostBuffer = bytearray() # clear messages after retrieval
        if (self.comm.blockTxOut):
            msgs.append(MeshMsg(MeshMsgType.BlockData, status=self.comm.blockTxOut['dataComplete'], msgBytes=self.comm.blockTxOut['data']))
            self.comm.blockTxOut = bytearray() # clear after retrieval
        
        return msgs

    def sendDataBlock(self, destId, blockBytes):
        """This function receives a large data block to be sent over the mesh network for Block Transfer."""
        # Store data block and request block data transfer
        blockTxStartTime = int(self.nodeParams.clock.getTime() + self.nodeParams.config.commConfig['pollTimeout'])
        blockTxLength = math.ceil(len(blockBytes) / self.nodeParams.config.commConfig['blockTxPacketSize']) # length in number of packets

        if (blockTxLength > self.nodeParams.config.commConfig['blockTxMaxLength']): # data block is too large
            return False

        self.blockTxData = blockBytes
        self.comm.tdmaCmds[TDMACmds['BlockTxRequest']] = Command(TDMACmds['BlockTxRequest'], {'blockReqId': self.getBlockRequestId(), 'destId': destId, 'startTime': blockTxStartTime, 'length': blockTxLength, 'status': 1}, [TDMACmds['BlockTxRequest'], self.nodeParams.config.nodeId, self.nodeParams.get_cmdCounter()])

        return True

    def getBlockRequestId(self):
        self.blockReqIdCounter = (self.blockReqIdCounter + 1) % 256 # wrap after exceeding 8-bit value
        return self.blockReqIdCounter 
