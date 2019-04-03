import serial, time, math, struct, copy
from mesh.generic.command import Command
from mesh.generic.tdmaComm import TDMAComm, TDMAMode
from mesh.generic.tdmaState import TDMABlockTxStatus, TDMAStatus
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.msgParser import MsgParser
from mesh.generic.hdlcMsg import HDLCMsg
from mesh.generic.radio import Radio, RadioMode
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeHeader import packHeader
from mesh.generic.customExceptions import InvalidTDMASlotNumber
from unittests.testConfig import configFilePath, testSerialPort
from mesh.generic.cmds import TDMACmds
from mesh.generic.hdlcMsg import HDLC_END_TDMA
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
        packetHeaderLen = 8

        # Test no send of empty message
        msgBytes = b''
        destId = 5
        assert(len(self.tdmaComm.packageMeshPacket(destId, msgBytes)) == 0)
        
        # Confirm packet structure
        msgBytes = b'1234567890'
        packet = self.tdmaComm.packageMeshPacket(destId, msgBytes)
        assert(len(packet) == packetHeaderLen + len(msgBytes))
        packetHeader = struct.unpack('<BBHHH', packet[0:packetHeaderLen])        
        assert(packetHeader[0] == self.tdmaComm.nodeParams.config.nodeId)
        assert(packetHeader[1] == destId)
        assert(packetHeader[2] == 0) # no admin bytes
        assert(packetHeader[3] == len(msgBytes))
 
        # Test sending of periodic TDMA commands (broadcast message only)
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(time.time()), 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
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
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': commStartTime, 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        encodedCmd = self.tdmaComm.tdmaCmdParser.encodeMsg(cmd.serialize())
        self.tdmaComm.tdmaCmds = dict()
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd
        payloadBytes = b'1234567890'
        
        # Verify pre-test conditions
        assert(len(self.tdmaComm.cmdRelayBuffer) == 0)
        assert(self.tdmaComm.commStartTime == None)

        # Send test packet
        packet = self.tdmaComm.packageMeshPacket(0, payloadBytes)
        self.tdmaComm.bufferTxMsg(packet)
        self.tdmaComm.sendBuffer()
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
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.cmdRelayBuffer) > 0)

        # Send msg with destination that should not be relayed
        self.tdmaComm.cmdRelayBuffer = bytearray()
        destId = 4
        self.tdmaComm.nodeParams.config.nodeId = 2
        packet = self.tdmaComm.packageMeshPacket(destId, payloadBytes)
        self.tdmaComm.bufferTxMsg(packet)
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.tdmaComm.readMsgs()
        self.tdmaComm.nodeParams.config.nodeId = 1
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.cmdRelayBuffer) == 0)

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
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': startTime, 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], 0)
        self.tdmaComm.bufferTxMsg(self.tdmaComm.packageMeshPacket(0, b''))
        #self.tdmaComm.bufferTxMsg(cmd.serialize())
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
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
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': 0.0, 'status': TDMAStatus.blockTx}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
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
        assert(self.tdmaComm.updateFrameTime(testTime) == 0) # returns 0 if during cycle

        # Test cycle end
        assert(self.tdmaComm.updateFrameTime(testTime + 0.5*self.tdmaComm.cycleLength + 0.01) == 1) # returns 1 if during sleep

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
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': commStartTime, 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], 0)
        assert(self.tdmaComm.commStartTime != commStartTime) # check that comm start times do not match
        #print(cmd.serialize())
        #self.tdmaComm.bufferTxMsg(cmd.serialize())
        self.tdmaComm.bufferTxMsg(self.tdmaComm.packageMeshPacket(0, b''))
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
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
        self.tdmaComm.updateMode(self.tdmaComm.cycleLength)
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
    
        # Test transition to blockTx
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId
        self.tdmaComm.updateMode(0.0)
        assert(self.tdmaComm.tdmaMode == TDMAMode.blockTx)  

        # Test transition to blockRx
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId + 1
        self.tdmaComm.updateMode(0.0)
        assert(self.tdmaComm.tdmaMode == TDMAMode.blockRx)  
        
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
        self.tdmaComm.commStartTime = time.time();
        flooredStartTime = math.floor(self.tdmaComm.commStartTime)
        self.tdmaComm.tdmaCmds.update({TDMACmds['MeshStatus']: Command(TDMACmds['MeshStatus'], {'commStartTimeSec': flooredStartTime, 'status': self.tdmaComm.tdmaStatus}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], 0.500)})

        # Check command serialized and returned
        tdmaCmdBytes = self.tdmaComm.sendTDMACmds()
        assert(len(tdmaCmdBytes) > 0)

        # Wait for resend
        time.sleep(0.1)
        assert(len(self.tdmaComm.sendTDMACmds()) == 0) # should not return anything
        time.sleep(0.4)
        assert(len(self.tdmaComm.sendTDMACmds()) > 0) # should return bytes

        # Confirm non-periodic commands are returned and then removed
        self.tdmaComm.tdmaCmds = {TDMACmds['MeshStatus']: Command(TDMACmds['MeshStatus'], {'commStartTimeSec': flooredStartTime, 'status': self.tdmaComm.tdmaStatus}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])}
        assert(len(self.tdmaComm.sendTDMACmds()) > 0)
        assert(len(self.tdmaComm.tdmaCmds) == 0)

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

    def test_queueMeshMsg(self):
        """Test queueMeshMsg method of TDMAComm."""
        destId = 3

        # Verify pre-test conditions
        assert(len(self.tdmaComm.meshQueueIn[destId]) == 0)
        
        # Run test
        testMsg = b'1234567890'
        self.tdmaComm.queueMeshMsg(destId, testMsg)
        assert(self.tdmaComm.meshQueueIn[destId] == testMsg)

    def test_sendMsg(self):
        """Test sendMsg method of TDMAComm."""
        # Test send only when conditions met
        self.tdmaComm.enabled = False
        self.tdmaComm.tdmaMode = TDMAMode.receive
        self.tdmaComm.transmitComplete = False
        assert(len(self.tdmaComm.radio.txBuffer) == 0)
        self.tdmaComm.radio.bufferTxMsg(b'12345')
        assert(len(self.tdmaComm.radio.txBuffer) > 0)
        self.tdmaComm.sendMsg()
        assert(len(self.tdmaComm.radio.txBuffer) > 0) # message not sent
        assert(self.tdmaComm.transmitComplete == False)
        self.tdmaComm.enabled = True
        self.tdmaComm.sendMsg()
        assert(len(self.tdmaComm.radio.txBuffer) > 0) # message still not sent
        self.tdmaComm.tdmaMode = TDMAMode.transmit
        self.tdmaComm.sendMsg()
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
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        serBytes = self.tdmaComm.radio.getRxBytes()
        assert(testMsg in serBytes)
       
        # Test command buffer
        self.tdmaComm.radio.clearRxBuffer()
        testCmd = {'bytes': b'12345'}
        self.tdmaComm.cmdBuffer['key1'] = testCmd
        self.tdmaComm.sendMsg()
        assert(len(self.tdmaComm.cmdBuffer) == 0) # command buffer flushed out
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0)

        ## Test meshQueue processing
        # Test no output for empty queue
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0) # nothing sent when meshQueue is empty (and no periodic commands)

        # Test broadcast message output
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(time.time()), 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd
        encodedCmd = self.tdmaComm.tdmaCmdParser.encodeMsg(cmd.serialize())
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0) # message sent when periodic commands pending
        self.tdmaComm.parseMsgs()
        assert(len(self.tdmaComm.msgParser.parsedMsgs) == 1)
        packetHeader = struct.unpack('<BBHHH', self.tdmaComm.msgParser.parsedMsgs[0][0:8])
        assert(packetHeader[1] == 0) # broadcast message
        assert(encodedCmd in self.tdmaComm.msgParser.parsedMsgs[0]) # tdmaCmds included in message

        # Test destination specific output
        self.nodeParams.config.commConfig['recvAllMsgs'] = True # receive all messages, regardless of dest
        msg1 = b'1234567890'
        msg1Dest = 3
        msg2 = b'0987654321'
        msg2Dest = 5
        self.tdmaComm.meshQueueIn[msg1Dest] = msg1
        self.tdmaComm.meshQueueIn[msg2Dest] = msg2 
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0)
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.hostBuffer) > 0)
        assert(msg1 in self.tdmaComm.hostBuffer)
        assert(msg2 in self.tdmaComm.hostBuffer)

        # Test without receiving messages for other nodes
        self.tdmaComm.hostBuffer = bytearray()
        self.nodeParams.config.commConfig['recvAllMsgs'] = False
        msg1Dest = self.nodeParams.config.nodeId
        self.tdmaComm.meshQueueIn[msg1Dest] = msg1
        self.tdmaComm.meshQueueIn[msg2Dest] = msg2 
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0)
        self.tdmaComm.processMsgs()
        assert(len(self.tdmaComm.hostBuffer) > 0)
        assert(self.tdmaComm.hostBuffer == msg1)

    def test_readMsgs(self):
        """Test readMsgs method of TDMAComm."""
        # Send message without END_TDMA byte and check for False returned
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.rxBufferReadPos = 0
        testMsg = b'1234567890'
        self.tdmaComm.sendBytes(testMsg)
        time.sleep(0.1)
        assert(self.tdmaComm.readMsgs() == False)

        # Send message with END_TDMA byte and check for True returned
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.rxBufferReadPos = 0
        self.tdmaComm.sendBytes(testMsg + HDLC_END_TDMA)    
        time.sleep(0.1)
        out = self.tdmaComm.readMsgs()
        print("Read status:", out, self.tdmaComm.rxBufferReadPos)
        assert(out == True)

    def test_processMeshMsgs(self):
        """Test processMeshMsgs method of TDMAComm."""
        commStartTime = int(time.time())
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': commStartTime, 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        encodedCmd = self.tdmaComm.tdmaCmdParser.encodeMsg(cmd.serialize())

        # Verify pre-test conditions
        assert(self.tdmaComm.commStartTime == None)
        self.tdmaComm.processMeshMsgs(encodedCmd)
        assert(self.tdmaComm.commStartTime == commStartTime)

    def test_executeTDMAComm(self):
        """Test executeTDMAComm method of TDMAComm."""
        testMsg = b'1234567890'
        self.tdmaComm.transmitSlot = 2
        self.tdmaComm.radio.clearRxBuffer()
        # Test times
        times = [0.0, self.tdmaComm.beginRxTime + 0.0001, self.tdmaComm.beginRxTime + 0.5*(self.tdmaComm.endRxTime - self.tdmaComm.beginRxTime), self.tdmaComm.endRxTime + 0.0001]
        times = times + [self.tdmaComm.slotLength + 0.0001, self.tdmaComm.slotLength + self.tdmaComm.beginTxTime + 0.0001, self.tdmaComm.slotLength + 0.5*(self.tdmaComm.endTxTime - self.tdmaComm.beginRxTime), self.tdmaComm.slotLength + self.tdmaComm.endTxTime + 0.0001]
        # Test truth modes
        truthModes = [TDMAMode.init, TDMAMode.receive, TDMAMode.receive, TDMAMode.sleep, TDMAMode.init, TDMAMode.transmit, TDMAMode.transmit, TDMAMode.sleep]   
       
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
                assert(self.tdmaComm.radio.mode == RadioMode.sleep) # receive terminated once end byte received
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

        # BlockRx
        self.setupForBlockTxTest('rx')
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.tdmaMode = TDMAMode.blockRx
        self.tdmaComm.radio.setMode(RadioMode.sleep)
        self.tdmaComm.executeTDMAComm(0.0)
        assert(self.tdmaComm.radio.mode == RadioMode.receive)
        
        # BlockTx
        self.setupForBlockTxTest('tx')
        self.tdmaComm.tdmaMode = TDMAMode.blockTx
        self.tdmaComm.radio.setMode(RadioMode.sleep)
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId
        self.tdmaComm.executeTDMAComm(0.0)
        assert(self.tdmaComm.radio.mode == RadioMode.transmit)
    
    def test_execute(self):
        """Test execute method of TDMAComm."""
        # Test init start
        assert(self.tdmaComm.inited == False)
        self.tdmaComm.commStartTime = time.time()
        self.tdmaComm.execute()
        assert(self.tdmaComm.inited == True)

        # Test TDMA logic executed
        self.tdmaComm.tdmaFailsafe = True
        self.tdmaComm.radio.setMode(RadioMode.sleep)
        self.tdmaComm.frameStartTime = time.time()
        self.tdmaComm.execute()
        assert(self.tdmaComm.radio.mode == RadioMode.receive) # should be listening in failsafe

    # Test block transmit functionality

    def setupForBlockTxTest(self, role):
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.blockTxStatus['length'] = 5
        self.tdmaComm.blockTxStatus['startTime'] = time.time()
        self.nodeParams.frameStartTime = time.time()
        self.nodeParams.tdmaStatus = TDMAStatus.blockTx
        if role == 'tx':
            self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId
        else:   
            self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId + 1
        
