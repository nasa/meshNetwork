from mesh.generic.nodeComm import NodeComm
from switch import switch
import random, time, math
from math import ceil
from mesh.generic.slipMsg import SLIP_END, SLIP_END_TDMA
from mesh.generic.radio import RadioMode
from mesh.generic.cmds import TDMACmds
from mesh.generic.tdmaState import TDMAStatus, TDMAMode, TDMABlockTxStatus
from mesh.generic.cmdDict import CmdDict
from mesh.generic.command import Command
from mesh.generic.customExceptions import InvalidTDMASlotNumber
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
import crcmod.predefined # crc
import sys, struct
#import Adafruit_BBIO.GPIO as GPIO

class TDMAComm(NodeComm):
    def __init__(self, commProcessor, radio, msgParser, nodeParams):
        if not commProcessor:
            commProcessor = CommProcessor([TDMACmdProcessor], nodeParams)

        NodeComm.__init__(self, commProcessor, radio, msgParser, nodeParams)        

        # TDMA init status
        #self.initPin = nodeParams.config.commConfig['initPin']
        #self.initAckPin = nodeParams.config.commConfig['initAckPin']
        #GPIO.setup(self.initPin, GPIO.IN)
        #GPIO.setup(self.initAckPin, GPIO.OUT)
        #GPIO.output(self.initAckPin, GPIO.LOW)
        #self.initTimeMsg = b'';
        self.inited = False

        self.crc16 = crcmod.predefined.mkCrcFun('crc16')
        
        # TDMA config
        self.transmitInterval = 1.0/nodeParams.config.commConfig['desiredDataRate']
        self.lastTransmitTime = -1.0

        # Command buffer
        self.cmdBuffer = dict()

        self.enabled = True

    def execute(self):
        """Execute communication functions."""
        currentTime = time.time()   
        # Initialize mesh network
        if self.inited == False: # local TDMA status not inited
            #if (GPIO.input(self.initPin) == 0): # FPGA TDMA not inited
            self.init() # look for comm start time
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
            self.sendMsg()
        
    def init(self):
        if self.nodeParams.commStartTime == []: # Mesh not initialized
            self.initComm()
            return
        else: # join/start mesh
            print("TDMA initialized with start time:", self.nodeParams.commStartTime)    
            self.initMesh(self.nodeParams.commStartTime)
    
    def initMesh(self, currentTime=time.time()):
        """Initialize node mesh networks."""
        # Create tdma comm messages
        self.tdmaCmds = dict()
        flooredStartTime = math.floor(self.nodeParams.commStartTime)
        self.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(flooredStartTime), 'status': self.nodeParams.tdmaStatus}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['statusTxInterval'])
        self.tdmaCmds[TDMACmds['LinkStatus']] = Command(TDMACmds['LinkStatus'], {'linkStatus': self.nodeParams.linkStatus, 'nodeId': self.nodeParams.config.nodeId}, [TDMACmds['LinkStatus'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['linksTxInterval'])
        
        # Init message for FPGA
        #self.initTimeMsg = struct.pack("=I", int(flooredStartTime))
        #self.initTimeMsg = SLIP_END + struct.pack("=B", TDMACmds['MeshStatus']) + self.initTimeMsg + struct.pack("=H", self.crc16(self.initTimeMsg))
       
        if self.nodeParams.config.nodeId != 0: # stop ground node from broadcasting time offset
            self.tdmaCmds[TDMACmds['TimeOffset']] = Command(TDMACmds['TimeOffset'], {'nodeStatus': self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1]}, [TDMACmds['TimeOffset'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['offsetTxInterval'])
    
        self.inited = True
        #GPIO.setup(self.initAckPin, GPIO.OUT)
        #GPIO.output(self.initAckPin, GPIO.HIGH) # send init ack to FPGA
         
    def initComm(self):
        # Look for tdma status message
        self.readBytes(True)
        if self.radio.bytesInRxBuffer > 0:
            self.parseMsgs()
            while self.msgParser.parsedMsgs:
                msg = self.msgParser.parsedMsgs.pop(0)
                cmdId = struct.unpack('=B',msg[0:1])[0]
                if cmdId == TDMACmds['MeshStatus']:
                    self.processMsg(msg, {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self, 'clock': self.nodeParams.clock})  
            
    def sendMsg(self):
        if (self.enabled == False): # Don't send anything if disabled
            return

        self.sendTDMACmds()
        if self.cmdBuffer: # command buffer
            noRepeatCmds = []
            for key in self.cmdBuffer:
            
            #for i in range(len(self.cmdBuffer)):
                self.bufferTxMsg(self.cmdBuffer[key]['bytes'])
                if self.cmdBuffer[key]['txInterval'] == 0: # no repeat
                    #self.cmdBuffer.pop(key)
                    noRepeatCmds.append(key)
            for key in noRepeatCmds: # remove non-repeat commands
                self.cmdBuffer.pop(key)
                
        if self.cmdRelayBuffer: # Add commands to tx buffer and clear relay buffer
            #for cmd in self.cmdRelayBuffer:
                #self.bufferTxMsg(cmd)
            self.radio.bufferTxMsg(self.cmdRelayBuffer)
        self.cmdRelayBuffer = bytearray()
        self.radio.bufferTxMsg(SLIP_END_TDMA)
        self.radio.sendBuffer(self.nodeParams.config.commConfig['maxTransferSize'])
    
    def readMsg(self):
        self.radio.readBytes(True)
    
    def sendTDMACmds(self):
        # Send TDMA messages
        timestamp = self.nodeParams.clock.getTime()
        for cmdId in list(self.tdmaCmds.keys()):
            cmd = self.tdmaCmds[cmdId]
            if ceil(timestamp*100)/100.0 >= ceil((cmd.lastTxTime + cmd.txInterval)*100)/100.0: # only compare down to milliseconds
                self.bufferTxMsg(cmd.serialize(timestamp))
                
    
