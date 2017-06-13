import serial, time, os.path
from mesh.generic.tdmaComm import TDMAComm, TDMAMode
from mesh.generic.tdmaState import TDMABlockTxStatus, TDMAStatus
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.testCmdProcessor import TestCmdProcessor
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.radio import Radio, RadioMode
from mesh.generic.nodeParams import NodeParams
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.command import Command
from mesh.generic.nodeHeader import packHeader
from mesh.generic.customExceptions import InvalidTDMASlotNumber
from unittests.testConfig import configFilePath, testSerialPort
from mesh.generic.cmds import TDMACmds, TestCmds
from mesh.generic.slipMsg import SLIP_END_TDMA
from mesh.generic.deserialize import deserialize
from unittests.testCmds import testCmds
import pytest

class TestTDMABlockTx:
    def setup_method(self, method):

        if testSerialPort:
            serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        else:
            serialPort = []

        self.nodeParams = NodeParams(configFile=configFilePath)
        self.nodeParams.commStartTime = time.time()
        self.nodeParams.config.commConfig['transmitSlot'] = 1
        self.radio = Radio(serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        commProcessor = CommProcessor([TDMACmdProcessor, TestCmdProcessor], self.nodeParams)
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        self.tdmaComm = TDMAComm(commProcessor, self.radio, msgParser, self.nodeParams)
        self.tdmaComm.nodeParams.frameStartTime = time.time()

    def test_populateBlockResponseList(self):
        """Test populateBlockResponseList method of TDMAComm."""
        # Set node presence flags
        presentNodes = [1,2,3]
        for node in presentNodes:
            self.nodeParams.nodeStatus[node-1].present = True
    
        self.tdmaComm.populateBlockResponseList()
        for node in presentNodes:
            assert(node in self.tdmaComm.blockTxStatus['blockResponseList'])

    
    def test_checkBlockResponse(self):
        """Test checkBlockResponse method of TDMAComm."""
        # Set block response list   
        self.tdmaComm.blockTxStatus['blockResponseList'] = {1: None, 2: None, 3: None}

        # False response test
        self.tdmaComm.blockTxStatus['blockResponseList'][2] = False
        assert(self.tdmaComm.checkBlockResponse() == False) 

        # Waiting for responses test
        self.tdmaComm.blockTxStatus['blockResponseList'][2] = True
        assert(self.tdmaComm.checkBlockResponse() == None) 
        
        # True responses test
        for node in self.tdmaComm.blockTxStatus['blockResponseList']:
            self.tdmaComm.blockTxStatus['blockResponseList'][node] = True
        assert(self.tdmaComm.checkBlockResponse() == True) 
    

    def test_sendDataBlock(self):
        """Test sendDataBlock method of TDMAComm."""
        # Manually set frame start time 
        self.tdmaComm.frameStartTime = time.time()
        
        dataBlock = b'1234567890'*50
        
        self.tdmaComm.sendDataBlock(dataBlock)

        # Check data stored and block tx request sent
        assert(self.tdmaComm.dataBlock == dataBlock) # data block stored
        header, msgContents = deserialize(self.tdmaComm.radio.txBuffer[1:-3], TDMACmds['BlockTxRequest']) # parse only raw message portions of output
        assert(msgContents['blockReqID'] == self.tdmaComm.blockTxStatus['blockReqID'])
        assert(msgContents['startTime'] == self.tdmaComm.blockTxStatus['startTime'])
        assert(msgContents['length'] == self.tdmaComm.blockTxStatus['length'])
        
    def test_monitorBlockTx(self):
        """Test monitorBlockTx method of TDMAComm."""
        # Manually set frame start time 
        self.tdmaComm.frameStartTime = time.time()

        ## Test block pending behavior
        # Check for block request response checks
        self.setupBlockRequest('tx')
        for node in self.tdmaComm.blockTxStatus['blockResponseList']:
            self.tdmaComm.blockTxStatus['blockResponseList'][node] = True
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.confirmed)

        # Check for request timeout
        self.setupBlockRequest('tx')
        self.tdmaComm.frameStartTime += 0.5 * self.nodeParams.config.commConfig['blockTxRequestTimeout'] * self.nodeParams.config.commConfig['frameLength']
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.pending)
        self.tdmaComm.frameStartTime += 0.5 * self.nodeParams.config.commConfig['blockTxRequestTimeout'] * self.nodeParams.config.commConfig['frameLength'] + 0.1
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false)

        # Check for cancel when not confirmed 
        self.setupBlockRequest('rx')
        self.tdmaComm.frameStartTime = self.tdmaComm.blockTxStatus['requestTime']
        self.tdmaComm.frameStartTime += 0.5 * (self.tdmaComm.blockTxStatus['startTime'] - self.tdmaComm.blockTxStatus['requestTime'])
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.pending)
        self.tdmaComm.frameStartTime += 0.5 * (self.tdmaComm.blockTxStatus['startTime'] - self.tdmaComm.blockTxStatus['requestTime'])
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false)
        
        ## Test block confirmed behavior
        # Check for change to active block tx status
        self.setupBlockRequest('rx')
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.confirmed
        self.tdmaComm.frameStartTime = self.tdmaComm.blockTxStatus['requestTime']
        self.tdmaComm.frameStartTime += 0.5 * (self.tdmaComm.blockTxStatus['startTime'] - self.tdmaComm.blockTxStatus['requestTime'])
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.confirmed)
        self.tdmaComm.frameStartTime += 0.5 * (self.tdmaComm.blockTxStatus['startTime'] - self.tdmaComm.blockTxStatus['requestTime'])
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active)
        
        # Check block tx status message sent 
        self.tdmaComm.radio.txBuffer = bytearray()
        self.setupBlockRequest()
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.confirmed
        self.tdmaComm.frameStartTime = self.tdmaComm.blockTxStatus['requestTime']
        self.tdmaComm.monitorBlockTx()
        print(self.tdmaComm.radio.txBuffer)
        header, msgContents = deserialize(self.tdmaComm.radio.txBuffer, TDMACmds['BlockTxStatus'])
        assert(msgContents['blockReqID'] == self.tdmaComm.blockTxStatus['blockReqID'])
        assert(msgContents['startTime'] == self.tdmaComm.blockTxStatus['startTime'])
        assert(msgContents['length'] == self.tdmaComm.blockTxStatus['length'])

        ## Test block active behavior
        # Check for block end from time
        self.setupBlockTxActive()
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active)
        self.tdmaComm.frameStartTime += self.tdmaComm.blockTxStatus['length'] * self.nodeParams.config.commConfig['frameLength']
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false)
        
        # Check for block end from complete flag set
        self.setupBlockTxActive()
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active)
        self.tdmaComm.blockTxStatus['blockTxComplete'] = True
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false)
        
        # Check for block end from status set to nominal
        self.setupBlockTxActive()
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active)
        self.nodeParams.tdmaStatus = TDMAStatus.nominal
        self.tdmaComm.monitorBlockTx()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false)
    

    def test_sendBlock(self):
        """Test sendBlock method of TDMAComm."""
        dataBlock = b'1234567890'*50
        
        # Check for blockTxComplete set if no data block
        assert(self.tdmaComm.blockTxStatus['blockTxComplete'] == False)
        self.tdmaComm.sendBlock()
        assert(self.tdmaComm.blockTxStatus['blockTxComplete'] == True)
                
        ## Test that block is sent in appropriately sized chunks
        self.tdmaComm.blockTxStatus['blockTxComplete'] = False # reset block tx complete flag
        self.nodeParams.config.commConfig['maxBlockTransferSize'] = int(len(dataBlock)/2) + 1 # half of block + 1
        self.tdmaComm.dataBlock = dataBlock
        self.tdmaComm.sendBlock()
        time.sleep(0.1)
        
        # Check that max block transfer sized chunk sent
        assert(self.tdmaComm.dataBlockPos == self.nodeParams.config.commConfig['maxBlockTransferSize'])
        self.tdmaComm.radio.readBytes(True)
        assert(self.tdmaComm.radio.bytesInRxBuffer == self.nodeParams.config.commConfig['maxBlockTransferSize'])
        assert(self.tdmaComm.blockTxStatus['blockTxComplete'] == False)
        
        # Check that rest of block sent
        self.tdmaComm.radio.clearRxBuffer()
        self.tdmaComm.sendBlock()
        time.sleep(0.1)
        assert(self.tdmaComm.dataBlockPos == 0)
        self.tdmaComm.radio.readBytes(True)
        assert(self.tdmaComm.radio.bytesInRxBuffer == int(len(dataBlock)/2) + 1) # half of block + END byte
        assert(self.tdmaComm.blockTxStatus['blockTxComplete'] == True)

    #def test_dumpBlockData(self):
    #    """Test dumpBlockData method of TDMAComm."""
    #    self.tdmaComm.receivedBlockData = b'1234567890'*10
    #    self.tdmaComm.dumpBlockData('./')
    #    assert(len(self.tdmaComm.receivedBlockData) == 0) 

    def test_nominalTDMABlockTx(self):
        """Test TDMA block transfer sequence."""
        # Force init
        self.tdmaComm.meshInited = True
        
        dataBlock = b'1234567890'*50
        self.nodeParams.config.commConfig['maxBlockTransferSize'] = int(len(dataBlock)/2) + 1
        self.tdmaComm.frameStartTime = time.time()
    
        # Set present nodes
        self.nodeParams.nodeStatus[0].present = True
        self.nodeParams.nodeStatus[1].present = True
    
        # Request sending of data block
        self.initiateBlockTransmit()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.pending)  
    
        ## Execute TDMA comm and monitor block transfer process
        # Check for status change to pending
        self.tdmaComm.frameStartTime += self.nodeParams.config.commConfig['frameLength'] 
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.pending)  
        
        # "Send" positive request response from one node
        cmdMsg = Command(TDMACmds['BlockTxRequestResponse'], {'blockReqID': self.tdmaComm.blockTxStatus['blockReqID'], "accept": True}, [TDMACmds['BlockTxRequestResponse'], 1, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        self.tdmaComm.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self.tdmaComm, 'clock': self.nodeParams.clock})
        print(self.tdmaComm.blockTxStatus['blockResponseList'])
        assert(self.tdmaComm.blockTxStatus['blockResponseList'][1] == True) # response list updated
        self.tdmaComm.frameStartTime += self.nodeParams.config.commConfig['frameLength'] 
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.pending)

        # Send remaining positive responses and check for update to confirmed status
        time.sleep(0.1)
        cmdMsg = Command(TDMACmds['BlockTxRequestResponse'], {'blockReqID': self.tdmaComm.blockTxStatus['blockReqID'], "accept": True}, [TDMACmds['BlockTxRequestResponse'], 2, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        self.tdmaComm.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self.tdmaComm, 'clock': self.nodeParams.clock})
        self.tdmaComm.frameStartTime += self.nodeParams.config.commConfig['frameLength'] 
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.confirmed)
        
        # Advance to block start time
        self.tdmaComm.radio.txBuffer = bytearray() # clear tx buffer
        self.tdmaComm.frameStartTime = self.tdmaComm.blockTxStatus['startTime']
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        time.sleep(0.1)
        self.tdmaComm.radio.readBytes(True)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active) # block started
        assert(self.nodeParams.tdmaStatus == TDMAStatus.blockTx) # tdma status updated
        assert(self.tdmaComm.radio.bytesInRxBuffer >= self.nodeParams.config.commConfig['maxBlockTransferSize'])
        assert(self.tdmaComm.blockTxStatus['blockTxComplete'] == False)     

        # Continue sending and check for block tx complete flag
        self.tdmaComm.frameStartTime += self.nodeParams.config.commConfig['frameLength'] 
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        assert(self.tdmaComm.blockTxStatus['blockTxComplete'] == True)      
    
        # Check for transition back to nominal TDMA
        self.tdmaComm.frameStartTime += self.nodeParams.config.commConfig['frameLength'] 
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        assert(self.nodeParams.tdmaStatus == TDMAStatus.nominal)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false)

    def test_rejectedTDMABlockTx(self):
        """Test rejecting block transmit request."""
        # Force init
        self.tdmaComm.meshInited = True
        
        # Start block transmit
        self.initiateBlockTransmit()
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.pending)  
        
        # "Send" negative response from other node
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxRequestResponse'], {'blockReqID': self.tdmaComm.blockTxStatus['blockReqID'], "accept": False}, [TDMACmds['BlockTxRequestResponse'], 2, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        self.tdmaComm.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self.tdmaComm, 'clock': self.nodeParams.clock})
        self.tdmaComm.frameStartTime += self.nodeParams.config.commConfig['frameLength'] 
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false) # request cancelled
        
    def test_blockTxEndTime(self):
        """Test block transmit ended due to block length reached."""
        # Force init
        self.tdmaComm.meshInited = True
        
        # Start block transmit
        self.initiateBlockTransmit()
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.confirmed
        self.tdmaComm.frameStartTime = self.tdmaComm.blockTxStatus['startTime']
        self.tdmaComm.execute(self.tdmaComm.frameStartTime)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active)
        assert(self.nodeParams.tdmaStatus == TDMAStatus.blockTx)
    
        # Advance to block end and check that block terminated
        self.tdmaComm.frameStartTime += self.nodeParams.config.commConfig['frameLength'] * self.tdmaComm.blockTxStatus['length']
        self.tdmaComm.execute(self.nodeParams.frameStartTime)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.false)
        assert(self.nodeParams.tdmaStatus == TDMAStatus.nominal)
        
    def test_processSendBlockDataCmd(self):
        """Test processing of SendBlockData command from GCS."""
        self.tdmaComm.frameStartTime = 0.0 # set a frame start time since main execution is bypassed
 
        # Create TestCmds['SendBlockData'] command
        cmdMsg = Command(TestCmds['SendDataBlock'], {'destId': self.nodeParams.config.nodeId}, [TestCmds['SendDataBlock'], 0, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        
        # Process command and check result
        self.tdmaComm.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeParams.nodeStatus, 'comm': self.tdmaComm})
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.pending)
        assert(self.tdmaComm.dataBlock == b'1234567890'*100)

    def test_nodePresenceUpdate(self):
        """Test that node presence does not timeout during block transmits."""
        self.nodeParams.frameStartTime = time.time()
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId + 1
        self.tdmaComm.blockTxStatus['length'] = 10
        self.tdmaComm.blockTxStatus['startTime'] = self.nodeParams.frameStartTime
        self.nodeParams.tdmaStatus = TDMAStatus.blockTx
        
        # Set present nodes
        self.nodeParams.nodeStatus[1].present = True
        self.nodeParams.nodeStatus[2].present = True
        

        # Propagate time and check that node update time is updated
        self.tdmaComm.execute(0.0)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active)
        assert((self.nodeParams.nodeStatus[1].lastStateUpdateTime - time.time()) <= 0.001)

        time.sleep(5.0)
        self.tdmaComm.execute(0.0)
        assert(self.tdmaComm.blockTxStatus['status'] == TDMABlockTxStatus.active)
        assert((self.nodeParams.nodeStatus[1].lastStateUpdateTime - time.time()) <= 0.001)

    def initiateBlockTransmit(self):
        """Initiate block transmit process."""
        dataBlock = b'1234567890'*50
        self.nodeParams.config.commConfig['maxBlockTransferSize'] = int(len(dataBlock)/2) + 1
        self.tdmaComm.frameStartTime = time.time()
    
        # Set present nodes
        self.nodeParams.nodeStatus[0].present = True
        self.nodeParams.nodeStatus[1].present = True
    
        # Request sending of data block
        self.tdmaComm.sendDataBlock(dataBlock)
    
    def setupBlockTxActive(self):
        self.setupBlockRequest('tx')
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.active
        self.nodeParams.tdmaStatus = TDMAStatus.blockTx
        self.tdmaComm.frameStartTime = self.tdmaComm.blockTxStatus['startTime']

    def setupBlockRequest(self, role='tx'):
        self.tdmaComm.resetBlockTxStatus()
        currentTime = time.time()
        self.tdmaComm.blockTxStatus['blockReqID'] = 5
        self.tdmaComm.blockTxStatus['startTime'] = int(currentTime + self.nodeParams.config.commConfig['minBlockTxDelay'] * self.nodeParams.config.commConfig['frameLength'])
        self.tdmaComm.blockTxStatus['length'] = 5
        
        # Set block response list   
        self.tdmaComm.blockTxStatus['blockResponseList'] = {1: None, 2: None, 3: None}

        if role == 'tx': # This node transmitting
            self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId
        else:
            self.tdmaComm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId + 1
        self.tdmaComm.blockTxStatus['status'] = TDMABlockTxStatus.pending
        self.tdmaComm.blockTxStatus['requestTime'] = currentTime

