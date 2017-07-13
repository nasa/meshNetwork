from mesh.generic.nodeComm import NodeComm
from switch import switch
import random, time, math
from math import ceil
from mesh.generic.slipMsg import SLIP_END_TDMA
from mesh.generic.radio import RadioMode
from mesh.generic.cmds import TDMACmds
from mesh.generic.tdmaState import TDMAStatus, TDMAMode, TDMABlockTxStatus
from mesh.generic.cmdDict import CmdDict
from mesh.generic.command import Command
from mesh.generic.customExceptions import InvalidTDMASlotNumber
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
import struct

class TDMAComm(NodeComm):
    def __init__(self, commProcessor, radio, msgParser, nodeParams):
        if not commProcessor:
            commProcessor = CommProcessor([TDMACmdProcessor], nodeParams)

        NodeComm.__init__(self, commProcessor, radio, msgParser, nodeParams)        

        # TDMA config       
        self.tdmaMode = TDMAMode.sleep
        self.frameStartTime = []
        self.nodeParams.commStartTime = [] # time that TDMA comm was started - initialized manually by first node or parsed from messages received for nodes joining existing mesh
        self.maxNumSlots = nodeParams.config.commConfig['maxNumSlots'] # Maximum number of slots
        self.enableLength = nodeParams.config.commConfig['enableLength']
        self.slotTime = 0.0
        self.slotNum = 1        
        self.slotStartTime = 0.0
    
        # TDMA Frame variables
        self.frameTime = 0.0
        self.frameLength = nodeParams.config.commConfig['frameLength']
        self.cycleLength = nodeParams.config.commConfig['cycleLength']
        
        # Mesh initialization variables
        self.inited = False
        self.initTimeToWait = nodeParams.config.commConfig['initTimeToWait'] # Time to wait before assuming no existing mesh network
        self.initStartTime = []
        
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

        # Command buffer
        self.cmdBuffer = dict()

        # Current read position in radio rx buffer
        self.rxBufferReadPos = 0

        # Block TX init
        self.resetBlockTxStatus()
        self.clearDataBlock()

        # Comm enable flag
        self.enabled = True

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

        if self.frameTime < self.cycleLength: 
            frameStatus = 0
        else: # sleep period
            frameStatus = 1
    
        return frameStatus

    def executeTDMAComm(self, currentTime):
        """Execute TDMA communication scheme."""
        # Check for block transfers
        self.monitorBlockTx()
        
        # Update frame time
        frameStatus = self.updateFrameTime(currentTime)
        if (frameStatus == 1):
            self.sleep()
            return

        # Check for mode updates
        self.updateMode(self.frameTime)
    
        # Perform mode specific behavior
        for case in switch(self.tdmaMode):
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
                    pass
                break
            if case(TDMAMode.receive):
                # Read data if TDMA message end not yet found
                if self.receiveComplete == False and self.slotTime >= self.rxReadTime:
                    self.radio.setMode(RadioMode.receive) # set radio mode
                    # Delay so we aren't hammering the radio
                    #remainingRxTime = self.rxLength - (self.slotTime - self.enableLength)
                    #time.sleep(remainingRxTime*0.2)                        
                    self.receiveComplete = self.readMsg()
                    if self.receiveComplete == True: 
                        # Set radio to sleep
                        self.radio.setMode(RadioMode.sleep)
                break
            if case(TDMAMode.transmit):
                # Send data
                if self.transmitComplete == False:
                    self.radio.setMode(RadioMode.transmit) # set radio mode
                    self.sendMsg()
                else: # Set radio to sleep
                    self.radio.setMode(RadioMode.sleep)
                break
            if case(TDMAMode.failsafe): # Read only failsafe mode
                # Enable radio in receive mode and read data
                self.radio.setMode(RadioMode.receive)
                self.readMsg()
                break
            if case(TDMAMode.blockRx): # Block receive mode
                self.radio.setMode(RadioMode.receive)
                self.readMsg()
                break
            if case(TDMAMode.blockTx): # Block transmit mode
                self.radio.setMode(RadioMode.transmit)
                self.sendBlock()
                break
    
    def init(self, currentTime):
        if self.nodeParams.commStartTime == []: # Mesh not initialized
            self.initComm(currentTime)
            return
        else: # Join existing mesh
            self.initMesh()
 
    def initMesh(self, currentTime=time.time()):
        """Initialize node mesh networks."""
        # Create tdma comm messages
        self.tdmaCmds = dict()
        flooredStartTime = math.floor(self.nodeParams.commStartTime)
        self.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(flooredStartTime), 'status': self.nodeParams.tdmaStatus}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['statusTxInterval'])
        self.tdmaCmds[TDMACmds['LinkStatus']] = Command(TDMACmds['LinkStatus'], {'linkStatus': self.nodeParams.linkStatus, 'nodeId': self.nodeParams.config.nodeId}, [TDMACmds['LinkStatus'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['linksTxInterval'])
        
        if self.nodeParams.config.nodeId != 0: # stop ground node from broadcasting time offset
            self.tdmaCmds[TDMACmds['TimeOffset']] = Command(TDMACmds['TimeOffset'], {'nodeStatus': self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1]}, [TDMACmds['TimeOffset'], self.nodeParams.config.nodeId], self.nodeParams.config.commConfig['offsetTxInterval'])
        
        # Determine where in frame mesh network currently is
        self.syncTDMAFrame(currentTime)

        self.inited = True
        print("Node " + str(self.nodeParams.config.nodeId) + " - Initializing comm")
    
    def initComm(self, currentTime):
        if self.initStartTime == []:
            # Start mesh initialization timer
            self.initStartTime = currentTime
            print("Node " + str(self.nodeParams.config.nodeId) + " - Starting initialization timer")
            return
        elif (currentTime - self.initStartTime) >= self.initTimeToWait:
            # Assume no existing mesh and initialize network
            self.nodeParams.commStartTime = math.ceil(currentTime)
            print("Initializing new mesh network")
            self.initMesh()
        else: # Wait for initialization timer to lapse
            # Turn on radios and check for comm messages
            self.checkForInit()

    def checkForInit(self):
        # Look for tdma status message
        self.radio.setMode(RadioMode.receive)
        self.readBytes(True)
        if self.radio.bytesInRxBuffer > 0:
            self.parseMsgs()
            while self.msgParser.parsedMsgs:
                msg = self.msgParser.parsedMsgs.pop(0)
                cmdId = struct.unpack('=B',msg[0:1])[0]
                if cmdId == TDMACmds['MeshStatus']:
                    self.processMsg(msg, {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self, 'clock': self.nodeParams.clock})  
    
    def syncTDMAFrame(self, currentTime=time.time()):
        """Determine where in frame mesh network currently is to ensure time sync."""
        self.frameTime = (currentTime - self.nodeParams.commStartTime)%self.frameLength
        self.frameStartTime = currentTime - self.frameTime
        print(str(self.frameStartTime),"- Frame start") 
        
        # Update periodic mesh messages
        self.tdmaCmds[TDMACmds['MeshStatus']].cmdData['status'] = self.nodeParams.tdmaStatus
                
        # Reset buffer read position
        self.rxBufferReadPos = 0

        # Check for tdma failsafe
        self.nodeParams.checkTimeOffset()
    
    def sleep(self):
        """Sleep until end of frame."""
        # Sleep until next frame to save CPU usage
        try: # wrap in try in case of negative sleep time
            # Sleep remaining frame length minus some delta to ensure waking in time
            remainingFrameTime = (self.frameLength - (time.time() - self.frameStartTime))
            if remainingFrameTime > 0.010:
                time.sleep(remainingFrameTime - 0.010)  
        except ValueError:
            print("WARNING: Frame length exceeded")
    
    def updateMode(self, frameTime):
        # Update slot
        self.resetTDMASlot(frameTime)

        # Check for TDMA failsafe
        if self.nodeParams.tdmaFailsafe == True:
            self.setTDMAMode(TDMAMode.failsafe)
            return
        
        if frameTime >= self.cycleLength: # Cycle complete
            self.setTDMAMode(TDMAMode.sleep)
            #print str(frameTime) + " - Cycle complete, sleeping"
            return

        # Check for block transmit
        if self.blockTxStatus['status'] == TDMABlockTxStatus.active:
            if self.blockTxStatus['txNode'] == self.nodeParams.config.nodeId: # this node is transmitting
                self.setTDMAMode(TDMAMode.blockTx)
            else: # this node is receiving
                self.setTDMAMode(TDMAMode.blockRx)
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
                if self.slotTime >= self.beginRxTime:
                    if self.slotTime < self.endRxTime: # Begin receiving
                        self.setTDMAMode(TDMAMode.receive)
                    else: # Sleep
                        self.setTDMAMode(TDMAMode.sleep)
        
                
    #def resetTDMASlot(self, frameTime, currentTime=time.time(), slotNum=[]):
    def resetTDMASlot(self, frameTime, slotNum=[]):
        
        # Reset slot number
        if slotNum:
            if isinstance(slotNum, int) and slotNum <= self.maxNumSlots:
                self.slotNum = slotNum
            else: # invalid number
                raise InvalidTDMASlotNumber("Provided TDMA slot number is not valid")
        else:
            #if self.slotStartTime:
            #   if (currentTime - self.slotStartTime) >= self.slotLength and self.slotNum < self.maxNumSlots:
            #       self.slotNum = int(frameTime/self.slotLength) + 1   
            #else:
            if frameTime < self.cycleLength: # during cycle
                self.slotNum = int(frameTime/self.slotLength) + 1
            else: # during sleep period
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
                #print str(time.time()) + ": " + str(frameTime) + " - Node " + str(self.nodeId) + " - Transmitting"
    
            
    def sendMsg(self):
        if (self.enabled == False): # Don't send anything if disabled
            return    
    
        # Send periodic TDMA commands
        self.sendTDMACmds()

        if self.tdmaMode == TDMAMode.transmit:
            if self.cmdBuffer: # command buffer
                noRepeatCmds = []
                for key in self.cmdBuffer:
                    self.bufferTxMsg(self.cmdBuffer[key]['bytes'])
                    if self.cmdBuffer[key]['txInterval'] == 0: # no repeat
                        noRepeatCmds.append(key)
                for key in noRepeatCmds: # remove non-repeat commands
                    self.cmdBuffer.pop(key)
                
            if self.cmdRelayBuffer: # Add commands to tx buffer and clear relay buffer
                #for cmd in cmdRelayBuffer:
                #    self.bufferTxMsg(cmd)
                self.radio.bufferTxMsg(self.cmdRelayBuffer)
                self.cmdRelayBuffer = bytearray()
            self.radio.bufferTxMsg(SLIP_END_TDMA)
            self.radio.sendBuffer(self.nodeParams.config.commConfig['maxTransferSize'])
                
            # End transmit period
            self.transmitComplete = True

        else:
            pass
            #print "Slot " + str(self.slotNum) + " - Node " + str(self.nodeId) + " - Can't send. Wrong mode: " + str(self.tdmaMode)

    def sendBlock(self):
        if self.dataBlock:
            if len(self.dataBlock[self.dataBlockPos:]) > self.nodeParams.config.commConfig['maxBlockTransferSize']: # buffer portion of data block
                blockDataCmd = Command(TDMACmds['BlockData'], {'data': self.dataBlock[self.dataBlockPos:self.dataBlockPos + self.nodeParams.config.commConfig['maxBlockTransferSize']]}, [TDMACmds['BlockData'], self.nodeParams.config.nodeId]).serialize(self.nodeParams.clock.getTime())
                self.dataBlockPos += self.nodeParams.config.commConfig['maxBlockTransferSize']
            else: # send entire data block
                blockDataCmd = Command(TDMACmds['BlockData'], {'data': self.dataBlock[self.dataBlockPos:]}, [TDMACmds['BlockData'], self.nodeParams.config.nodeId]).serialize(self.nodeParams.clock.getTime())
                self.clearDataBlock() # clear stored data block
                self.blockTxStatus['blockTxComplete'] = True # end block transfer
            
            # Send block data
            self.radio.bufferTxMsg(blockDataCmd)
            self.radio.bufferTxMsg(SLIP_END_TDMA)
            self.radio.sendBuffer(self.nodeParams.config.commConfig['maxBlockTransferSize'])
        
        else: # end block transfer - no data to send
            self.blockTxStatus['blockTxComplete'] = True

    def readMsg(self):
        """Read from serial connection and look for end of message value."""
        self.radio.readBytes(True)
        for i in range(self.rxBufferReadPos, self.radio.bytesInRxBuffer):
            self.rxBufferReadPos = i+1
            #byte = self.rxBuffer[i:i+1]
            if self.radio.rxBuffer[i:i+1] == SLIP_END_TDMA: # End of transmission found
                return True
        
        return False # end of transmission not found
    
    def sendTDMACmds(self):
        # Send TDMA messages
        timestamp = self.nodeParams.clock.getTime()
        for cmdId in list(self.tdmaCmds.keys()):
            cmd = self.tdmaCmds[cmdId]
            if ceil(timestamp*100)/100.0 >= ceil((cmd.lastTxTime + cmd.txInterval)*100)/100.0: # only compare down to milliseconds
                self.bufferTxMsg(cmd.serialize(timestamp))
                
    def resetBlockTxStatus(self):
        """Clears block transmit status."""
        self.blockTxStatus = {'status': TDMABlockTxStatus.false, 'txNode': None, 'startTime': None, 'length': None, 'blockResponseList': {}, 'blockReqID': None, 'requestTime': None, 'blockTxComplete': False}
        self.nodeParams.tdmaStatus = TDMAStatus.nominal

    def monitorBlockTx(self):
        """Monitors current status of block transmit."""
        if self.blockTxStatus['status'] == TDMABlockTxStatus.false:
            return

        elif self.blockTxStatus['status'] == TDMABlockTxStatus.pending: # monitor pending block request
            if self.blockTxStatus['txNode'] == self.nodeParams.config.nodeId: # this node requested block tx
                # Check block request responses
                response = self.checkBlockResponse()
                if response == True:
                    # Confirm block tx
                    blockConfirmCmd = Command(TDMACmds['BlockTxConfirmed'], {'blockReqID': self.blockTxStatus['blockReqID']}, [TDMACmds['BlockTxConfirmed'], self.nodeParams.config.nodeId, self.nodeParams.get_cmdCounter()])
                    self.radio.bufferTxMsg(blockConfirmCmd.serialize(self.nodeParams.clock.getTime()))
                    self.blockTxStatus['status'] = TDMABlockTxStatus.confirmed              
                    return

                elif response == False:
                    # Cancel request
                    self.resetBlockTxStatus()
                    return

                # Check for request timeout
                if (self.frameStartTime - self.blockTxStatus['requestTime']) > self.nodeParams.config.commConfig['blockTxRequestTimeout'] * self.nodeParams.config.commConfig['frameLength']:
                    # Request timed out - reset status
                    self.resetBlockTxStatus()
                    return
            if self.frameStartTime >= self.blockTxStatus['startTime']: # no block confirmed received
                # Cancel pending block
                self.resetBlockTxStatus()
                return
        
        elif self.blockTxStatus['status'] == TDMABlockTxStatus.confirmed: 
            # Check for block start
            if self.frameStartTime >= self.blockTxStatus['startTime']: # start block
                self.blockTxStatus['status'] = TDMABlockTxStatus.active
                self.nodeParams.tdmaStatus = TDMAStatus.blockTx
        
            # Send block transmit status message
            if self.blockTxStatus['txNode'] == self.nodeParams.config.nodeId:
                blockStatusCmd = Command(TDMACmds['BlockTxStatus'], {'blockReqID': self.blockTxStatus['blockReqID'], 'startTime': self.blockTxStatus['startTime'], 'length': self.blockTxStatus['length']}, [TDMACmds['BlockTxStatus'], self.nodeParams.config.nodeId, self.nodeParams.get_cmdCounter()])
                self.radio.bufferTxMsg(blockStatusCmd.serialize(self.nodeParams.clock.getTime()))
    
        elif self.blockTxStatus['status'] == TDMABlockTxStatus.active: # block transmit in progress
            # Check for end of block transmit
            if self.blockTxStatus['blockTxComplete'] or (self.frameStartTime - self.blockTxStatus['startTime']) >= self.blockTxStatus['length']*self.nodeParams.config.commConfig['frameLength'] or self.nodeParams.tdmaStatus == TDMAStatus.nominal:
                # Block transmit ended - reset status
                self.resetBlockTxStatus()

    def clearDataBlock(self):
        """Clear data stored for block transfer."""
        self.dataBlock = bytearray()
        self.dataBlockPos = 0

    def sendDataBlock(self, dataBlock):
        """Begins block transfer process."""
        
        # Calculate block tx parameters
        length = int(ceil(len(dataBlock) / self.nodeParams.config.commConfig['maxBlockTransferSize']))
        if length > self.nodeParams.config.commConfig['maxTxBlockSize']:
            # Too much data to transmit
            return False
        
        startTime = int(self.frameStartTime + self.nodeParams.config.commConfig['frameLength'] * self.nodeParams.config.commConfig['minBlockTxDelay'])
        
        # Store data block
        self.dataBlock = dataBlock
    
        # Populate response list
        self.populateBlockResponseList()

        # Send block tx request
        blockReqID = random.randint(1,255) # just a random "unique" number 
        blockTxCmd = Command(TDMACmds['BlockTxRequest'], {'blockReqID': blockReqID, 'startTime': startTime, 'length': length}, [TDMACmds['BlockTxRequest'], self.nodeParams.config.nodeId, self.nodeParams.get_cmdCounter()])
        self.bufferTxMsg(blockTxCmd.serialize(self.nodeParams.clock.getTime()))
    
        # Update blockTxStatus
        self.blockTxStatus['blockReqID'] = blockReqID
        self.blockTxStatus['startTime'] = startTime
        self.blockTxStatus['length'] = length
        self.blockTxStatus['requestTime'] = self.frameStartTime
        self.blockTxStatus['txNode'] = self.nodeParams.config.nodeId
        self.blockTxStatus['status'] = TDMABlockTxStatus.pending
    
        return True

    def populateBlockResponseList(self):
        """Add currently present nodes to block request response list."""
        for i in range(len(self.nodeParams.nodeStatus)):
            if self.nodeParams.nodeStatus[i].present:
                self.blockTxStatus['blockResponseList'].update({i+1: None})

    def checkBlockResponse(self):
        # Check for positive response from all nodes
        numPosResponses = 0
        for node in self.blockTxStatus['blockResponseList']:
            response = self.blockTxStatus['blockResponseList'][node]
            if response != None:
                if response == False: # False response
                    return False
                elif response == True:
                    numPosResponses += 1

        if numPosResponses == len(self.blockTxStatus['blockResponseList']): # all responded positive
            return True
        else: # still awaiting responses
            return None
                    
