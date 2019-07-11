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

        # Configuration update holder
        self.newConfig = None

        # Mesh status
        self.restartTime = None
        self.restartRequested = False
        self.restartConfirmed = False

        self.setupParams()

    def setupParams(self):
        self.configConfirmed = False

        #self.commStartTime = None
        #self.cmdRelayBuffer = []
        self.cmdHistory = deque(maxlen=100) # FIFO list of last commands received

        self.cmdResponse = dict()

        # Initialize node status
        self.initNodeStatus()
        
        # Formation clock
        self.clock = FormationClock()


    def initNodeStatus(self):
        # Node status
        self.nodeStatus = [NodeState(node+1) for node in range(self.config.maxNumNodes)]
        
        # Comm link status
        self.linkStatus = [[LinkStatus.NoLink for i in range(self.config.maxNumNodes)] for j in range(self.config.maxNumNodes)]

    def get_cmdCounter(self):
        #if self.commStartTime: # time-based counter
        #    return int((self.clock.getTime() - self.commStartTime)*1000)
        #else: # random counter
            cmdCounter = random.randint(1, 65536)

            # Add counter value to history
            self.cmdHistory.append(cmdCounter)

            return cmdCounter

    def loadConfig(self, newConfig, hashValue):
        '''Verify and queue new configuration for loading.'''

        # Convert from protobuf to json
        jsonConfig = NodeConfig.fromProtoBuf(newConfig)
        jsonConfig['node']['nodeId'] = self.config.nodeId # Don't overwrite node id via update

        # Create, verify, and store new configuration
        newConfig = NodeConfig(configData=jsonConfig)

        if (newConfig.calculateHash() == hashValue and newConfig.loadSuccess): # configuration verified
            #self.newConfig = newConfig
            return [True, newConfig]
        else:
            #self.newConfig = None
            return [False, None]
    
    def updateConfig(self):
        retValue = False
        if (self.newConfig and self.newConfig.loadSuccess): # load pending configuration update
            print("Node " + str(self.config.nodeId) + ": Updating to new configuration")
            self.config = self.newConfig
            retValue = True

        self.newConfig = None

        return retValue

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

    def addCmdResponse(self, cmdCounter, cmdResponse, sourceId):
        if (cmdCounter in self.cmdResponse): # update existing responses
            self.cmdResponse[cmdCounter][sourceId] = cmdResponse
        else: # add new command response
            self.cmdResponse[cmdCounter] = dict()
            self.cmdResponse[cmdCounter][sourceId] = cmdResponse
