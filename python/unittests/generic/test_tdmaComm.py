import serial, time, math
from mesh.generic.command import Command
from mesh.generic.tdmaComm import TDMAComm, TDMAMode
from mesh.generic.tdmaState import TDMABlockTxStatus, TDMAStatus
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.radio import Radio, RadioMode
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeHeader import packHeader
from mesh.generic.customExceptions import InvalidTDMASlotNumber
from unittests.testConfig import configFilePath, testSerialPort
from mesh.generic.cmds import TDMACmds
from mesh.generic.slipMsg import SLIP_END_TDMA
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
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
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
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': startTime, 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        self.tdmaComm.bufferTxMsg(cmd.serialize())
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
        assert(self.tdmaComm.nodeParams.nodeStatus[self.tdmaComm.nodeParams.config.nodeId-1].timeOffset == 127)
        assert(self.tdmaComm.timeOffsetTimer != None)

        # Test timer clear
        ret = self.tdmaComm.checkTimeOffset(self.nodeParams.config.commConfig['operateSyncBound'])
        assert(self.tdmaComm.timeOffsetTimer == None)

        # Elapse offset timer
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
        assert(self.tdmaComm.timeOffsetTimer == None) # no offset timer running
        
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
        assert(self.tdmaComm.timeOffsetTimer != None) # offset timer started
       
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
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': commStartTime, 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        assert(self.tdmaComm.commStartTime != commStartTime) # check that comm start times do not match
        self.tdmaComm.bufferTxMsg(cmd.serialize())
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
        # Test for frame exceedance
        self.tdmaComm.frameStartTime = time.time() - self.tdmaComm.frameLength - 0.011
        assert(self.tdmaComm.frameExceedanceCount == 0)
        self.tdmaComm.sleep()
        assert(self.tdmaComm.frameExceedanceCount == 1)

    def test_sendTDMACmds(self):
        """Test sendTDMACmds method of TDMAComm."""
        self.tdmaComm.commStartTime = time.time();
        flooredStartTime = math.floor(self.tdmaComm.commStartTime)
        self.tdmaComm.tdmaCmds.update({TDMACmds['MeshStatus']: Command(TDMACmds['MeshStatus'], {'commStartTimeSec': flooredStartTime, 'status': self.tdmaComm.tdmaStatus}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId], 0.500)})

        # Check command properly buffered
        assert(len(self.tdmaComm.radio.txBuffer) == 0)
        self.tdmaComm.sendTDMACmds()
        assert(len(self.tdmaComm.radio.txBuffer) > 0)

        # Wait for resend
        self.tdmaComm.radio.txBuffer = bytearray()
        time.sleep(0.1)
        assert(len(self.tdmaComm.radio.txBuffer) == 0)
        self.tdmaComm.sendTDMACmds() # should not send
        assert(len(self.tdmaComm.radio.txBuffer) == 0) 
        time.sleep(0.4)
        self.tdmaComm.sendTDMACmds() # should send
        assert(len(self.tdmaComm.radio.txBuffer) > 0)

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
        assert(self.tdmaComm.transmitComplete == True) # check that transmitComplete flag set

        # Test transmission of periodic commands
        serBytes = self.tdmaComm.radio.getRxBytes() # clear incoming bytes
        assert(len(self.tdmaComm.cmdBuffer) == 0)
        assert(len(self.tdmaComm.cmdRelayBuffer) == 0)
        cmd = Command(TDMACmds['MeshStatus'], {'commStartTimeSec': int(time.time()), 'status': TDMAStatus.nominal}, [TDMACmds['MeshStatus'], self.nodeParams.config.nodeId])
        self.tdmaComm.tdmaCmds[TDMACmds['MeshStatus']] = cmd
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        serBytes = self.tdmaComm.radio.getRxBytes()
        assert(len(serBytes) > 0)
        assert(serBytes[-1:] == SLIP_END_TDMA) # check for end of message indicator

        # Test command relay buffer
        testMsg = b'1234567890'
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.cmdRelayBuffer = testMsg
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        serBytes = self.tdmaComm.radio.getRxBytes()
        assert(serBytes == testMsg + SLIP_END_TDMA)
       
        # Test command buffer
        self.tdmaComm.radio.clearRxBuffer()
        testCmd = {'bytes': b'12345'}
        self.tdmaComm.cmdBuffer['key1'] = testCmd
        self.tdmaComm.sendMsg()
        assert(len(self.tdmaComm.cmdBuffer) == 0) # command buffer flushed out
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        assert(len(self.tdmaComm.radio.getRxBytes()) > 0)

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
        self.tdmaComm.sendBytes(testMsg + SLIP_END_TDMA)    
        time.sleep(0.1)
        out = self.tdmaComm.readMsgs()
        print("Read status:", out, self.tdmaComm.rxBufferReadPos)
        assert(out == True)


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
                self.tdmaComm.sendBytes(testMsg + SLIP_END_TDMA) # send bytes to read
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
        
