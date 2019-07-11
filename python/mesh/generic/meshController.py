from enum import IntEnum
from collections import namedtuple
from mesh.generic.cmds import NodeCmds, TDMACmds
from mesh.generic.command import Command
from switch import switch

class NetworkVote(IntEnum):
    NotReceived = 0
    Yes = 1
    No = 2
    Excluded = 3

class VoteDecision(IntEnum):
    Undecided = 0
    Yes = 1
    No = 2

class NetworkPoll(object):
    def __init__(self, cmdId, cmdCounter, cmd, votes, exclusions):
        self.cmdId = cmdId
        self.cmdCounter = cmdCounter
        self.cmd = cmd
        self.votes = votes
        self.exclusions = exclusions
        self.decision = VoteDecision.Undecided
        self.voteSent = False

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
 
        # Node configuration
        self.nodeParams = nodeParams

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
            print("Node " + str(self.nodeParams.config.nodeId) + " - Message received: ", str(msg['header']['cmdId']))
            
            # Create new poll to monitor command acceptance
            if ('destId' in msg['msgContents'] and msg['msgContents']['destId'] != 0): # populate exclusion list
                exclusions = [msg['msgContents']['destId']]
            else:
                exclusions = []
            newPoll = NetworkPoll(msg['header']['cmdId'], msg['header']['cmdCounter'], msg['msgContents'], [NetworkVote.NotReceived]*self.nodeParams.config.maxNumNodes, exclusions)
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
                for case in switch(poll.cmdId):
                    if case(TDMACmds['ConfigUpdate']):
                        if (poll.cmd['valid'] == True):
                            poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.Yes
                        else: # invalid config
                            poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.No
                        break
                    
                    if case(TDMACmds['NetworkRestart']):
                        # TODO - Hardcode positive response for now
                        poll.votes[self.nodeParams.config.nodeId-1] = NetworkVote.Yes
                        break
                    
                # Send poll response        
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
 
        # Take action on completed polls and remove from list
        updatedPolls = []
        for poll in self.networkPolls:
            if (poll.decision == VoteDecision.Undecided):
                updatedPolls.append(poll)
            else: # take action on poll
                self.executeNetworkAction(poll)
        self.networkPolls = updatedPolls

    def executeNetworkAction(self, poll):
        # Perform action from accepted poll
        for case in switch(poll.cmdId):
            if case(TDMACmds['NetworkRestart']):
                if (poll.decision == VoteDecision.Yes and (poll.cmd['destId'] == 0 or poll.cmd['destId'] == self.nodeParams.config.nodeId)): # global or restart for this node
                    self.nodeParams.restartRequested = True
                    self.nodeParams.restartTime = poll.cmd['restartTime']
                    print("Node " + str(self.nodeParams.config.nodeId) + " - Executing network restart.")               
                    return True
                break

            if case(TDMACmds['ConfigUpdate']):
                if (poll.decision == VoteDecision.Yes and (poll.cmd['destId'] == 0 or poll.cmd['destId'] == self.nodeParams.config.nodeId)): # load configuration for update
                    self.nodeParams.newConfig = poll.cmd['config']
                    print("Node " + str(self.nodeParams.config.nodeId) + " - Storing new config for update.")               
                else: # no action further action on rejected update
                    pass
                return True        

            else: # Unimplemented command
                print("Not an implemented command id")
                return False
 
    def sendMsg(self, destId, msgBytes):
        """This function receives messages to be sent over the mesh network and queues them for transmission."""
        
        # Place message in appropriate position in outgoing queue (broadcast messages are stored in the zero position) 
        self.comm.meshQueueIn[destId] += msgBytes

    def getMsgs(self):
        msgs = self.comm.hostBuffer
        self.comm.hostBuffer = bytearray() # clear messages after retrieval
        
        return msgs


    # TODO - monitor network voting
