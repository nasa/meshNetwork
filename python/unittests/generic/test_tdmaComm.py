import serial, time, math, struct, copy
from collections import deque
from mesh.generic.command import Command
from mesh.generic.meshController import MeshTxMsg
from mesh.generic.tdmaComm import TDMAComm, TDMAMode, BLOCK_TX_MSG
from mesh.generic.tdmaState import TDMABlockTxStatus, TDMAStatus
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.blockTx import BlockTxPacketStatus
from mesh.generic.msgParser import MsgParser
from mesh.generic.hdlcMsg import HDLCMsg
from mesh.generic.radio import Radio, RadioMode
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeHeader import packHeader
from mesh.generic.customExceptions import InvalidTDMASlotNumber
from unittests.testConfig import configFilePath, testSerialPort
from mesh.generic.cmds import TDMACmds
from mesh.generic.hdlcMsg import HDLC_END_TDMA
from mesh.generic.deserialize import deserialize
from unittests.testCmds import testCmds
import pytest

class TestTDMAComm:
    def setup_method(self, method):

        if testSerialPort:
            serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        else:
            serialPort = []

        self.nodeParams = NodeParams(configFile=configFilePath)
        self.nodeParams.config.commConfig['transmitSlot'] = 1
        self.radio = Radio(serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        msgParser = MsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax}, HDLCMsg(256))
        self.tdmaComm = TDMAComm([TDMACmdProcessor], self.radio, msgParser, self.nodeParams)
  
        # Flush radio
        self.radio.serial.read(100)
 
    def test_resetTDMASlot(self):
        """Test resetTDMASlot method of TDMAComm."""
        frameTime = self.tdmaComm.slotLength
        # Test resetting through range of valid slots
        for i in range(self.tdmaComm.maxNumSlots):
            # Start of slot
            frameTime = self.tdmaComm.slotLength*i
            self.tdmaComm.resetTDMASlot(frameTime)
            assert(math.fabs(self.tdmaComm.slotTime - 0.0) < 1e-5)
            
            # End of slot
            frameTime = self.tdmaComm.slotLength*(i+1) - 0.01
            self.tdmaComm.resetTDMASlot(frameTime)
            assert(math.fabs(self.tdmaComm.slotTime - (self.tdmaComm.slotLength - 0.01)) < 1e-5)
            
            # Verify correct slot number
            assert(self.tdmaComm.slotNum == i + 1)
            
        # Test with frame time greater than cycle time 
        frameTime = self.tdmaComm.cycleLength 
        self.tdmaComm.resetTDMASlot(frameTime)
        assert(self.tdmaComm.slotNum == self.tdmaComm.maxNumSlots)

        # Test with invalid slot numbers
        #with pytest.raises(InvalidTDMASlotNumber): # slot number too high
        #    self.tdmaComm.resetTDMASlot(frameTime, self.tdmaComm.maxNumSlots+1) 
        #with pytest.raises(InvalidTDMASlotNumber) as e: # slot number too low
        #    self.tdmaComm.resetTDMASlot(frameTime, 0)

    def test_setTDMAMode(self):
        """Test setTDMAMode method of TDMAComm."""
        # Test setting all modes
        for mode in TDMAMode.__members__:
            # Set complete flags to True to test reset
            self.tdmaComm.receiveComplete = True
            self.tdmaComm.transmitComplete = True
            # Set mode and check for change
            self.tdmaComm.setTDMAMode(mode)
            assert(self.tdmaComm.tdmaMode == mode)
            if mode == TDMAMode.receive:
                assert(self.tdmaComm.receiveComplete == False) # check receiveComplete status reset
                assert(self.tdmaComm.transmitComplete == True) # check transmitComplete status not reset
            elif mode == TDMAMode.transmit:
                assert(self.tdmaComm.receiveComplete == True) # check receiveComplete status not reset
                assert(self.tdmaComm.transmitComplete == False) # check transmitComplete status reset
        # Test same mode lockout
        self.tdmaComm.setTDMAMode(TDMAMode.receive)
        self.tdmaComm.receiveComplete = True
        self.tdmaComm.setTDMAMode(TDMAMode.receive)
        assert(self.tdmaComm.receiveComplete == True) # flag not reset 
        self.tdmaComm.setTDMAMode(TDMAMode.transmit)
        self.tdmaComm.transmitComplete = True
        self.tdmaComm.setTDMAMode(TDMAMode.transmit)
        assert(self.tdmaComm.transmitComplete == True) # flag not reset 

    def test_packageMeshPacket(self):
        """Test packageMeshPacket method of TDMAComm."""
        packetHeaderLen = struct.calcsize(self.tdmaComm.meshPacketHeaderFormat)

        # Test no send of empty message
        msgBytes = b''
        destId = 5
        assert(len(self.tdmaComm.packageMeshPacket(destId, msgBytes)) == 0)
        
        # Confirm packet structure
        msgBytes = b'1234567890'
        packet = self.tdmaComm.packageMeshPacket(destId, msgBytes)
        assert(len(packet) == packetHeaderLen + len(msgBytes))
        packetHeader = struct.unpack(self.tdmaComm.meshPacketHeaderFormat, packet[0:packetHeaderLen])        
        assert(packetHeader[0] == self.tdmaComm.nodeParams.config.nodeId)
        assert(packetHeader[1] == destId)
        assert(packetHeader[2] == 0) # no admin bytes
        assert(packetHeader[3] == len(msgBytes))
 
        # Test sending of periodic TDMA commands (broadcast message only)
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(time.time()), 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        encodedCmd = self.tdmaComm.tdmaCmdParser.encodeMsg(cmd.serialize())
        self.tdmaComm.tdmaCmds = dict()
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd

        destId = 0 # broadcast message
        packet = self.tdmaComm.packageMeshPacket(destId, msgBytes)
        assert(len(packet) == packetHeaderLen + len(encodedCmd) + len(msgBytes))
        assert(packet[packetHeaderLen:packetHeaderLen+len(encodedCmd)] == encodedCmd)
        assert(packet[packetHeaderLen+len(encodedCmd):] == msgBytes)

        # Confirm admin bytes still sent with zero length message bytes
        msgBytes = b''
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd
        packet = self.tdmaComm.packageMeshPacket(destId, msgBytes)
        assert(len(packet) == packetHeaderLen + len(encodedCmd))
        assert(packet[packetHeaderLen:packetHeaderLen+len(encodedCmd)] == encodedCmd)

    def test_relayMsg(self):
        """Test relayMsg method of TDMAComm."""
        
        # Test that input message is buffered with no alterations other than sourceId
        packet = self.tdmaComm.packageMeshPacket(0, b'1234567890')
        sourceId = int(6)
        assert(sourceId != self.tdmaComm.nodeParams.config.nodeId)
        packet[0:1] = struct.pack('<B', sourceId) # change to a nodeId that doesn't match this node
    
        assert(len(self.tdmaComm.cmdRelayBuffer) == 0)
        self.tdmaComm.relayMsg(packet)
        assert(len(self.tdmaComm.cmdRelayBuffer) > 0)
        decodedBuffer = self.tdmaComm.msgParser.msg.parseMsg(self.tdmaComm.cmdRelayBuffer, 0)
        assert(decodedBuffer[0] == self.tdmaComm.nodeParams.config.nodeId) # sourceId updated
        assert(decodedBuffer[1:] == packet[1:]) # other msg contents unchanged

    def test_processMsgs(self):
        """Test processMsgs method of TDMAComm."""
        commStartTime = int(time.time())
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': commStartTime, 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        encodedCmd = self.tdmaComm.tdmaCmdParser.encodeMsg(cmd.serialize())
        self.tdmaComm.tdmaCmds = dict()
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd
        payloadBytes = b'1234567890'
        
        # Verify pre-test conditions
        assert(len(self.tdmaComm.cmdRelayBuffer) == 0)
        assert(self.tdmaComm.commStartTime == None)

        # Send test packet
        packet = self.tdmaComm.packageMeshPacket(0, payloadBytes)
        self.nodeParams.cmdHistory = deque(maxlen=100) # clear command history to prevent command rejection
        self.tdmaComm.bufferTxMsg(packet)
        numBytesSent = self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        
        # Confirm payload bytes buffered for host
        assert(len(self.tdmaComm.hostBuffer) == 0)
        self.tdmaComm.readMsgs()
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.hostBuffer) > 0)
        assert(self.tdmaComm.hostBuffer == payloadBytes)

        # Confirm mesh admin message processed
        assert(self.tdmaComm.commStartTime == commStartTime)

        ## Test proper relaying
        self.tdmaComm.initMesh() # mesh needs to be inited to relay
        self.nodeParams.cmdHistory = deque(maxlen=100) # clear command history to prevent command rejection
        self.tdmaComm.bufferTxMsg(packet)
        numBytesSent = self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.tdmaComm.readMsgs()
        self.tdmaComm.processMsgs()
        
        cmdRelayBufferLen = len(self.tdmaComm.cmdRelayBuffer)
        assert(cmdRelayBufferLen > 0) # new broadcast command should be relayed
        self.tdmaComm.bufferTxMsg(packet)
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.tdmaComm.readMsgs()
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.cmdRelayBuffer) == cmdRelayBufferLen) # stale command should be tossed
        # Send msg with destination that should be relayed
        self.tdmaComm.maxNumSlots = 7
        self.tdmaComm.meshPaths = [[]*7]*7
        self.tdmaComm.nodeParams.linkStatus = [[0, 1, 1, 0, 0, 0, 0],
                                               [1, 0, 0, 1, 0 ,0, 0],
                                               [1, 0, 0, 1, 0, 0, 0],
                                               [0, 1, 1, 0, 1, 1, 0],
                                               [0, 0, 0, 1, 0, 0, 1],
                                               [0, 0, 0, 1, 0, 0, 1],
                                               [0, 0, 0, 0, 1, 1, 0]]
        self.tdmaComm.updateShortestPaths()
        
        self.tdmaComm.cmdRelayBuffer = bytearray()
        destId = 3
        self.tdmaComm.nodeParams.config.nodeId = 2
        packet = self.tdmaComm.packageMeshPacket(destId, payloadBytes)
        self.tdmaComm.bufferTxMsg(packet)
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.tdmaComm.readMsgs()
        self.tdmaComm.nodeParams.config.nodeId = 1
        self.nodeParams.cmdHistory = deque(maxlen=100) # clear command history to prevent command rejection
        
        self.nodeParams.config.commConfig['recvAllMsgs'] = False # test messages for other nodes not passed to host
        self.tdmaComm.hostBuffer = bytearray()
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.cmdRelayBuffer) > 0) # messages placed in relay buffer
        assert(len(self.tdmaComm.hostBuffer) == 0)
        

        # Send msg with destination that should not be relayed
        self.tdmaComm.cmdRelayBuffer = bytearray()
        destId = 4
        self.tdmaComm.nodeParams.config.nodeId = 2
        packet = self.tdmaComm.packageMeshPacket(destId, payloadBytes)
        self.nodeParams.cmdHistory = deque(maxlen=100) # clear command history to prevent command rejection
        self.tdmaComm.bufferTxMsg(packet)
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.tdmaComm.readMsgs()
        self.tdmaComm.nodeParams.config.nodeId = 1
        self.nodeParams.config.commConfig['recvAllMsgs'] = True # test passing of messages for other nodes to host
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.cmdRelayBuffer) == 0) # message not relayed
        assert(len(self.tdmaComm.hostBuffer) > 0) # message passed to this node's host

    def test_checkForInit(self):
        """Test checkForInit method of TDMAComm."""
        # Confirm radio is off
        assert(self.radio.mode == RadioMode.off)
        
        # Test without message
        self.tdmaComm.checkForInit()
        assert(self.radio.mode == RadioMode.receive)
        assert(self.tdmaComm.commStartTime == None)
        
        # Test with MeshStatus message
        startTime = int(time.time())
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': startTime, 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        self.tdmaComm.bufferTxMsg(self.tdmaComm.packageMeshPacket(0, b''))
        #self.tdmaComm.bufferTxMsg(cmd.serialize())
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.nodeParams.cmdHistory = deque(maxlen=100) # clear command history to prevent command rejection
        self.tdmaComm.checkForInit()
        assert(self.tdmaComm.commStartTime == startTime)

    def test_checkTimeOffset(self):
        """Test checkTimeOffset method of TDMAComm."""
      
        # Test with in bounds time offset
        offsetValue = self.nodeParams.config.commConfig['operateSyncBound'] - 0.001
        ret = self.tdmaComm.checkTimeOffset(offsetValue)
        assert(self.tdmaComm.nodeParams.nodeStatus[self.tdmaComm.nodeParams.config.nodeId-1].timeOffset == offsetValue)
        assert(ret == 0)
        assert(self.tdmaComm.timeOffsetTimer == None)

        # Test with out of bounds time offset
        offsetValue = self.nodeParams.config.commConfig['operateSyncBound'] + 0.001
        ret = self.tdmaComm.checkTimeOffset(offsetValue)
        assert(ret == 1)

        # Test with no offset available
        ret = self.tdmaComm.checkTimeOffset()
        assert(self.tdmaComm.nodeParams.nodeStatus[self.tdmaComm.nodeParams.config.nodeId-1].timeOffset == 0)
        assert(self.tdmaComm.timeOffsetTimer == None)

        # Test timer clear
        ret = self.tdmaComm.checkTimeOffset(self.nodeParams.config.commConfig['operateSyncBound'])
        assert(self.tdmaComm.timeOffsetTimer == None)

        # Elapse offset timer
        self.nodeParams.clock.timeSource = 'pps' # set to something other than None
        self.tdmaComm.timeOffsetTimer = time.time() - (self.tdmaComm.nodeParams.config.commConfig['offsetTimeout'] + 1.0)
        ret = self.tdmaComm.checkTimeOffset()
        assert(self.tdmaComm.tdmaFailsafe == True)
        assert(ret == 2)

    def test_syncTDMAFrame(self):
        """Test syncTDMAFrame method of TDMAComm."""
        # Setup test conditions
        testTime = 5.0
        self.tdmaComm.rxBufferReadPos = 10
        self.tdmaComm.commStartTime = testTime - 0.5*self.tdmaComm.frameLength
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': 0.0, 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        self.tdmaComm.tdmaStatus = TDMAStatus.nominal
        assert(self.tdmaComm.nodeParams.nodeStatus[self.tdmaComm.nodeParams.config.nodeId-1].timeOffset == 127) # offset at default value
        
        # Call method under test
        self.tdmaComm.syncTDMAFrame(testTime)

        # Check frame time variables
        assert(self.tdmaComm.frameTime == 0.5*self.tdmaComm.frameLength)
        assert(self.tdmaComm.frameStartTime == testTime - self.tdmaComm.frameTime)

        # Check that TDMA status updated in outgoing MeshStatus message
        assert(self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']].cmdData['status'] == TDMAStatus.nominal)

        # Check that rx buffer position reset
        assert(self.tdmaComm.rxBufferReadPos == 0)

        # Verify time offset check
        assert(self.tdmaComm.nodeParams.nodeStatus[self.tdmaComm.nodeParams.config.nodeId-1].timeOffset != 127) # offset updated
       
    def test_updateFrameTime(self):
        """Test updateFrameTime method of TDMAComm.""" 
        testTime = time.time()
        self.tdmaComm.commStartTime = testTime

        # Test frame time updates
        self.tdmaComm.frameStartTime = testTime - 0.5*self.tdmaComm.cycleLength
        assert(self.tdmaComm.updateFrameTime(testTime) == 0) # returns 0 if not during sleep 
        self.tdmaComm.frameStartTime = testTime - self.tdmaComm.cycleLength - 0.5*self.tdmaComm.adminLength
        assert(self.tdmaComm.updateFrameTime(testTime) == 0) # returns 0 if not during sleep 

        # Test sleep
        self.tdmaComm.frameStartTime = testTime - self.tdmaComm.cycleLength - self.tdmaComm.adminLength - 0.001
        assert(self.tdmaComm.updateFrameTime(testTime) == 1) # returns 1 if during sleep

    def test_initMesh(self):
        """Test initMesh method of TDMAComm."""
        testTime = time.time()
        self.tdmaComm.commStartTime = testTime - 10.0
        self.tdmaComm.rxBufferReadPos = 10

        # Test pre-test conditions
        assert(len(self.tdmaComm.tdmaCmds) == 0)
        assert(self.tdmaComm.inited == False)
       
        # Call method and check test results
        self.tdmaComm.initMesh(testTime)
        assert(self.tdmaComm.inited == True)
        assert(TDMACmds['MeshStatus'] in self.tdmaComm.tdmaCmds) # periodic messages populated
        assert(TDMACmds['LinkStatus'] in self.tdmaComm.tdmaCmds)
        assert(TDMACmds['TimeOffset'] in self.tdmaComm.tdmaCmds)
        assert(self.tdmaComm.rxBufferReadPos == 0) # confirms syncTDMAFrame called

    @pytest.mark.skipif(testSerialPort == [], reason="No serial port")
    def test_initComm(self):
        """Test initComm method of TDMAComm."""
        testTime = time.time()
        # Confirm starting conditions
        assert(self.radio.mode == RadioMode.off)
        assert(self.tdmaComm.initStartTime == None)

        # Init comm and check radio is now in receive
        self.tdmaComm.initComm(testTime)
        assert(self.tdmaComm.initStartTime == testTime)
        self.tdmaComm.initComm(testTime + 0.01)
        assert(self.radio.mode == RadioMode.receive)
        
        # Send MeshStatus message and confirm that commStartTime is updated
        commStartTime = int(testTime)
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': commStartTime, 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        assert(self.tdmaComm.commStartTime != commStartTime) # check that comm start times do not match
        #print(cmd.serialize())
        #self.tdmaComm.bufferTxMsg(cmd.serialize())
        self.tdmaComm.bufferTxMsg(self.tdmaComm.packageMeshPacket(0, b''))
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.nodeParams.cmdHistory = deque(maxlen=100) # clear command history to prevent command rejection
        self.tdmaComm.initComm(testTime)
        assert(self.tdmaComm.commStartTime == commStartTime) # check that comm start times now match
        
    def test_initCommTimeout(self):
        # Test init timer elapsed
        testTime = time.time()
        self.tdmaComm.initComm(testTime)
        assert(self.tdmaComm.initStartTime == testTime)
        assert(self.tdmaComm.inited == False)

        # Elapse timer and retest
        self.tdmaComm.initComm(testTime + self.tdmaComm.initTimeToWait)
        assert(self.tdmaComm.inited == True) # initMesh called
        assert(self.tdmaComm.commStartTime == math.ceil(testTime + self.tdmaComm.initTimeToWait))

    def test_init(self):
        """Test init method of TDMAComm."""
        # Test initializing when no existing mesh (executing initComm)
        assert(self.tdmaComm.initStartTime == None)
        self.tdmaComm.init(time.time())
        assert(self.tdmaComm.initStartTime != None) # verify initComm called

        # Test joining existing mesh (executing initMesh)
        self.tdmaComm.commStartTime = time.time() # set commStartTime to trigger proper branch
        self.tdmaComm.networkConfigConfirmed = True # set config confirmed to trigger proper branch
        assert(self.tdmaComm.inited == False)
        self.tdmaComm.init(time.time())
        assert(self.tdmaComm.inited == True) # verify initMesh called

    def test_updateMode(self):
        """Test updateMode method of TDMAComm."""
        
        # Test slot change
        self.tdmaComm.slotNum = 1
        self.tdmaComm.updateMode(self.tdmaComm.slotLength)
        assert(self.tdmaComm.slotNum == 2)

        # Test transition to failsafe mode
        self.tdmaComm.tdmaFailsafe = True
        assert(self.tdmaComm.tdmaMode != TDMAMode.failsafe)
        self.tdmaComm.updateMode(0.0)
        assert(self.tdmaComm.tdmaMode == TDMAMode.failsafe)
        self.tdmaComm.tdmaFailsafe = False
        
        # Test transition to sleep
        self.tdmaComm.tdmaMode == TDMAMode.transmit
        self.tdmaComm.updateMode(self.tdmaComm.cycleLength + self.tdmaComm.adminLength)
        assert(self.tdmaComm.tdmaMode == TDMAMode.sleep)
        
        # Test transition to init
        self.tdmaComm.updateMode(self.tdmaComm.enableLength-0.001)
        assert(self.tdmaComm.tdmaMode == TDMAMode.init) 
    
        # Test transition to transmit
        self.tdmaComm.updateMode(self.tdmaComm.beginTxTime)
        assert(self.tdmaComm.tdmaMode == TDMAMode.transmit) 
        self.tdmaComm.updateMode(self.tdmaComm.endTxTime - 0.001)
        assert(self.tdmaComm.tdmaMode == TDMAMode.transmit) 
        self.tdmaComm.updateMode(self.tdmaComm.endTxTime + 0.001)
        assert(self.tdmaComm.tdmaMode == TDMAMode.sleep)    

        # Test transition to receive
        self.tdmaComm.updateMode(self.tdmaComm.slotLength + self.tdmaComm.beginRxTime)
        assert(self.tdmaComm.tdmaMode == TDMAMode.receive)  
        self.tdmaComm.updateMode(self.tdmaComm.slotLength + self.tdmaComm.endRxTime - 0.001)
        assert(self.tdmaComm.tdmaMode == TDMAMode.receive)  
        self.tdmaComm.updateMode(self.tdmaComm.slotLength + self.tdmaComm.endRxTime + 0.001)
        assert(self.tdmaComm.tdmaMode == TDMAMode.sleep)    
    
    def test_sleep(self):
        """Test sleep method of TDMAComm."""
        self.tdmaComm.maxNumSlots = 7
        self.tdmaComm.meshPaths = [[]*7]*7
        self.tdmaComm.nodeParams.linkStatus = [[0, 1, 1, 0, 0, 0, 0],
                                               [1, 0, 0, 1, 0 ,0, 0],
                                               [1, 0, 0, 1, 0, 0, 0],
                                               [0, 1, 1, 0, 1, 1, 0],
                                               [0, 0, 0, 1, 0, 0, 1],
                                               [0, 0, 0, 1, 0, 0, 1],
                                               [0, 0, 0, 0, 1, 1, 0]]
        self.tdmaComm.lastGraphUpdate = time.time()
        meshPaths = copy.deepcopy(self.tdmaComm.meshPaths)        
       
        # Test for frame exceedance
        self.tdmaComm.frameStartTime = time.time() - self.tdmaComm.frameLength - 0.011
        assert(self.tdmaComm.frameExceedanceCount == 0)
        self.tdmaComm.sleep()
        assert(self.tdmaComm.frameExceedanceCount == 1)
        assert(meshPaths == self.tdmaComm.meshPaths) # meshPaths not updated
        
        # Test path update
        self.tdmaComm.lastGraphUpdate = time.time() - self.tdmaComm.nodeParams.config.commConfig['linksTxInterval'] - 0.001
        self.tdmaComm.sleep()
        assert(meshPaths != self.tdmaComm.meshPaths) # meshPaths updated
         

    def test_sendTDMACmds(self):
        """Test sendTDMACmds method of TDMAComm."""
        maxLength = 1000
        self.tdmaComm.commStartTime = time.time();
        flooredStartTime = math.floor(self.tdmaComm.commStartTime)
        self.tdmaComm.tdmaCmds.update({TDMACmds['MeshStatus']: Command(TDMACmds['MeshStatus'], {'commStartTimeSec': flooredStartTime, 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], 0.500)})

        # Check command serialized and returned
        tdmaCmdBytes = self.tdmaComm.sendTDMACmds(maxLength)
        assert(len(tdmaCmdBytes) > 0)

        # Wait for resend
        time.sleep(0.1)
        assert(len(self.tdmaComm.sendTDMACmds(maxLength)) == 0) # should not return anything
        time.sleep(0.4)
        assert(len(self.tdmaComm.sendTDMACmds(maxLength)) > 0) # should return bytes

        # Confirm non-periodic commands are returned and then removed
        self.tdmaComm.tdmaCmds.update({TDMACmds['MeshStatus']: Command(TDMACmds['MeshStatus'], {'commStartTimeSec': flooredStartTime, 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])})
        cmdBytes = self.tdmaComm.sendTDMACmds(maxLength)
        assert(len(cmdBytes) > 0)
        assert(len(self.tdmaComm.tdmaCmds) == 0)

        # Test max length limit
        maxLength = len(cmdBytes) - 1
        self.tdmaComm.tdmaCmds.update({TDMACmds['MeshStatus']: Command(TDMACmds['MeshStatus'], {'commStartTimeSec': flooredStartTime, 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])})
        assert(len(self.tdmaComm.sendTDMACmds(maxLength)) == 0) # should not return anything 
        maxLength = len(cmdBytes)
        assert(len(self.tdmaComm.sendTDMACmds(maxLength)) > 0) # should return bytes successfully
        

    def test_updateShortestPaths(self):
        """ Test updateShortestPaths method of TDMAComm."""
        self.tdmaComm.maxNumSlots = 12
        self.tdmaComm.meshPaths = [[]*12]*12
        nodeId = 1
        sourceId = 11
        self.nodeParams.linkStatus = [[0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0], # tight grid mesh layout
                     [1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0],
                     [1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
                     [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
                     [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0],
                     [0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
                     [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
                     [0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
                     [0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0],
                     [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                     [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0]]
        
        shortestPathLengths = [[0, 1, 1, 1, 1, 2, 1, 2, 2, 2, 2, 2], # expected lengths to all nodes
                               [1, 0, 1, 1, 2, 1, 2, 1, 2, 2, 2, 2],
                               [1, 1, 0, 2, 2, 2, 1, 1, 3, 3, 1, 1],
                               [1, 1, 2, 0, 1, 1, 2, 2, 1, 1, 3, 3],
                               [1, 2, 2, 1, 0, 2, 1, 3, 1, 2, 2, 3],
                               [2, 1, 2, 1, 2, 0, 3, 1, 2, 1, 3, 2],
                               [1, 2, 1, 2, 1, 3, 0, 2, 2, 3, 1, 2],
                               [2, 1, 1, 2, 3, 1, 2, 0, 3, 2, 2, 1],
                               [2, 2, 3, 1, 1, 2, 2, 3, 0, 1, 3, 4],
                               [2, 2, 3, 1, 2, 1, 3, 2, 1, 0, 4, 3],
                               [2, 2, 1, 3, 2, 3, 1, 2, 3, 4, 0, 1],
                               [2, 2, 1, 3, 3, 2, 2, 1, 4, 3, 1, 0]]

        self.tdmaComm.updateShortestPaths()

        # Verify all computed paths meet expected lengths
        for startNode in range(self.tdmaComm.maxNumSlots):
            for node in range(self.tdmaComm.maxNumSlots):
                assert(len(self.tdmaComm.meshPaths[startNode][node][0]) - 1 == shortestPathLengths[startNode][node])

    def test_checkForRelay(self):
        """Test checkForRelay method of TDMAComm."""
 
        # Test relay is true if current node on shortest path
        self.tdmaComm.maxNumSlots = 12
        self.tdmaComm.meshPaths = [[]*12]*12
        nodeId = 1
        sourceId = 11
        self.nodeParams.linkStatus = [[0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0], # tight grid mesh layout
                     [1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0],
                     [1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
                     [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
                     [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0],
                     [0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
                     [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
                     [0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
                     [0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0],
                     [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                     [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0]]
        self.tdmaComm.updateShortestPaths() # determine shortest paths

        truthRelay = [False, False, False, True, False, False, False, False, False, True, False, False]
        for node in range(len(self.nodeParams.linkStatus)):
            assert(self.tdmaComm.checkForRelay(nodeId, node + 1, sourceId) == truthRelay[node])

    def test_createMeshPacket(self):
        """Test createMeshPacket method of TDMAComm."""
       
        destId = 1
        sourceId = 2
        statusByte = 3
        adminBytes = b'1122334455'
        msgBytes = b'09876543'

        # Create packet with admin and message bytes
        packet = self.tdmaComm.createMeshPacket(destId, msgBytes, adminBytes, sourceId, statusByte)
        assert(len(packet) == self.tdmaComm.meshHeaderLen + len(adminBytes) + len(msgBytes))
        packetHeader = struct.unpack(self.tdmaComm.meshPacketHeaderFormat, packet[0:self.tdmaComm.meshHeaderLen])
        assert(packetHeader[0] == sourceId) # verify header contents
        assert(packetHeader[1] == destId) 
        assert(packetHeader[2] == len(adminBytes)) 
        assert(packetHeader[3] == len(msgBytes)) 
        assert(packetHeader[5] == statusByte) 
        assert(adminBytes in packet)
        assert(msgBytes in packet)
        
        # Create admin bytes only packet
        packet = self.tdmaComm.createMeshPacket(destId, b'', adminBytes, sourceId, statusByte)
        assert(len(packet) == self.tdmaComm.meshHeaderLen + len(adminBytes))
        assert(adminBytes in packet) # verify admin bytes included

        # Create message bytes only packet
        packet = self.tdmaComm.createMeshPacket(destId, msgBytes, b'', sourceId, statusByte)
        assert(len(packet) == self.tdmaComm.meshHeaderLen + len(msgBytes))
        assert(msgBytes in packet) # verify message bytes included

    def test_parseMeshPacket(self):
        """Test parseMeshPacket method of TDMAComm."""
        
        # Create test packet
        destId = 1
        sourceId = 2
        statusByte = 3
        adminBytes = b'1122334455'
        msgBytes = b'09876543'
        packet = self.tdmaComm.createMeshPacket(destId, msgBytes, adminBytes, sourceId, statusByte)
       
        # Parse valid packet and verify contents
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(packet) 
        assert(packetValid == True)
        assert(header['sourceId'] == sourceId) # verify header contents
        assert(header['destId'] == destId) 
        assert(header['adminLength'] == len(adminBytes)) 
        assert(header['payloadLength'] == len(msgBytes)) 
        assert(header['statusByte'] == statusByte) 
        assert(admin == adminBytes)
        assert(msg == msgBytes)

        # Attempt to parse invalid packet
        badPacket = packet[0:5] + b'999' + packet[5:]
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(badPacket) 
        assert(packetValid == False)

    def test_sendMsgs(self):
        """Test sendMsgs method of TDMAComm."""
        # Test send only when conditions met
        self.tdmaComm.enabled = False
        self.tdmaComm.tdmaMode = TDMAMode.receive
        self.tdmaComm.transmitComplete = False
        assert(len(self.tdmaComm.radio.txBuffer) == 0)
        self.tdmaComm.radio.bufferTxMsg(b'12345')
        assert(len(self.tdmaComm.radio.txBuffer) > 0)
        self.tdmaComm.sendMsgs()
        assert(len(self.tdmaComm.radio.txBuffer) > 0) # message not sent
        assert(self.tdmaComm.transmitComplete == False)
        self.tdmaComm.enabled = True
        self.tdmaComm.sendMsgs()
        assert(len(self.tdmaComm.radio.txBuffer) > 0) # message still not sent
        self.tdmaComm.tdmaMode = TDMAMode.transmit
        self.tdmaComm.sendMsgs()
        assert(len(self.tdmaComm.radio.txBuffer) == 0) # message sent
        

        # Test transmission of periodic commands
        #serBytes = self.tdmaComm.radio.getRxBytes() # clear incoming bytes
        #assert(len(self.tdmaComm.cmdBuffer) == 0)
        #assert(len(self.tdmaComm.cmdRelayBuffer) == 0)
        #cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(time.time()), 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        #self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd
        #self.tdmaComm.sendMsg()
        #time.sleep(0.1)
        #self.tdmaComm.readBytes()
        #serBytes = self.tdmaComm.radio.getRxBytes()
        #assert(len(serBytes) > 0)
        #assert(serBytes[-1:] == HDLC_END_TDMA) # check for end of message indicator

        # Test command relay buffer
        testMsg = b'1234567890'
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.cmdRelayBuffer = testMsg
        self.tdmaComm.sendMsgs()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        serBytes = self.tdmaComm.radio.getRxBytes()
        assert(testMsg in serBytes)
       
        # Test command buffer
        self.tdmaComm.radio.clearRxBuffer()
        testCmd = {'bytes': b'12345'}
        self.tdmaComm.cmdBuffer['key1'] = testCmd
        self.tdmaComm.sendMsgs()
        assert(len(self.tdmaComm.cmdBuffer) == 0) # command buffer flushed out
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0)

        ## Test meshQueue processing
        # Test no output for empty queue
        self.tdmaComm.sendMsgs()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0) # nothing sent when meshQueue is empty (and no periodic commands)

        # Test broadcast message output
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(time.time()), 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd
        encodedCmd = self.tdmaComm.tdmaCmdParser.encodeMsg(cmd.serialize())
        self.tdmaComm.sendMsgs()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0) # message sent when periodic commands pending
        self.tdmaComm.parseMsgs()
        assert(len(self.tdmaComm.msgParser.parsedMsgs) == 1)
        packetHeader = struct.unpack('<BB', self.tdmaComm.msgParser.parsedMsgs[0][0:2])
        assert(packetHeader[1] == 0) # broadcast message
        assert(encodedCmd in self.tdmaComm.msgParser.parsedMsgs[0]) # tdmaCmds included in message

        # Test destination specific output
        self.tdmaComm.msgParser.parsedMsgs = []
        self.nodeParams.config.commConfig['recvAllMsgs'] = True # receive all messages, regardless of dest
        msg1 = b'1234567890'
        msg1Dest = 3
        msg2 = b'0987654321'
        msg2Dest = 5
        self.tdmaComm.meshQueueIn.append(MeshTxMsg(msg1Dest, msg1))
        self.tdmaComm.meshQueueIn.append(MeshTxMsg(msg2Dest, msg2)) 
        self.tdmaComm.sendMsgs()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0)
        self.tdmaComm.parseMsgs()
        assert(len(self.tdmaComm.msgParser.parsedMsgs) == 2)
        destIds = []
        for msg in self.tdmaComm.msgParser.parsedMsgs:
            packetHeader = struct.unpack('<BB', msg[0:2])
            destIds.append(packetHeader[1])
        assert(msg1Dest in destIds)
        assert(msg2Dest in destIds)

        # Test maximum transmit size limit

    def test_sendMsgs_sendBroadcast(self):
        """Test that a broadcast message is sent if admin messages pending."""
        self.tdmaComm.commStartTime = time.time()
        self.tdmaComm.initMesh()
        self.tdmaComm.enabled = True
        self.tdmaComm.tdmaMode = TDMAMode.transmit
        
        # Test automatic broadcast message output
        assert(len(self.tdmaComm.meshQueueIn) == 0) # no pending outgoing messages
        assert(self.tdmaComm.radio.bytesInRxBuffer == 0) # read buffer is empty
        self.tdmaComm.sendMsgs()
        time.sleep(0.1) 
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0)
        
        self.tdmaComm.parseMsgs()
        assert(len(self.tdmaComm.msgParser.parsedMsgs) == 1)
        packetHeader = struct.unpack('<BB', self.tdmaComm.msgParser.parsedMsgs[0][0:2])
        assert(packetHeader[1] == 0) # broadcast message

    def test_readMsgs(self):
        """Test readMsgs method of TDMAComm."""
        self.tdmaComm.radio.clearRxBuffer()
        testMsg = b'1234567890'
        self.tdmaComm.sendBytes(testMsg)
        time.sleep(0.1)
        assert(self.tdmaComm.readMsgs() == False)
        assert(self.radio.bytesInRxBuffer == len(testMsg))

    def test_processMeshMsgs(self):
        """Test processMeshMsgs method of TDMAComm."""
        commStartTime = int(time.time())
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': commStartTime, 'status': TDMAStatus.nominal, 'configHash': self.nodeParams.config.calculateHash()}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        encodedCmd = self.tdmaComm.tdmaCmdParser.encodeMsg(cmd.serialize())

        # Verify pre-test conditions
        assert(self.tdmaComm.commStartTime == None)
        self.tdmaComm.processMeshMsgs(encodedCmd)
        assert(self.tdmaComm.commStartTime == commStartTime)

    def test_startBlockTx(self):
        """Test startBlockTx method of TDMAComm."""
        # Pre-test conditions
        assert(self.tdmaComm.blockTxInProgress == False)
        assert(self.tdmaComm.blockTx == None)

        # Test starting a block tx
        assert(self.tdmaComm.startBlockTx(10, 0, 1, time.time(), 10, b'1234567890') == True)
        assert(self.tdmaComm.blockTx != None)
        assert(self.tdmaComm.blockTxInProgress == True)

        # Test rejection when block tx already in progress
        assert(self.tdmaComm.startBlockTx(20, 0, 1, time.time(), 10, b'1234567890') == False)

    def test_endBlockTx(self):
        "Test endBlockTx method of TDMAComm."""

        blockTxData = b'1234567890'        

        # Test ending block transmit as sending node
        self.tdmaComm.startBlockTx(10, 0, self.nodeParams.config.nodeId, time.time(), 10, blockTxData)
        assert(self.tdmaComm.blockTxInProgress == True)
        self.tdmaComm.blockTxPacketStatus = {'a': 1} # setup up dummy contents to check clearing
        self.tdmaComm.blockTxPacketReceipts = [1]
        self.tdmaComm.endBlockTx()
        assert(self.tdmaComm.blockTxInProgress == False)
        assert(len(self.tdmaComm.blockTxPacketStatus) == 0)
        assert(len(self.tdmaComm.blockTxPacketReceipts) == 0)
        assert(len(self.tdmaComm.blockTxOut) == 0) # source node does not forward to host
        
        # Test ending block transmit as receiver
        self.tdmaComm.startBlockTx(10, 0, self.nodeParams.config.nodeId + 1, time.time(), 10, blockTxData)
        assert(self.tdmaComm.blockTxInProgress == True)
        self.tdmaComm.blockTx.packets = {1: blockTxData}
        self.tdmaComm.endBlockTx()
        assert(self.tdmaComm.blockTxInProgress == False)
        assert(len(self.tdmaComm.blockTxOut['data']) == len(blockTxData)) # receiving node should forward to host

    def test_updateBlockTxStatus(self):
        "Test updateBlockTxStatus method of TDMAComm."""

        # Set up block tx
        self.tdmaComm.startBlockTx(10, 0, self.nodeParams.config.nodeId, time.time(), 10, b'12345')
        assert(self.tdmaComm.blockTxInProgress == True)
        assert(self.tdmaComm.blockTx.complete == False)
        assert(TDMACmds['BlockTxRequest'] not in self.tdmaComm.tdmaCmds)

        # Test sending node sends block tx end request and ends block transmit
        self.tdmaComm.updateBlockTxStatus()
        assert(self.tdmaComm.blockTxInProgress == True) # end conditions not met
        self.tdmaComm.blockTx.complete = True
        self.tdmaComm.updateBlockTxStatus()
        assert(self.tdmaComm.blockTxInProgress == False) # end by complete indication
        assert(TDMACmds['BlockTxRequest'] in self.tdmaComm.tdmaCmds) # end request sent

        # Test ending via time and receiving node
        del self.tdmaComm.tdmaCmds[TDMACmds['BlockTxRequest']]
        self.tdmaComm.startBlockTx(10, 0, self.nodeParams.config.nodeId+1, 0, 10, b'12345')
        assert(self.tdmaComm.blockTxInProgress == True)
        assert(self.tdmaComm.blockTx.complete == False)
        self.tdmaComm.updateBlockTxStatus()
        assert(self.tdmaComm.blockTxInProgress == False) # ended by time
        assert(TDMACmds['BlockTxRequest'] not in self.tdmaComm.tdmaCmds) # no end request
        

    def test_processBlockTxReceipts(self):
        "Test processBlockTxReceipts method of TDMAComm."""
        # Set up block tx and packet status
        blockReqId = 10
        packetNum = 1
        receiptSrcId = self.nodeParams.config.nodeId + 1
        self.tdmaComm.startBlockTx(blockReqId, 0, self.nodeParams.config.nodeId, time.time(), 10, b'12345')
        self.tdmaComm.blockTxPacketStatus[packetNum] = BlockTxPacketStatus(None, packetNum)

        # Process receipt
        assert(receiptSrcId not in self.tdmaComm.blockTxPacketStatus[packetNum].responsesRcvd)
        self.tdmaComm.blockTxPacketReceipts.append({'blockReqId': blockReqId, 'packetNum': packetNum, 'sourceId': receiptSrcId})
        self.tdmaComm.processBlockTxReceipts()
        assert(receiptSrcId in self.tdmaComm.blockTxPacketStatus[packetNum].responsesRcvd) # receipt processed
        assert(len(self.tdmaComm.blockTxPacketReceipts) == 0) # block tx receipts cleared

    def test_getBlockTxPacket(self):
        """Test getBlockTxPacket method of TDMAComm."""
        # Start a block transmit
        blockData = b'123457890'*500
        blockReqId = 10
        destId = 3
        sourceId = self.nodeParams.config.nodeId
        startTime = time.time()
        length = 2 
        dataLength = int(1.5 * self.nodeParams.config.commConfig['blockTxPacketSize'])
        self.tdmaComm.startBlockTx(blockReqId, destId, sourceId, startTime, length, blockData[0:dataLength])

        # Test generating full size packet
        blockTxPacket = self.tdmaComm.getBlockTxPacket()
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(blockTxPacket) 
        assert(packetValid == True)
        assert(header['statusByte'] == BLOCK_TX_MSG)
        self.tdmaComm.tdmaCmdParser.parseMsgs(admin)
        assert(len(self.tdmaComm.tdmaCmdParser.parsedMsgs) == 1)
        blockTxPacketCmd = deserialize(self.tdmaComm.tdmaCmdParser.parsedMsgs.pop(), TDMACmds['BlockData'])
        assert(blockTxPacketCmd[0]['cmdId'] == TDMACmds['BlockData'])
        assert(blockTxPacketCmd[1]['blockReqId'] == blockReqId)
        assert(blockTxPacketCmd[1]['packetNum'] == 1)
        assert(blockTxPacketCmd[1]['raw'] == blockData[0:self.nodeParams.config.commConfig['blockTxPacketSize']])

        # Test generating partial size packet
        blockTxPacket = self.tdmaComm.getBlockTxPacket()
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(blockTxPacket) 
        self.tdmaComm.tdmaCmdParser.parseMsgs(admin)
        blockTxPacketCmd = deserialize(self.tdmaComm.tdmaCmdParser.parsedMsgs.pop(), TDMACmds['BlockData'])
        assert(blockTxPacketCmd[1]['packetNum'] == 2)
        assert(blockTxPacketCmd[1]['raw'] == blockData[self.nodeParams.config.commConfig['blockTxPacketSize']:dataLength])

    def test_sendBlockTxPacket(self):
        """Test sendBlockTxPacket method of TDMAComm."""
        # Set up test conditions
        self.nodeParams.config.commConfig['blockTxReceiptTimeout'] = 2
        self.nodeParams.config.commConfig['blockTxPacketRetry'] = 1
        self.tdmaComm.neighbors = [1,2,3,4,5] # add neighbors

        # Start a block transmit
        blockData = b'123457890'*500
        blockReqId = 10
        destId = 3
        sourceId = self.nodeParams.config.nodeId
        startTime = time.time()
        length = 10
        self.tdmaComm.startBlockTx(blockReqId, destId, sourceId, startTime, length, blockData)

        # Send out first packet
        blockTxPacket = self.tdmaComm.sendBlockTxPacket()
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(blockTxPacket) 
        self.tdmaComm.tdmaCmdParser.parseMsgs(admin)
        blockTxPacketCmd = deserialize(self.tdmaComm.tdmaCmdParser.parsedMsgs.pop(), TDMACmds['BlockData'])
        assert(blockTxPacketCmd[1]['packetNum'] == 1)
        assert(len(blockTxPacketCmd[1]['raw']) == self.nodeParams.config.commConfig['blockTxPacketSize'])
        assert(len(self.tdmaComm.blockTxPacketStatus) == 1) # packet status list updated

        # Send another packet
        blockTxPacket = self.tdmaComm.sendBlockTxPacket()
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(blockTxPacket) 
        self.tdmaComm.tdmaCmdParser.parseMsgs(admin)
        blockTxPacketCmd = deserialize(self.tdmaComm.tdmaCmdParser.parsedMsgs.pop(), TDMACmds['BlockData'])
        assert(blockTxPacketCmd[1]['packetNum'] == 2)
        assert(len(self.tdmaComm.blockTxPacketStatus) == 2) # packet status list updated

        # Test packet resend 
        assert(self.tdmaComm.nodeParams.config.commConfig['blockTxReceiptTimeout'] == 2)
        #self.tdmaComm.blockTxPacketStatus[0].framesSinceTx = self.nodeParams.config.commConfig['blockTxReceiptTimeout'] # set retransmit trigger
        blockTxPacket = self.tdmaComm.sendBlockTxPacket()
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(blockTxPacket) 
        self.tdmaComm.tdmaCmdParser.parseMsgs(admin)
        blockTxPacketCmd = deserialize(self.tdmaComm.tdmaCmdParser.parsedMsgs.pop(), TDMACmds['BlockData'])
        assert(blockTxPacketCmd[1]['packetNum'] == 1) # resend of packet 1
        assert(len(self.tdmaComm.blockTxPacketStatus) == 1) # packet removed from status list because retry limit met, expired packet removed
        assert(2 in self.tdmaComm.blockTxPacketStatus.keys()) # second packet only

        # Test packet receipt processing
        self.tdmaComm.nodeParams.config.commConfig['blockTxReceiptTimeout'] = 10 # increase timeout so packet status isn't cleared
        self.tdmaComm.blockTxPacketStatus[2].responsesRcvd = self.tdmaComm.neighbors # update responses to include all neighbors
        blockTxPacket = self.tdmaComm.sendBlockTxPacket()
        packetValid, header, admin, msg = self.tdmaComm.parseMeshPacket(blockTxPacket) 
        self.tdmaComm.tdmaCmdParser.parseMsgs(admin)
        blockTxPacketCmd = deserialize(self.tdmaComm.tdmaCmdParser.parsedMsgs.pop(), TDMACmds['BlockData'])
        assert(blockTxPacketCmd[1]['packetNum'] == 3) # new packet
        assert(2 not in self.tdmaComm.blockTxPacketStatus.keys()) # packet 2 status cleared

    def test_executeBlockTx(self):
        """Test executeBlockTx method of TDMAComm."""
        # Set up test
        blockData = b'123457890'*500
        blockReqId = 10
        destId = self.nodeParams.config.nodeId+1
        sourceId = self.nodeParams.config.nodeId-1
        startTime = time.time()
        length = 2 
        dataLength = int(1.5 * self.nodeParams.config.commConfig['blockTxPacketSize'])
        self.tdmaComm.startBlockTx(blockReqId, destId, sourceId, startTime, length, blockData[0:dataLength])
        
        # Test transition to enable (as receiver)
        adminTime = 0.0
        assert(self.tdmaComm.radio.mode == RadioMode.off)
        self.tdmaComm.executeBlockTx(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.receive)

        # Test block receive
        adminTime = self.tdmaComm.rxReadTime 
        self.tdmaComm.executeBlockTx(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.receive) # still in receive
        self.tdmaComm.receiveComplete = True # set receive complete flag
        self.tdmaComm.executeBlockTx(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.sleep) # radio set to sleep

        # Test block transmit
        sourceId = self.nodeParams.config.nodeId
        self.tdmaComm.blockTxInProgress = False 
        self.tdmaComm.startBlockTx(blockReqId, destId, sourceId, time.time(), length, blockData[0:dataLength])
        assert(self.tdmaComm.blockTxInProgress == True)
        assert(self.tdmaComm.blockTx.packetNum == 0)
        assert(self.tdmaComm.transmitComplete == False)
        adminTime = self.tdmaComm.beginTxTime 
        self.tdmaComm.executeBlockTx(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.transmit)
        assert(self.tdmaComm.transmitComplete == True)
        assert(self.tdmaComm.blockTx.packetNum == 1) # block tx packet sent
        self.tdmaComm.executeBlockTx(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.sleep) # radio set to sleep upon transmit completion

    def test_executeAdmin(self):
        """Test executeAdmin method of TDMAComm."""
        # Set up test
        self.tdmaComm.frameCount = 0 
        
        # Test transition to enable (as receiver)
        adminTime = 0.0
        assert(self.tdmaComm.radio.mode == RadioMode.off)
        self.tdmaComm.executeAdmin(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.receive)

        # Test admin receive
        adminTime = self.tdmaComm.rxReadTime 
        self.tdmaComm.executeAdmin(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.receive) # still in receive
        self.tdmaComm.receiveComplete = True # set receive complete flag
        self.tdmaComm.executeAdmin(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.sleep) # radio set to sleep

        # Test admin transmit
        assert(self.tdmaComm.transmitComplete == False)
        adminTime = self.tdmaComm.beginTxTime 
        self.tdmaComm.frameCount = self.nodeParams.config.nodeId - 1
        self.tdmaComm.executeAdmin(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.transmit)
        assert(self.tdmaComm.transmitComplete == True)
        self.tdmaComm.executeAdmin(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.sleep) # radio set to sleep upon transmit completion

    def test_admin(self):
        """Test admin method of TDMAComm."""
        # Set up test
        self.tdmaComm.frameCount = 0 
        
        # Test radio sleep once receive or transmit complete
        self.tdmaComm.radio.setMode(RadioMode.receive)
        self.tdmaComm.receiveComplete = True
        self.tdmaComm.admin()
        assert(self.tdmaComm.radio.mode == RadioMode.sleep)
        self.tdmaComm.radio.setMode(RadioMode.receive)
        self.tdmaComm.receiveComplete = False
        self.tdmaComm.transmitComplete = True
        self.tdmaComm.admin()
        assert(self.tdmaComm.radio.mode == RadioMode.sleep)

        # Test execution of admin rx
        self.tdmaComm.receiveComplete = False
        self.tdmaComm.transmitComplete = False
        adminTime = 0.0
        self.tdmaComm.executeAdmin(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.receive)

        # Test execution of block tx
        blockData = b'123457890'*500
        blockReqId = 10
        destId = self.nodeParams.config.nodeId+1
        sourceId = self.nodeParams.config.nodeId
        startTime = time.time()
        length = 2 
        self.tdmaComm.startBlockTx(blockReqId, destId, sourceId, startTime, length, blockData)
        assert(self.tdmaComm.blockTxInProgress == True)
        adminTime = self.tdmaComm.beginTxTime 
        self.tdmaComm.executeBlockTx(adminTime)
        assert(self.tdmaComm.radio.mode == RadioMode.transmit)
        assert(self.tdmaComm.transmitComplete == True)
        assert(self.tdmaComm.blockTx.packetNum == 1) # block tx packet sent

    def test_executeTDMAComm(self):
        """Test executeTDMAComm method of TDMAComm."""
        testMsg = b'1234567890'
        self.tdmaComm.transmitSlot = 2
        self.tdmaComm.radio.clearRxBuffer()
        # Test times
        times = [0.0, self.tdmaComm.beginRxTime, self.tdmaComm.beginRxTime + 0.5*(self.tdmaComm.endRxTime - self.tdmaComm.beginRxTime), self.tdmaComm.endRxTime]
        times = times + [self.tdmaComm.slotLength, self.tdmaComm.slotLength + self.tdmaComm.beginTxTime, self.tdmaComm.slotLength + 0.5*(self.tdmaComm.endTxTime - self.tdmaComm.beginRxTime), self.tdmaComm.slotLength + self.tdmaComm.endTxTime]
        times = times + [self.tdmaComm.cycleLength, self.tdmaComm.cycleLength + self.tdmaComm.adminLength] # post cycle
        print(times)
        # Test truth modes
        truthModes = [TDMAMode.init, TDMAMode.receive, TDMAMode.receive, TDMAMode.sleep, TDMAMode.init, TDMAMode.transmit, TDMAMode.transmit, TDMAMode.sleep, TDMAMode.admin, TDMAMode.sleep]   
       
        # Force init
        self.tdmaComm.inited = True
        self.tdmaComm.commStartTime = 0.0
        self.tdmaComm.initMesh()
        time.sleep(1.0) # sleep to ensure periodic commands get queued
        self.tdmaComm.frameStartTime = 0.0
 
        # Loop through test times and verify conditions
        for i in range(len(times)):
            print("Test time/Expected mode:", times[i], truthModes[i])
            self.tdmaComm.executeTDMAComm(times[i])
            assert(self.tdmaComm.tdmaMode == truthModes[i])
            # Receive slot actions
            if i == 1: # prep for read
                assert(self.tdmaComm.radio.mode == RadioMode.receive)
                assert(self.tdmaComm.radio.bytesInRxBuffer == 0);
                self.tdmaComm.sendBytes(testMsg + HDLC_END_TDMA) # send bytes to read
                time.sleep(0.1)
            if i == 2: # post receive 
                assert(self.tdmaComm.radio.mode == RadioMode.receive)
                assert(self.tdmaComm.radio.bytesInRxBuffer > 0);
    
            # Transmit slot actions     
            if i == 4:
                self.tdmaComm.radio.clearRxBuffer()
                assert(self.tdmaComm.transmitComplete == False)
            if i == 5: # prep for transmit
                assert(self.tdmaComm.radio.mode == RadioMode.transmit)
                self.tdmaComm.bufferTxMsg(testMsg) # buffer bytes to transmit
            if i == 6: # post transmit
                assert(self.tdmaComm.radio.mode == RadioMode.sleep)
                assert(self.tdmaComm.transmitComplete == True)
                time.sleep(0.1) # delay to ensure transmit complete

                # Check if bytes transmitted
                self.tdmaComm.readBytes()
                assert(self.tdmaComm.radio.bytesInRxBuffer > 0)
            
        ## Test non-time-based modes
        # Failsafe
        self.tdmaComm.tdmaMode = TDMAMode.failsafe
        self.tdmaComm.radio.setMode(RadioMode.sleep)
        self.tdmaComm.executeTDMAComm(0.0)
        assert(self.tdmaComm.radio.mode == RadioMode.receive)

    def test_execute(self):
        """Test execute method of TDMAComm."""
        # Test init start
        assert(self.tdmaComm.inited == False)
        self.tdmaComm.commStartTime = time.time()
        self.tdmaComm.networkConfigConfirmed = True
        self.tdmaComm.execute()
        assert(self.tdmaComm.inited == True)

        # Test TDMA logic executed
        self.tdmaComm.tdmaFailsafe = True
        self.tdmaComm.radio.setMode(RadioMode.sleep)
        self.tdmaComm.frameStartTime = time.time()
        self.tdmaComm.execute()
        assert(self.tdmaComm.radio.mode == RadioMode.receive) # should be listening in failsafe

    
