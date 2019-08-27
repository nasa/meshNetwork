from mesh.generic.serialComm import SerialComm
from switch import switch
import random, time, math
from math import ceil
from copy import deepcopy
from mesh.generic.msgParser import MsgParser
from mesh.generic.slipMsg import SLIPMsg
from mesh.generic.radio import RadioMode
from mesh.generic.cmds import TDMACmds, NodeCmds
from mesh.generic.tdmaState import TDMAStatus, TDMAMode, TDMABlockTxStatus
from mesh.generic.cmdDict import CmdDict
from mesh.generic.command import Command
from mesh.generic.customExceptions import InvalidTDMASlotNumber
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.nodeCmdProcessor import NodeCmdProcessor
from mesh.generic.dijkstra import findShortestPaths
from mesh.generic.nodeConfig import NodeConfig
from mesh.generic.blockTx import BlockTx, BlockTxPacketStatus
import struct

BLOCK_TX_MSG = 1

class TDMAComm(SerialComm):
    def __init__(self, msgProcessors, radio, msgParser, nodeParams):
        if not msgProcessors:
            msgProcessors = [NodeCmdProcessor, TDMACmdProcessor]

        super().__init__(msgProcessors, nodeParams, radio, parser=msgParser)

        self.reinit(nodeParams)
    
    def reinit(self, nodeParams, initDelay=None):

        self.nodeParams = nodeParams

        # TDMA config       
        self.tdmaMode = TDMAMode.sleep
        self.frameStartTime = []
        self.commStartTime = None # time that TDMA comm was started - initialized manually by first node or parsed from messages received for nodes joining existing mesh
        self.networkConfigConfirmed = None
        self.networkConfigRcvd = False
        self.maxNumSlots = nodeParams.config.commConfig['maxNumSlots'] # Maximum number of slots
        self.enableLength = nodeParams.config.commConfig['enableLength']
        self.slotTime = 0.0
        self.slotNum = 1        
        self.slotStartTime = 0.0
        self.networkMsgQueue = []   
 
        # TDMA Frame variables
        self.frameTime = 0.0
        self.frameCount = 0
        self.frameLength = nodeParams.config.commConfig['frameLength']
        self.cycleLength = nodeParams.config.commConfig['cycleLength']
        self.adminEnabled = nodeParams.config.commConfig['adminEnable']
        self.adminLength = nodeParams.config.commConfig['adminLength']

        # TDMA status
        self.tdmaStatus = TDMAStatus.nominal
        self.tdmaFailsafe = False
        self.timeOffsetTimer = None
        self.frameExceedanceCount = 0       
 
        # Mesh initialization variables
        self.inited = False
        self.initTimeToWait = nodeParams.config.commConfig['initTimeToWait'] # Time to wait before assuming no existing mesh network
        self.initStartTime = None
        
        # Mesh network commands
        self.tdmaCmds = dict()
        self.tdmaCmdParser = MsgParser({'parseMsgMax': nodeParams.config.parseMsgMax}, SLIPMsg(2048))
        
        # Transmit period variables
        self.transmitSlot = nodeParams.config.commConfig['transmitSlot'] # Slot in cycle that this node is schedule to transmit
        self.beginTxTime = self.enableLength + nodeParams.config.commConfig['preTxGuardLength']
        self.endTxTime = self.beginTxTime + nodeParams.config.commConfig['txLength']
        self.transmitComplete = False       
    
        # Receive period variables
        self.beginRxTime = self.enableLength
        self.endRxTime = self.beginRxTime + nodeParams.config.commConfig['rxLength']
        self.slotLength = nodeParams.config.commConfig['slotLength'] # total length of slot
        self.rxLength = nodeParams.config.commConfig['rxLength']
        self.rxReadTime = self.beginTxTime + nodeParams.config.commConfig['rxDelay'] # time to begin reading serial
        self.receiveComplete = False

        # Current read position in radio rx buffer
        self.rxBufferReadPos = 0

        # Mesh header information
        self.meshPacketHeaderFormat = '<BBHHHB'
        self.meshHeaderLen = struct.calcsize(self.meshPacketHeaderFormat)

        # Block Tx information
        self.blockTx = None
        self.blockTxInProgress = False
        self.blockTxPacketStatus = dict() # stores transmitted packet status until all receipt requests received
        self.blockTxPacketReceipts = []

        # Comm enable flag
        self.enabled = True

        # Mesh data in/out buffers
        #self.meshQueueIn = [b''] * (self.maxNumSlots + 1)
        self.meshQueueIn = []
        self.hostBuffer = bytearray()
        self.blockTxOut = dict()

        # Network graph
        #self.meshGraph = [0] * self.maxNumSlots # timestamps of last received message from each other node
        self.lastGraphUpdate = 0.0
        self.meshPaths = [[]*self.maxNumSlots] * self.maxNumSlots
        self.neighbors = []

        # Delay init (for full network restart)
        if (initDelay):
            time.sleep(initDelay)

        # Network metrics
        self.bytesSent = 0
        self.bytesRcvd = 0

    def execute(self):
        """Execute communication functions."""
        currentTime = time.time()

        # Initialize mesh network
        if self.inited == False:
            self.init(currentTime)
            return
        else: # perform TDMA execution logic
            self.executeTDMAComm(currentTime)
    
    def updateFrameTime(self, currentTime):
        self.frameTime = currentTime - self.frameStartTime
        
        if self.frameTime >= self.frameLength: # Start new frame
            #print(str(currentTime) + ": Node " + str(self.nodeParams.config.nodeId) + " - New frame started")
            self.syncTDMAFrame(currentTime)
            #print("Node " + str(self.nodeParams.config.nodeId) + " - Previous frame data throughput(in/out): ", self.bytesRcvd, self.bytesSent)
            self.bytesSent = 0
            self.bytesRcvd = 0
        
        if self.frameTime < (self.cycleLength + self.adminLength): # active portion of frame
            return 0
        else: 
            return 1
        #elif self.frameTime < (self.cycleLength + self.adminLength): # admin period
        #    framePeriod = 1
        #else: # sleep period
        #    framePeriod = 2

        #return framePeriod

    def executeTDMAComm(self, currentTime):
        """Execute TDMA communication scheme."""
        # Check for block transfers
        #self.monitorBlockTx()
 
        # Update frame time
        frameStatus = self.updateFrameTime(currentTime)
        
        # Check for mode updates
        self.updateMode(self.frameTime)
        
        # Execute sleep
        if (frameStatus == 1):
            self.sleep()
            return
        #elif (frameStatus == 2):
        #    self.sleep()
        #    return

    
        # Perform mode specific behavior
        for case in switch(self.tdmaMode):
            if case(TDMAMode.admin):
                self.admin()
                break
            if case(TDMAMode.sleep):
                # Set radio to sleep mode
                self.radio.setMode(RadioMode.sleep)
                break
            if case(TDMAMode.init):
                # Prepare radio to receive or transmit
                if self.slotNum == self.transmitSlot:
                    # Set radio to transmit mode
                    self.radio.setMode(RadioMode.transmit)
                else: 
                    # Set radio to receive mode
                    self.radio.setMode(RadioMode.receive)
                break
            if case(TDMAMode.receive):
                # Read data if TDMA message end not yet found
                if self.receiveComplete == False and self.slotTime >= self.rxReadTime:
                    self.radio.setMode(RadioMode.receive) # set radio mode
                    # Delay so we aren't hammering the radio
                    #remainingRxTime = self.rxLength - (self.slotTime - self.enableLength)
                    #time.sleep(remainingRxTime*0.2)                        
                    self.receiveComplete = self.readMsgs()
                    if self.receiveComplete == True:
                        #print("Node " + str(self.nodeParams.config.nodeId) + " - End of receive slot " + str(self.slotNum)) 
                        # Set radio to sleep
                        self.radio.setMode(RadioMode.sleep)
                break
            if case(TDMAMode.transmit):
                # Send data
                if self.transmitComplete == False:
                    self.radio.setMode(RadioMode.transmit) # set radio mode
                    self.sendMsgs()
                else: # Set radio to sleep
                    self.radio.setMode(RadioMode.sleep)
                break
            if case(TDMAMode.failsafe): # Read only failsafe mode
                # Enable radio in receive mode and read data
                self.radio.setMode(RadioMode.receive)
                self.readMsgs()
                break
   
    def admin(self):
        # Disable radio upon admin completion
        if (self.receiveComplete == True or self.transmitComplete == True):
            self.radio.setMode(RadioMode.sleep)
            return

        # Admin period process control
        adminTime = self.frameTime - (self.cycleLength)
        if (self.blockTxInProgress): # execute block transfer logic
            self.executeBlockTx(adminTime)
        else:
            self.executeAdmin(adminTime)
        
    def executeAdmin(self, adminTime):
        adminLength = self.nodeParams.config.commConfig['adminBytesMaxLength'] + self.nodeParams.config.commConfig['msgPayloadMaxLength']
        controlNode = int(self.frameCount % (self.maxNumSlots+1) + 1) # each node gets a round as admin controller followed by one open opportunity for all
        if (adminTime < self.enableLength): # Initialize radio
            if (controlNode == self.nodeParams.config.nodeId): # This node is in control
                # Set radio to transmit mode
                self.radio.setMode(RadioMode.transmit)
            else: # listening this period
                # Set radio to receive mode
                self.radio.setMode(RadioMode.receive)
        else: # execute admin period
            if (controlNode == self.nodeParams.config.nodeId): # This node is in control
                if (self.transmitComplete == True):
                    self.radio.setMode(RadioMode.sleep)
                elif (adminTime >= self.beginTxTime): # Execute admin transmission 
                    self.radio.setMode(RadioMode.transmit) # set radio mode
                    adminBytes = self.packageAdminData(adminLength)
                    packetBytes = self.createMeshPacket(0, b'', adminBytes, self.nodeParams.config.nodeId)
                    if (packetBytes): # if packet is of non-zero length
                        self.bufferTxMsg(packetBytes)
                    
                    #self.radio.bufferTxMsg(HDLC_END_TDMA) # append end of message byte
                    self.bytesSent += self.sendBuffer() 

                    self.transmitComplete = True
                    #print("Node " + str(self.nodeParams.config.nodeId) + " - Admin transmit complete")
                    
            else: # other nodes in control this admin period
                if (self.receiveComplete == True):
                    self.radio.setMode(RadioMode.sleep)
                elif (adminTime >= self.rxReadTime):
                    self.radio.setMode(RadioMode.receive) # set radio mode
                    self.receiveComplete = self.readMsgs()
                    if (self.receiveComplete):    
                        #print("Node " + str(self.nodeParams.config.nodeId) + " - Admin receive complete")
                        self.radio.setMode(RadioMode.sleep)

    def executeBlockTx(self, adminTime):
        if (adminTime < self.enableLength): # Initialize radio
            if (self.blockTx.srcId == self.nodeParams.config.nodeId): # This node is transmiting
                # Set radio to transmit mode
                self.radio.setMode(RadioMode.transmit)
            else: # receiving
                # Set radio to receive mode
                self.radio.setMode(RadioMode.receive)
        else: # execute block transmit period
            if (self.blockTx.srcId == self.nodeParams.config.nodeId): # This node is sending
                if (self.transmitComplete == True):
                    self.radio.setMode(RadioMode.sleep)
                elif (adminTime >= self.beginTxTime): # Execute transmission 
                    self.radio.setMode(RadioMode.transmit) # set radio mode
                    
                    packetBytes = self.sendBlockTxPacket()
                    if (packetBytes): # if packet is of non-zero length
                        self.bufferTxMsg(packetBytes)
                    
                    #self.radio.bufferTxMsg(HDLC_END_TDMA) # append end of message byte
                    self.bytesSent += self.sendBuffer() 

                    self.transmitComplete = True
                else:
                    self.radio.setMode(RadioMode.sleep)
                    
            else:
                if (self.receiveComplete == True):
                    self.radio.setMode(RadioMode.sleep)
                elif (adminTime >= self.rxReadTime):
                    self.radio.setMode(RadioMode.receive) # set radio mode
                    self.receiveComplete = self.readMsgs()
                    if (self.receiveComplete):    
                        #print("Node " + str(self.nodeParams.config.nodeId) + " - Block packet receive complete")
                        self.radio.setMode(RadioMode.sleep)
            

 
    def init(self, currentTime):
        if not self.commStartTime or not self.networkConfigConfirmed: # Mesh not initialized
            self.initComm(currentTime)
            return
        else: # Join existing mesh
            self.initMesh()
 
    def initMesh(self, currentTime=time.time()):
        """Initialize node mesh networks."""
        # Create tdma comm messages
        flooredStartTime = math.floor(self.commStartTime)
        self.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(flooredStartTime), 'status': self.tdmaStatus, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['statusTxInterval'])

        self.tdmaCmds[TDMACmds['LinkStatus']] = Command(TDMACmds['LinkStatus'], {'linkStatus': self.nodeParams.linkStatus, 'nodeId': self.nodeParams.config.nodeId}, [TDMACmds['LinkStatus'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['linksTxInterval'])
        
        if self.nodeParams.config.nodeId != 0: # stop ground node from broadcasting time offset
            self.tdmaCmds[TDMACmds['TimeOffset']] = Command(TDMACmds['TimeOffset'], {'nodeStatus': self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1]}, [TDMACmds['TimeOffset'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['offsetTxInterval'])
        
        # Current network configuration message
        self.initialConfigTxTime = self.commStartTime + self.nodeParams.config.nodeId * self.nodeParams.config.commConfig['configTxInterval']
        configHash = self.nodeParams.config.calculateHash()
        config_pb = NodeConfig.toProtoBuf(self.nodeParams.config.rawConfig).SerializeToString()
        self.tdmaCmds[TDMACmds['CurrentConfig']] = Command(TDMACmds['CurrentConfig'], {'config': config_pb, 'configLength': len(config_pb), 'configHash': configHash, 'hashLength': self.nodeParams.config.hashSize}, [TDMACmds['CurrentConfig'], self.nodeParams.config.nodeId], self.maxNumSlots * self.nodeParams.config.commConfig['configTxInterval'])

        # Determine where in frame mesh network currently is
        self.syncTDMAFrame(currentTime)

        self.inited = True
        print("Node " + str(self.nodeParams.config.nodeId) + " - Initializing comm")
        
    def initComm(self, currentTime):
        if self.initStartTime == None:
            # Start mesh initialization timer
            self.initStartTime = currentTime
            print("Node " + str(self.nodeParams.config.nodeId) + " - Starting initialization timer")
            return
        elif (currentTime - self.initStartTime) >= self.initTimeToWait and not self.commStartTime:
            # Assume no existing mesh and initialize network
            self.commStartTime = math.ceil(currentTime)
            print("Node " + str(self.nodeParams.config.nodeId) + " - Initializing new mesh network")
            self.initMesh()
        else: # Wait for initialization timer to lapse
            # Turn on radios and check for comm messages
            self.checkForInit()

        # TODO - Add branch to read correct configuration from network

    def checkForInit(self):
        # Look for tdma status message
        self.radio.setMode(RadioMode.receive)
        self.readBytes(True)
        if self.radio.bytesInRxBuffer > 0:
            self.processMsgs()
            #while self.msgParser.parsedMsgs:
            #    msg = self.msgParser.parsedMsgs.pop(0)
            #    cmdId = struct.unpack('=B',msg[0:1])[0]
            #    if cmdId == TDMACmds['MeshStatus']:
            #        print("Mesh status received")
            #        self.processMsg(msg, {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self, 'clock': self.nodeParams.clock})  
    
    def syncTDMAFrame(self, currentTime=time.time()):
        """Determine where in frame mesh network currently is to ensure time sync."""
        self.frameTime = (currentTime - self.commStartTime)%self.frameLength
        self.frameStartTime = currentTime - self.frameTime
        self.frameCount = math.floor(currentTime - self.commStartTime) / self.frameLength
        #print("Node " + str(self.nodeParams.config.nodeId) + " " + str(self.frameStartTime),"- Frame start") 
        
        # Update periodic mesh messages
        if (TDMACmds['MeshStatus'] in self.tdmaCmds):
            self.tdmaCmds[TDMACmds['MeshStatus']].cmdData['status'] = self.tdmaStatus
            self.tdmaCmds[TDMACmds['MeshStatus']].cmdData['configHash'] = self.nodeParams.config.calculateHash()
        if (TDMACmds['LinkStatus'] in self.tdmaCmds):
            self.tdmaCmds[TDMACmds['LinkStatus']].cmdData['linkStatus'] = self.nodeParams.linkStatus
                
        # Reset buffer read position
        self.rxBufferReadPos = 0

        # Check for tdma failsafe
        self.checkTimeOffset()
    
    def sleep(self):
        """Sleep until end of frame."""
        #print("Node " + str(self.nodeParams.config.nodeId) + " - In sleep method.")
    
        # Update mesh paths
        if ((self.nodeParams.clock.getTime() - self.lastGraphUpdate) > self.nodeParams.config.commConfig['linksTxInterval']):
            self.updateShortestPaths()

        # Process any received messages
        self.processMsgs()

        # Update block transmit status
        if (self.blockTxInProgress):
            # Process block transmit receipts
            if (self.blockTx.srcId == self.nodeParams.config.nodeId):
                self.processBlockTxReceipts()
            
            self.updateBlockTxStatus()


        # Sleep until next frame to save CPU usage
        remainingFrameTime = (self.frameLength - (self.nodeParams.clock.getTime() - self.frameStartTime))
        if (remainingFrameTime > 0.010):
            # Sleep remaining frame length minus some delta to ensure waking in time
            time.sleep(remainingFrameTime - 0.010) 
        elif (remainingFrameTime < -0.010):
            print("WARNING: Frame length exceeded! Exceedance- " + str(abs(remainingFrameTime)))
            self.frameExceedanceCount += 1 
    
    def updateShortestPaths(self):
        for node in range(self.maxNumSlots):
            self.meshPaths[node] = findShortestPaths(self.maxNumSlots, self.nodeParams.linkStatus, node+1)
            # Populate direct mesh network neightbors list for this node
            if (node+1 == self.nodeParams.config.nodeId):
                for paths in self.meshPaths[node]:
                    for path in paths:
                        if (len(path) > 1): # path exists
                           if (path[1] not in self.neighbors): # new neighbor
                                self.neighbors.append(path[1])  
    
        #print("Node", self.nodeParams.config.nodeId, "- Direct neighbors:", str(self.neighbors)) 
        

    def updateMode(self, frameTime):
        # Update slot
        self.resetTDMASlot(frameTime)

        # Check for TDMA failsafe
        if (self.tdmaFailsafe == True):
            self.setTDMAMode(TDMAMode.failsafe)
            return
        
        if (frameTime >= self.cycleLength): # Cycle complete
            if (self.adminEnabled and frameTime < (self.cycleLength + self.adminLength)): # admin period
                self.setTDMAMode(TDMAMode.admin)
            else: # sleep period
                self.setTDMAMode(TDMAMode.sleep)
                #print str(frameTime) + " - Cycle complete, sleeping"
            return

        # Normal cycle sequence
        if self.slotTime < self.enableLength: # Initialize comm at start of slot
            self.setTDMAMode(TDMAMode.init)
        else:
            # Transmit slot
            if self.slotNum == self.transmitSlot:
                if self.slotTime >= self.beginTxTime: 
                    if self.slotTime < self.endTxTime: # Begin transmitting
                        self.setTDMAMode(TDMAMode.transmit)
                    else: # Sleep
                        self.setTDMAMode(TDMAMode.sleep)
                
            # Receive slot
            else:
                if self.slotTime >= self.beginRxTime: # begin receiviing
                    if self.slotTime < self.endRxTime: # receive
                        self.setTDMAMode(TDMAMode.receive)
                    else: # Sleep
                        self.setTDMAMode(TDMAMode.sleep)
        
                
    #def resetTDMASlot(self, frameTime, currentTime=time.time(), slotNum=[]):
    #def resetTDMASlot(self, frameTime, slotNum=None):
    def resetTDMASlot(self, frameTime):
        
        # Reset slot number
        #if slotNum != None:
        #    if slotNum >= 1 and slotNum <= self.maxNumSlots:
        #        self.slotNum = int(slotNum)
        #    else: # invalid number
        #        raise InvalidTDMASlotNumber("Provided TDMA slot number is not valid")
        #else:
            #if self.slotStartTime:
            #   if (currentTime - self.slotStartTime) >= self.slotLength and self.slotNum < self.maxNumSlots:
            #       self.slotNum = int(frameTime/self.slotLength) + 1   
            #else:
            if frameTime < self.cycleLength: # during cycle
                self.slotNum = int(frameTime/self.slotLength) + 1
            else: # post-cycle
                self.slotNum = self.maxNumSlots
        #self.slotStartTime = currentTime - (frameTime - (self.slotNum-1)*self.slotLength) 
        #self.slotTime = frameTime - self.slotStartTime
            self.slotStartTime = (self.slotNum-1)*self.slotLength 
            self.slotTime = frameTime - self.slotStartTime
        #print("Updating slot number: " + str(self.slotNum))
        

    def setTDMAMode(self, mode):
        if self.tdmaMode != mode:
            #print("Setting mode:", mode)
            
            self.tdmaMode = mode    
            #print str(self.slotTime) + " - TDMA mode change: " + str(self.tdmaMode)
            if mode == TDMAMode.receive:
                self.receiveComplete = False 
            elif mode == TDMAMode.transmit:
                self.transmitComplete = False 
            elif mode == TDMAMode.admin: 
                self.receiveComplete = False 
                self.transmitComplete = False 
                #print str(time.time()) + ": " + str(frameTime) + " - Node " + str(self.nodeId) + " - Transmitting"
    
    def sendMsgs(self):
        if (self.enabled == False): # Don't send anything if disabled
            return    
    
        # Send buffered and periodic commands
        broadcastMsgSent = False
        if self.tdmaMode == TDMAMode.transmit:
            # Send periodic TDMA commands
            #self.sendTDMACmds()

            # Check queue for waiting outgoing messages
            bytesSent = 0
            bytesSent += self.processBuffers() # process relay and command buffers
            for msg in self.meshQueueIn:
                packetBytes = b''

                if (bytesSent + len(msg.msgBytes) > self.nodeParams.config.commConfig['maxTransferSize']): # maximum transmit size reached
                    break 

                if (msg.destId == 0):
                    packetBytes = self.packageMeshPacket(msg.destId, msg.msgBytes)
                    broadcastMsgSent = True
                elif (msg.destId != 0 and msg.msgBytes): # only send non-zero non-broadcast messages
                    packetBytes = self.packageMeshPacket(msg.destId, msg.msgBytes)
                    
                if (packetBytes): # if packet is of non-zero length
                    self.bufferTxMsg(packetBytes)
 
            # Clear queue
            self.meshQueueIn = []

            # Send broadcast message
            if (broadcastMsgSent == False): # send a broadcast message for network administration
                if (bytesSent < self.nodeParams.config.commConfig['maxTransferSize']): # maximum transmit size not reached
                    packetBytes = self.packageMeshPacket(0, b'')
                
                    if (packetBytes): # if packet is of non-zero length
                        self.bufferTxMsg(packetBytes)

            #self.radio.bufferTxMsg(HDLC_END_TDMA) # append end of message byte
        
            #print("Node " + str(self.nodeParams.config.nodeId) + " - Number of bytes sent: " + str(len(self.radio.txBuffer)))
            self.bytesSent += self.sendBuffer() 

            # End transmit period
            self.transmitComplete = True

        else:
            pass
            #print "Slot " + str(self.slotNum) + " - Node " + str(self.nodeId) + " - Can't send. Wrong mode: " + str(self.tdmaMode)

    def packageMeshPacket(self, destId, msgBytes):
        adminBytes = b''
        if (destId == 0): # package network admin messages into broadcast message
            adminBytes = self.packageAdminData(self.nodeParams.config.commConfig['adminBytesMaxLength'])
            #adminBytes = self.sendTDMACmds()

        return self.createMeshPacket(destId, msgBytes, adminBytes, self.nodeParams.config.nodeId)

    def createMeshPacket(self, destId, msgBytes, adminBytes, sourceId, statusByte=0):

        if (len(adminBytes) == 0 and len(msgBytes) == 0): # do not send empty message
            return bytearray()

        # Create mesh packet header
        packetHeader = struct.pack(self.meshPacketHeaderFormat, sourceId, destId, len(adminBytes), len(msgBytes), self.nodeParams.get_cmdCounter(), statusByte)
        
        # Return mesh packet
        return bytearray(packetHeader + adminBytes + msgBytes)

    def parseMeshPacket(self, packetBytes):
        """Parse out a mesh packet."""
                
        # Parse mesh packet header
        packetHeader = dict()
        packetHeaderContents = struct.unpack(self.meshPacketHeaderFormat, packetBytes[0:self.meshHeaderLen])
        packetHeader = {'sourceId': packetHeaderContents[0], 'destId': packetHeaderContents[1], 'adminLength': packetHeaderContents[2], 'payloadLength': packetHeaderContents[3], 'cmdCounter': packetHeaderContents[4], 'statusByte': packetHeaderContents[5]}
                
        # Validate message length
        if (len(packetBytes) == (self.meshHeaderLen + packetHeader['adminLength'] + packetHeader['payloadLength'])): # message length is valid
            adminBytes = packetBytes[self.meshHeaderLen:self.meshHeaderLen + packetHeader['adminLength']]
            messageBytes = packetBytes[self.meshHeaderLen + packetHeader['adminLength']:]
            
            return True, packetHeader, adminBytes, messageBytes
        else:
            return False, packetHeader, [], []
        

    def readMsgs(self):
        """Read from serial connection and look for end of message value."""
        self.bytesRcvd += self.radio.readBytes(True)
       
        # Look for TDMA message end indicator 
        #for i in range(self.rxBufferReadPos, self.radio.bytesInRxBuffer):
        #    self.rxBufferReadPos = i+1
            #byte = self.rxBuffer[i:i+1]
       #     if self.radio.rxBuffer[i:i+1] == HDLC_END_TDMA: # End of transmission found
                #print("Node " + str(self.nodeParams.config.nodeId) + " - Bytes in rxBuffer: ", self.radio.bytesInRxBuffer)
       #         return True
        
        #print("Node " + str(self.nodeParams.config.nodeId) + " - Bytes in rxBuffer: ", self.radio.bytesInRxBuffer)

        return False # end of transmission not found
   
    def relayMsg(self, msgBytes):
        """Relay received message. Existing mesh header is maintained with only the source updated."""
        packetHeader = struct.unpack(self.meshPacketHeaderFormat, msgBytes[0:self.meshHeaderLen])
        sourceId = packetHeader[0]
        destId = packetHeader[1]
        adminLength = packetHeader[2]    
        payloadLength = packetHeader[3]
        cmdCounter = packetHeader[4]
        statusByte = packetHeader[5]
        #print("Node " + str(self.nodeParams.config.nodeId) + " relaying message from " + str(sourceId) + " - " + str(cmdCounter))

        # Update packet sourceId
        msgBytes[0:1] = struct.pack('<B', self.nodeParams.config.nodeId)        

        # Store in buffer for relay
        self.cmdRelayBuffer += self.msgParser.encodeMsg(msgBytes)
 
    def processMsgs(self):
        """Processes parsed mesh network messages. Raw data bytes are then stored for forwarding to the node host for processing."""
            
        # Parse any received bytes
        self.parseMsgs()

        # Process any received messages
        if (self.msgParser.parsedMsgs):
            for i in range(len(self.msgParser.parsedMsgs)):
                msg = self.msgParser.parsedMsgs.pop(0)
                
                # Parse mesh packet header
                packetValid, packetHeader, adminBytes, messageBytes = self.parseMeshPacket(msg)
                if (packetValid == False): # packet invalid
                    continue                

                # Ignore stale commands
                if (packetHeader['cmdCounter'] in self.nodeParams.cmdHistory):
                    continue
                else:
                    self.nodeParams.cmdHistory.append(packetHeader['cmdCounter']) # update command history

                # Update information on direct mesh links based on sourceId
                self.nodeParams.nodeStatus[packetHeader['sourceId']-1].present = True
                self.nodeParams.nodeStatus[packetHeader['sourceId']-1].lastMsgRcvdTime = self.nodeParams.clock.getTime()

                # Extract any mesh messages and process
                if (packetHeader['adminLength'] > 0):
                    self.processMeshMsgs(adminBytes)
   
                # Place raw message bytes in buffer to send to host
                if (packetHeader['payloadLength'] > 0):
                    if (packetHeader['destId'] == self.nodeParams.config.nodeId or self.nodeParams.config.commConfig['recvAllMsgs']):
                        #print("Placing in hostBuffer: " + str(msg[self.meshHeaderLen + adminLength:]))
                        self.hostBuffer += messageBytes
       
                # Check for relay
                if (self.inited == False): # don't process for relaying if mesh not inited
                    continue
 
                if (packetHeader['destId'] == 0):
                    if (packetHeader['statusByte'] != BLOCK_TX_MSG): # broadcast message (don't relay block tx packets)
                        # All broadcast messages are relayed
                        self.relayMsg(bytearray(msg))

                elif (packetHeader['destId'] != self.nodeParams.config.nodeId): # message for another node
                    # Only relay if on the shortest path
                    if (self.checkForRelay(self.nodeParams.config.nodeId, packetHeader['destId'], packetHeader['sourceId']) == True): # message should be relayed
                        self.relayMsg(bytearray(msg))
                else:
                    pass
       
    def checkForRelay(self, currentNode, destId, sourceId):
        """This method checks if a message should be relayed based on the current mesh graph."""
        # No relay if this is the destination
        if (currentNode == destId):
            return False
        
        try:
            lenPathToSource = len(self.meshPaths[currentNode-1][sourceId-1][0]) - 1            
            lenPathToDest = len(self.meshPaths[currentNode-1][destId-1][0]) - 1           
            lenSourceToDest = len(self.meshPaths[sourceId-1][destId-1][0]) - 1

            # Relay if the total path through this node to destination is equal to or less than shortest path from the source
            if (lenSourceToDest >= (lenPathToDest + lenPathToSource)):
                return True
            else:
                return False

        except IndexError:
            # Path data not available (may not have been updated yet)
            return True

    def processMeshMsgs(self, meshMsgs):
        """Processes mesh network administration commands and messages received."""
        # Process any mesh commands
        if (len(meshMsgs) > 0):
            # Parse and process individual commands
            self.tdmaCmdParser.parseMsgs(meshMsgs)
            for i in range(len(self.tdmaCmdParser.parsedMsgs)):
                self.processMsg(self.tdmaCmdParser.parsedMsgs.pop(0), {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self, 'clock': self.nodeParams.clock})  

    def packageAdminData(self, maxLength):
        adminBytes = b''
        
        # Send command responses
        #for resp in self.nodeParams.cmdResponse:
        #    cmd = Command(NodeCmds['CmdResponse'], resp, [NodeCmds['CmdResponse'], self.nodeParams.config.nodeId])
        #    adminBytes += self.tdmaCmdParser.encodeMsg(cmd.serialize(self.nodeParams.clock.getTime()))
            
        # Send TDMA commands
        adminBytes += self.sendTDMACmds(maxLength)

        return adminBytes

    def sendTDMACmds(self, maxLength):
        tdmaCmdBytes = b''    
        # Send TDMA messages
        timestamp = self.nodeParams.clock.getTime()
        for cmdId in list(self.tdmaCmds.keys()):
            cmd = self.tdmaCmds[cmdId]
            
            # Check for admin period only commands
            adminCmds = [TDMACmds['CurrentConfig'], TDMACmds['ConfigUpdate']]
            if (cmdId in adminCmds and self.tdmaMode != TDMAMode.admin): # do not send admin only commands
                continue
            # Delay config transmission (initial delay upon mesh startup)
            if (cmdId == TDMACmds['CurrentConfig'] and timestamp < self.initialConfigTxTime):
                continue
   
            # Check for polling commands (need to be processed by sender)
            if (cmdId in [TDMACmds['NetworkRestart'], TDMACmds['ConfigUpdate'], TDMACmds['BlockTxRequest']]):
                TDMACmdProcessor['msgProcessor'](self, cmdId, {'cmdId': cmd.cmdId, 'sourceId': self.nodeParams.config.nodeId, 'cmdCounter': cmd.header['header']['cmdCounter']}, cmd.serialize(timestamp), {'nodeStatus': self.nodeParams.nodeStatus, 'clock': self.nodeParams.clock, 'comm': self})
                #self.networkMsgQueue.append({"header": {"cmdId": cmd.cmdId, "sourceId": self.nodeParams.config.nodeId, "cmdCounter": cmd.cmdCounter}, "msgContents": cmd.cmdData})
            #elif (cmdId == TDMACmds['ConfigUpdate']):
            #    self.networkMsgQueue.append({"header": {"cmdId": cmd.cmdId, "sourceId": self.nodeParams.config.nodeId, "cmdCounter": cmd.cmdCounter}, "msgContents": {"valid": True, "destId": cmd.cmdData['destId']}})

            # Update command counter
            if ('cmdCounter' in cmd.header):
                cmd.header['cmdCounter'] = self.nodeParams.get_cmdCounter()

            # Send periodic commands at prescribed interval
            msgBytes = b''
            if cmd.txInterval:
                if ceil(timestamp*100)/100.0 >= ceil((cmd.lastTxTime + cmd.txInterval)*100)/100.0: # only compare down to milliseconds
                    #self.bufferTxMsg(cmd.serialize(timestamp))
                    msgBytes = self.tdmaCmdParser.encodeMsg(cmd.serialize(timestamp))
                    #print("Node", self.nodeParams.config.nodeId, "- Sending periodic command:", cmd.cmdId) 
                    #tdmaCmdBytes += self.tdmaCmdParser.encodeMsg(cmd.serialize(timestamp))
            else: # non-periodic command
                #self.bufferTxMsg(cmd.serialize(timestamp))
                msgBytes = self.tdmaCmdParser.encodeMsg(cmd.serialize(timestamp))
                #tdmaCmdBytes += self.tdmaCmdParser.encodeMsg(cmd.serialize(timestamp))
                
            # Check for alotted size overflow    
            if (msgBytes and (len(tdmaCmdBytes) + len(msgBytes) <= maxLength)): # append to outgoing bytes
                tdmaCmdBytes += msgBytes
                if (cmdId == TDMACmds['CurrentConfig']):
                    print("Node " + str(self.nodeParams.config.nodeId) + " Sending CurrentConfig message.")
                if (cmd.txInterval): # update last transmit time
                    cmd.lastTxTime = timestamp
                else: # remove single-time command
                    del self.tdmaCmds[cmdId]

        return tdmaCmdBytes
                                

    def startBlockTx(self, reqId, destId, srcId, startTime, length, blockData=None):
        if (self.blockTxInProgress == True): # reject new block tx because one already in progress
            return False    

        # Store block transfer details
        endTime = startTime + int(length*self.frameLength*self.nodeParams.config.commConfig['blockTxEndMult'])
        self.blockTx = BlockTx(reqId, length, srcId, destId, startTime, endTime, blockData)
        self.blockTxInProgress = True

        print("Node", self.nodeParams.config.nodeId, "- Starting block transmit, length-", self.blockTx.length)

        return True

    def sendBlockTxPacket(self):
        """Send next block transmit packet."""

        # Check for missed packets
        packetsToRemove = []
        repeatPacket = None
        #for entry in range(len(self.blockTxPacketStatus)):
        for entry in self.blockTxPacketStatus.keys():
            status = self.blockTxPacketStatus[entry]
            status.framesSinceTx += 1
            
            # Check for responses from all directly connected nodes
            allResponsesRcvd = True
            for node in self.neighbors:
                if (node not in status.responsesRcvd): # response not received from this node
                    allResponsesRcvd = False
                    break
        
            # Check packet status
            #print("Responses received, framesSinceTx:", allResponsesRcvd, status.framesSinceTx)
            if (allResponsesRcvd == True): # packet successfully sent
                print("Node", self.nodeParams.config.nodeId, "- All responses received for block tx packet", status.packetNum)
                packetsToRemove.append(entry)
            elif (allResponsesRcvd == False and status.framesSinceTx >= self.nodeParams.config.commConfig['blockTxReceiptTimeout']): # resend packet
                status.framesSinceTx = 0 # reset frame counter
                status.retries += 1
                repeatPacket = status.packet
                if (status.retries >= self.nodeParams.config.commConfig['blockTxPacketRetry']): # Retry limit met, remove packet from status list
                    packetsToRemove.append(entry)
                break
     
        # Remove entries from packet status list
        #self.blockTxPacketStatus = [self.blockTxPacketStatus[entry] for entry in range(len(self.blockTxStatus)) if entry not in packetsToRemove] 
        for entry in packetsToRemove:
            del self.blockTxPacketStatus[entry]
        
        # Check for packet to resend
        if (repeatPacket): # packet to resend
            print("Node " + str(self.nodeParams.config.nodeId) + " - Resending block transmit packet")
            return repeatPacket

        ## Send next increment of block data
        newPacket = self.getBlockTxPacket()
        
        if (newPacket != None): # data to send
            # Add new packet to status list
            self.blockTxPacketStatus[self.blockTx.packetNum] = BlockTxPacketStatus(newPacket, self.blockTx.packetNum)
        elif (len(self.blockTxPacketStatus) == 0): # Check for block transmit completion (all packets sent successfully)
            self.blockTx.complete = True

        return newPacket

    
    def getBlockTxPacket(self):
        # Check for block data
        #if (self.blockTxData == None): # no data to send
        #    return None

        # Create mesh packet from next chunk of block data
        if (self.blockTx.dataLoc >= len(self.blockTx.data)): # no packets remaining
            return None
        elif (len(self.blockTx.data) > self.blockTx.dataLoc + self.nodeParams.config.commConfig['blockTxPacketSize']): 
            newBlockTxDataLoc = self.blockTx.dataLoc + int(self.nodeParams.config.commConfig['blockTxPacketSize'])
            blockDataChunk = self.blockTx.data[self.blockTx.dataLoc:newBlockTxDataLoc]
            self.blockTx.dataLoc = newBlockTxDataLoc
        else: # send remainder of data block
            blockDataChunk = self.blockTx.data[self.blockTx.dataLoc:]
            self.blockTx.dataLoc = len(self.blockTx.data) # reached end of data block
       
        # Generate new packet command
        self.blockTx.packetNum += 1
        blockDataCmd = Command(TDMACmds['BlockData'], {'blockReqId': self.blockTx.reqId, 'packetNum': self.blockTx.packetNum, 'dataLength': len(blockDataChunk), 'data': blockDataChunk}, [TDMACmds['BlockData'], self.nodeParams.config.nodeId])
        blockDataSerialized = self.tdmaCmdParser.encodeMsg(blockDataCmd.serialize(self.nodeParams.clock.getTime()))
 
        blockPacket = self.createMeshPacket(self.blockTx.destId, b'', blockDataSerialized, self.nodeParams.config.nodeId, BLOCK_TX_MSG)
                    
        print("Node " + str(self.nodeParams.config.nodeId) + " - Sending block transmit packet", self.blockTx.packetNum, ". Length-", len(blockPacket))

        return blockPacket

    def processBlockTxReceipts(self):
        # Update block tx packet receipt status
        for receipt in self.blockTxPacketReceipts:
            if (receipt['blockReqId'] == self.blockTx.reqId and receipt['packetNum'] in self.blockTxPacketStatus):
                if (receipt['sourceId'] not in self.blockTxPacketStatus[receipt['packetNum']].responsesRcvd):
                    self.blockTxPacketStatus[receipt['packetNum']].responsesRcvd.append(receipt['sourceId'])

        self.blockTxPacketReceipts = []
            
    def updateBlockTxStatus(self):
        # Monitor for block transmit end
        if (self.blockTx.complete or self.nodeParams.clock.getTime() >= self.blockTx.endTime): # block transmit ended
            if (self.blockTx.srcId == self.nodeParams.config.nodeId): # sender end block tx
                # Send block transmit end message
                self.tdmaCmds[TDMACmds['BlockTxRequest']] = Command(TDMACmds['BlockTxRequest'], {'blockReqId': self.blockTx.reqId, 'destId': self.blockTx.destId, 'startTime': self.blockTx.startTime, 'length': self.blockTx.length, 'status': 0}, [TDMACmds['BlockTxRequest'], self.nodeParams.config.nodeId, self.nodeParams.get_cmdCounter()])
    
            # End block transmit
            self.endBlockTx()
    
    def endBlockTx(self):
        print("Node", self.nodeParams.config.nodeId, "- Concluding block transmit.")

        # Assemble and pass data block to host
        if (self.blockTx.srcId != self.nodeParams.config.nodeId and self.blockTx.destId in [0, self.nodeParams.config.nodeId]): # pass block transmit data to host
            self.blockTxOut = {'dataComplete': self.blockTx.dataComplete, 'data': self.blockTx.getData()}
            
            if (len(self.blockTxOut['data']) > 0):
                print("Node", self.nodeParams.config.nodeId, "- Sending block tx data to host, length:", len(self.blockTxOut['data']))

        # Check for need to relay - TODO - implement logic for relaying block tx to destination node

        # Clear block transmit parameters
        self.blockTx = None
        self.blockTxInProgress = False
        self.blockTxPacketStatus = dict() # stores transmitted packet status until all receipt requests received
        self.blockTxPacketReceipts = []

    def checkTimeOffset(self, offset=None):
        if offset == None: # offset not provided so attempt to get offset from clock
            offset = self.nodeParams.clock.getOffset()

        if offset != None: # time offset available
            self.timeOffsetTimer = None # reset time offset timer
            self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1].timeOffset = offset
            if abs(self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1].timeOffset) > self.nodeParams.config.commConfig['operateSyncBound']:
                return 1
        else: # no offset available
            self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1].timeOffset = 127 # Error value
            # Check time offset timer
            if self.timeOffsetTimer:
                #print(self.clock.getTime() - self.timeOffsetTimer)
                if self.nodeParams.clock.getTime() - self.timeOffsetTimer > self.nodeParams.config.commConfig['offsetTimeout']: # No time offset reading for longer than allowed
                    self.tdmaFailsafe = True # Set TDMA failsafe flag
                    return 2
            else: # start timer
                self.timeOffsetTimer = self.nodeParams.clock.getTime()
                    
        return 0
