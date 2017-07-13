from mesh.generic.tdmaComm import TDMAComm
from switch import switch
import time
from mesh.generic.tdmaState import TDMAMode
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor

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

    def execute(self):
        """Execute communication functions."""
        currentTime = time.time()   

        # Initialize mesh network
        if self.inited == False: # local TDMA status not inited
            #if (GPIO.input(self.initPin) == 0): # FPGA TDMA not inited
            self.init(currentTime) # look for comm start time
            return
            #else: # temporary hack TODO: FIX THIS!
            #    self.nodeParams.commStartTime = 0;
            #    self.initMesh(self.nodeParams.commStartTime)
        else: # perform TDMA execution logic
            #if (GPIO.input(self.initPin) == 0): # FPGA TDMA not inited
                # send start time to fpga
                #self.radio.sendBytes(self.initTimeMsg)
                
            self.executeTDMAComm()
    
    def executeTDMAComm(self):
        """Execute TDMA communication scheme."""
        # Read any new bytes
        self.readMsg()
        
        # Send current message data
        if (time.time() - self.lastTransmitTime > self.transmitInterval):
            self.lastTransmitTime = time.time()
            self.tdmaMode == TDMAMode.transmit
            self.sendMsg()
        else:
            self.tdmaMode = TDMAMode.receive

    def initComm(self, currentTime):
        self.checkForInit()

    def readMsg(self):
        self.radio.readBytes(True)
    
    def sleep(self): # no sleep operations for FPGA implementation
        pass
