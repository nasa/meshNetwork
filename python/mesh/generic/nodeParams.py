import random
from collections import deque
from mesh.generic.nodeConfig import NodeConfig
from mesh.generic.customExceptions import InvalidCmdCounter
from mesh.generic.formationClock import FormationClock
from mesh.generic.tdmaState import TDMAStatus
from mesh.generic.nodeState import NodeState, LinkStatus
from mesh.generic.nodeTools import isBeaglebone
import mesh.generic.gpio as GPIO

class NodeParams():
    def __init__(self, configFile=[], config=[]):
        if configFile:
            self.config = NodeConfig(configFile)
        elif config:
            self.config = config

        self.cmdCounterMax = 255 # DEPRECATED - TODO - DELETE
        self.cmdCounterThreshold = 10 # DEPRECATED - TODO - DELETE  
        self.commStartTime = []
        #self.cmdRelayBuffer = []
        self.cmdHistory = deque(maxlen=50) # FIFO list of last commands received

        # Node status
        self.nodeStatus = [NodeState(node+1) for node in range(self.config.maxNumNodes)]
        
        # Formation clock
        self.clock = FormationClock()

        # TDMA Failsafe status
        self.tdmaStatus = TDMAStatus.nominal
        self.frameStartTime = [] # DEPRECATED - REMOVE
        self.tdmaFailsafe = False
        self.timeOffsetTimer = None
        if isBeaglebone():
            if (self.config.commConfig['fpga'] == True):
                # Setup FPGA failsafe status pin
                self.fpgaFailsafePin = self.config.commConfig['fpgaFailsafePin']
                GPIO.setup(self.fpgaFailsafePin, "in")
            else:
                self.fpgaFailsafePin = []
        # Comm link status
        self.linkStatus = [[LinkStatus.NoLink for i in range(self.config.maxNumNodes)] for j in range(self.config.maxNumNodes)]

    def get_cmdCounter(self):
        #if self.commStartTime: # time-based counter
        #    return int((self.clock.getTime() - self.commStartTime)*1000)
        #else: # random counter
            return random.randint(1, 65536)
    
    def checkTimeOffset(self, offset=None):
        if (self.config.commType == "TDMA"): # TDMA time offset failsafe
            if self.config.commConfig['fpga'] and self.config.fpgaFailsafePin: # TDMA time controlled by FPGA
                if (GPIO.input(self.fpgaFailsafePin) == 0): # failsafe not set
                    self.timeOffsetTimer = None # reset timer
                else: # failsafe condition set
                    if self.timeOffsetTimer:
                        if self.clock.getTime() - self.timeOffsetTimer > self.config.commConfig['offsetTimeout']: # No time offset reading for longer than allowed
                            self.tdmaFailsafe = True # Set TDMA failsafe flag
                            return 3
                    else: # start timer
                        self.timeOffsetTimer = self.clock.getTime()
                    
            else:
                if offset == None: # offset not provided so attempt to get offset from clock
                    offset = self.clock.getOffset()

                if offset != None: # time offset available
                    self.timeOffsetTimer = None # reset time offset timer
                    self.nodeStatus[self.config.nodeId-1].timeOffset = offset
                    if abs(self.nodeStatus[self.config.nodeId-1].timeOffset) > self.config.commConfig['operateSyncBound']:
                        return 1
                else: # no offset available
                    self.nodeStatus[self.config.nodeId-1].timeOffset = 127 # Error value
                    # Check time offset timer
                    if self.timeOffsetTimer:
                        #print(self.clock.getTime() - self.timeOffsetTimer)
                        if self.clock.getTime() - self.timeOffsetTimer > self.config.commConfig['offsetTimeout']: # No time offset reading for longer than allowed
                            self.tdmaFailsafe = True # Set TDMA failsafe flag
                            return 2
                    else: # start timer
                        self.timeOffsetTimer = self.clock.getTime()
