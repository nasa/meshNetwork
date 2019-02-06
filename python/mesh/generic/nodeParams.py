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
        self.cmdHistory = deque(maxlen=50) # FIFO list of last commands received

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
