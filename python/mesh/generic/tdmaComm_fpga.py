from mesh.generic.tdmaComm import TDMAComm
from switch import switch
import time
from mesh.generic.tdmaState import TDMAMode
from mesh.generic.cmds import TDMACmds
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.command import Command

class TDMAComm_FPGA(TDMAComm):
    def __init__(self, commProcessor, radio, msgParser, nodeParams):
        if not commProcessor:
            commProcessor = CommProcessor([TDMACmdProcessor], nodeParams)

        TDMAComm.__init__(self, commProcessor, radio, msgParser, nodeParams)        

        # TDMA init status
        #self.initPin = nodeParams.config.commConfig['initPin']
        #self.initAckPin = nodeParams.config.commConfig['initAckPin']
        #GPIO.setup(self.initPin, GPIO.IN)
        #GPIO.setup(self.initAckPin, GPIO.OUT)
        #GPIO.output(self.initAckPin, GPIO.LOW)
        #self.initTimeMsg = b'';

        # TDMA config for FPGA implementation
        self.transmitInterval = 1.0/nodeParams.config.commConfig['desiredDataRate']
        self.lastTransmitTime = -1.0

    def executeTDMAComm(self, currentTime):
        """Execute TDMA communication scheme."""
        # Read any new bytes
        self.readMsg()
        
        # Send current message data
        if (time.time() - self.lastTransmitTime > self.transmitInterval):
            self.lastTransmitTime = time.time()
            self.tdmaMode = TDMAMode.transmit
            print("TdmaMode in execute:", self.tdmaMode)
            self.sendMsg()
        else:
            self.tdmaMode = TDMAMode.receive

    def init(self, currentTime):
        # Network search and start performed by FPGA
        self.initMesh()

    def initMesh(self, currentTime=time.time()):
        self.tdmaCmds[TDMACmds['LinkStatus']] = Command(TDMACmds['LinkStatus'], {'linkStatus': self.nodeParams.linkStatus, 'nodeId': self.nodeParams.config.nodeId}, [TDMACmds['LinkStatus'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['linksTxInterval'])
        
        if self.nodeParams.config.nodeId != 0: # stop ground node from broadcasting time offset
            self.tdmaCmds[TDMACmds['TimeOffset']] = Command(TDMACmds['TimeOffset'], {'nodeStatus': self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1]}, [TDMACmds['TimeOffset'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['offsetTxInterval'])
        
        self.inited = True
        print("Node " + str(self.nodeParams.config.nodeId) + " - Initializing comm")
            

    def readMsg(self):
        self.radio.readBytes(True)
    
    def sleep(self): # no sleep operations for FPGA implementation
        pass
