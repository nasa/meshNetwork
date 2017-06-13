import serial, time
from mesh.generic.tdmaComm import TDMAComm, TDMAMode
from mesh.generic.tdmaState import TDMABlockTxStatus, TDMAStatus
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.radio import Radio, RadioMode
from mesh.generic.nodeParams import NodeParams
from mesh.generic.commProcessor import CommProcessor
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
        commProcessor = CommProcessor([TDMACmdProcessor], self.nodeParams)
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        self.tdmaComm = TDMAComm(commProcessor, self.radio, msgParser, self.nodeParams)
    
    def test_resetTDMASlot(self):
        """Test resetTDMASlot method of TDMAComm."""
        frameTime = self.tdmaComm.slotLength
        currentTime = time.time()
        print("Slot length:", self.tdmaComm.slotLength)
        # Test resetting through range of valid slots
        for i in range(self.tdmaComm.maxNumSlots):
            frameTime = self.tdmaComm.slotLength*i
            self.tdmaComm.resetTDMASlot(frameTime)
            
            # Verify slot time is within bounds
            assert(self.tdmaComm.slotTime >= 0)
            assert(self.tdmaComm.slotTime < self.tdmaComm.slotLength)
        
            # Verify correct slot number
            assert(self.tdmaComm.slotNum == i + 1)
            
            print("Frame time/Slot number/Slot time/Slot start time:", frameTime, self.tdmaComm.slotNum, self.tdmaComm.slotTime, self.tdmaComm.slotStartTime)
        
        # Test with frame time greater than cycle time
        frameTime = self.tdmaComm.cycleLength + 0.1
        self.tdmaComm.resetTDMASlot(frameTime)
        assert(self.tdmaComm.slotNum == self.tdmaComm.maxNumSlots)

        # Test with non-int slot number
        with pytest.raises(InvalidTDMASlotNumber):
            self.tdmaComm.resetTDMASlot(frameTime, 1.1)
        
        # Test with invalid slot number
        with pytest.raises(InvalidTDMASlotNumber):
            self.tdmaComm.resetTDMASlot(frameTime, self.tdmaComm.maxNumSlots+1) 


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
            elif mode == TDMAMode.receive:
                assert(self.tdmaComm.receiveComplete == True) # check receiveComplete status not reset
                assert(self.tdmaComm.transmitComplete == False) # check transmitComplete status reset


    @pytest.mark.skipif(testSerialPort == [], reason="No serial port")
    def test_initComm(self):
        """Test initComm method of TDMAComm."""
        # Confirm radio is off
        assert(self.radio.mode == RadioMode.off)

        # Init comm and check radio is now in receive
        self.tdmaComm.initComm()
        assert(self.radio.mode == RadioMode.receive)
        
        # Send MeshStatus message and confirm that commStartTime is updated
        meshStatusMsg = packHeader(testCmds[TDMACmds['MeshStatus']].header) + testCmds[TDMACmds['MeshStatus']].body
        commStartTime = testCmds[TDMACmds['MeshStatus']].cmdData['commStartTimeSec']
        assert(self.nodeParams.commStartTime != commStartTime) # check that comm start times do not match
        self.tdmaComm.bufferTxMsg(meshStatusMsg)
        self.tdmaComm.sendBuffer()
        time.sleep(0.1)
        self.tdmaComm.initComm()
        assert(self.nodeParams.commStartTime == commStartTime) # check that comm start times now match

    def test_updateMode(self):
        """Test updateMode method of TDMAComm."""
        
        # Test slot change
        self.tdmaComm.slotNum = 1
        self.tdmaComm.updateMode(self.tdmaComm.slotLength)
        assert(self.tdmaComm.slotNum == 2)

        # Test transition to failsafe mode
        self.nodeParams.tdmaFailsafe = True
        assert(self.tdmaComm.tdmaMode != TDMAMode.failsafe)
        self.tdmaComm.updateMode(0.0)
        assert(self.tdmaComm.tdmaMode == TDMAMode.failsafe)
        self.nodeParams.tdmaFailsafe = False
        
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
        
        
    def test_sendMsg(self):
        """Test sendMsg method of TDMAComm."""
        # Send message and check for END_TDMA byte
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.transmitComplete = False
        self.tdmaComm.radio.setMode(RadioMode.transmit)
        self.tdmaComm.tdmaMode = TDMAMode.transmit
        testMsg = b'1234567890'
        self.tdmaComm.bufferTxMsg(testMsg)
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
    
        self.tdmaComm.readBytes()
        serBytes = self.tdmaComm.radio.getRxBytes()
        assert(serBytes[-1:] == SLIP_END_TDMA)
    
        # Check for radio mode change to sleep and transmit complete flag set
        #assert(self.tdmaComm.radio.mode == RadioMode.sleep)
        assert(self.tdmaComm.transmitComplete == True)

        # Test command relay buffer
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.cmdRelayBuffer = testMsg
        self.tdmaComm.sendMsg()
        time.sleep(0.1)
        self.tdmaComm.readBytes()
        serBytes = self.tdmaComm.radio.getRxBytes()
        assert(serBytes == testMsg + SLIP_END_TDMA)
        
    def test_readMsg(self):
        """Test readMsg method of TDMAComm."""
        # Send message without END_TDMA byte and check for False returned
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.rxBufferReadPos = 0
        testMsg = b'1234567890'
        self.tdmaComm.sendBytes(testMsg)
        time.sleep(0.1)
        assert(self.tdmaComm.readMsg() == False)

        # Send message with END_TDMA byte and check for True returned
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.rxBufferReadPos = 0
        self.tdmaComm.sendBytes(testMsg + SLIP_END_TDMA)    
        time.sleep(0.1)
        out = self.tdmaComm.readMsg()
        print("Read status:", out, self.tdmaComm.rxBufferReadPos)
        #assert(self.tdmaComm.readMsg() == True)

    def test_execute(self):
        """Test execute method of TDMAComm."""
        testMsg = b'1234567890'
        self.tdmaComm.transmitSlot = 2
        self.tdmaComm.radio.clearRxBuffer()
        # Test times
        times = [0.0, self.tdmaComm.beginRxTime + 0.0001, self.tdmaComm.beginRxTime + 0.5*(self.tdmaComm.endRxTime - self.tdmaComm.beginRxTime), self.tdmaComm.endRxTime + 0.0001]
        times = times + [self.tdmaComm.slotLength + 0.0001, self.tdmaComm.slotLength + self.tdmaComm.beginTxTime + 0.0001, self.tdmaComm.slotLength + 0.5*(self.tdmaComm.endTxTime - self.tdmaComm.beginRxTime), self.tdmaComm.slotLength + self.tdmaComm.endTxTime + 0.0001]
        # Test truth modes
        truthModes = [TDMAMode.init, TDMAMode.receive, TDMAMode.receive, TDMAMode.sleep, TDMAMode.init, TDMAMode.transmit, TDMAMode.transmit, TDMAMode.sleep]   
       
        # Force init
        self.tdmaComm.meshInited = True
        self.nodeParams.commStartTime = 0.0
        self.tdmaComm.init(0.0)
        self.tdmaComm.frameStartTime = 0.0
 
        # Loop through test times and verify conditions
        for i in range(len(times)):
            print("Test time/Expected mode:", times[i], truthModes[i])
            self.tdmaComm.execute(times[i])
            assert(self.tdmaComm.tdmaMode == truthModes[i])
            # Receive slot actions
            if i == 1: # prep for read
                assert(self.tdmaComm.radio.mode == RadioMode.receive)
                self.tdmaComm.sendBytes(testMsg + SLIP_END_TDMA) # send bytes to read
                time.sleep(0.1)
            if i == 2: # post receive 
                assert(self.tdmaComm.radio.mode == RadioMode.sleep)
    
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
        self.tdmaComm.execute(0.0)
        assert(self.tdmaComm.radio.mode == RadioMode.receive)

        # BlockRx
        self.setupForBlockTxTest('rx')
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.tdmaMode = TDMAMode.blockRx
        self.tdmaComm.radio.setMode(RadioMode.sleep)
        self.tdmaComm.execute(0.0)
        assert(self.tdmaComm.radio.mode == RadioMode.receive)
        
        # BlockTx
        self.setupForBlockTxTest('tx')
        self.tdmaComm.tdmaMode = TDMAMode.blockTx
        self.tdmaComm.radio.setMode(RadioMode.sleep)
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId
        self.tdmaComm.execute(0.0)
        assert(self.tdmaComm.radio.mode == RadioMode.transmit)
        
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
        
