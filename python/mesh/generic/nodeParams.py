import random
from collections import deque
from mesh.generic.nodeConfig import NodeConfig
from mesh.generic.formationClock import FormationClock
from mesh.generic.nodeState import NodeState, LinkStatus
from mesh.generic.cmdDict import CmdDict 

class NodeParams():
    def __init__(self, configFile=[], config=[]):
        if configFile:
            self.config = NodeConfig(configFile)
        elif config:
            self.config = config

        self.setupParams()

    def setupParams(self):
        self.configConfirmed = False

        #self.commStartTime = None
        #self.cmdRelayBuffer = []
        self.cmdHistory = deque(maxlen=100) # FIFO list of last commands received

        # Node status
        self.nodeStatus = [NodeState(node+1) for node in range(self.config.maxNumNodes)]
        
        # Formation clock
        self.clock = FormationClock()

        # Comm link status
        self.linkStatus = [[LinkStatus.NoLink for i in range(self.config.maxNumNodes)] for j in range(self.config.maxNumNodes)]

    def get_cmdCounter(self):
        #if self.commStartTime: # time-based counter
        #    return int((self.clock.getTime() - self.commStartTime)*1000)
        #else: # random counter
            return random.randint(1, 65536)

    def updateStatus(self):
        """Update status information."""
        self.nodeStatus[self.config.nodeId-1].status = 0
        if (self.configConfirmed == True):
            self.nodeStatus[self.config.nodeId-1].status += 64 # bit 6

    def checkNodeLinks(self):
        """Checks status of links to other nodes."""
        thisNode = self.config.nodeId - 1
        for i in range(self.config.maxNumNodes):
            # Check for direct link
            if (self.nodeStatus[i].present and (self.clock.getTime() - self.nodeStatus[i].lastMsgRcvdTime) < self.config.commConfig['linkTimeout']):
                self.linkStatus[thisNode][i] = LinkStatus.GoodLink
                
            # Check for indirect link
            elif (self.nodeStatus[i].updating == True): # state data is updating, so at least an indirect link
                self.linkStatus[thisNode][i] = LinkStatus.IndirectLink
                
            else: # no link
                    self.linkStatus[thisNode][i] = LinkStatus.NoLink
