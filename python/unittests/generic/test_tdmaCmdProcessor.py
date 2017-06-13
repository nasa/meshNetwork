import random, time
from struct import calcsize
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor, validateBlockTxRequest
from mesh.generic.tdmaState import TDMABlockTxStatus
from mesh.generic.cmds import TDMACmds
from mesh.generic.command import Command
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeParams import NodeParams
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.radio import Radio
from mesh.generic.nodeState import NodeState
from mesh.generic.tdmaComm import TDMAComm
from mesh.generic.nodeHeader import packHeader, headers
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath

cmdsToTest = [TDMACmds['TimeOffsetSummary'], TDMACmds['TimeOffset'], TDMACmds['MeshStatus']]

class TestTDMACmdProcessor:
    
    def setup_method(self, method):
        self.nodeStatus = [NodeState(i+1) for i in range(5)]
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.commProcessor = CommProcessor([TDMACmdProcessor], self.nodeParams)
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        radio = Radio([], {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        self.comm = TDMAComm(self.commProcessor, radio, msgParser, self.nodeParams)
    
    def test_validateBlockTxRequest(self):
        """Test validateBlockTxRequest  method of TDMACmdProcessor."""
        # Test request rejected if start time passed
        contents = {'startTime': time.time() - 1.0, 'length': self.nodeParams.config.commConfig['maxTxBlockSize']}
        assert(validateBlockTxRequest(contents, [], self.nodeParams) == False)

        # Test request rejected if block too long           
        contents = {'startTime': time.time() + 1.0, 'length': self.nodeParams.config.commConfig['maxTxBlockSize'] + 1}
        assert(validateBlockTxRequest(contents, [], self.nodeParams) == False)

        # Test for request acceptance   
        contents = {'startTime': time.time() + 1.0, 'length': self.nodeParams.config.commConfig['maxTxBlockSize']}
        assert(validateBlockTxRequest(contents, [], self.nodeParams) == True)

    def test_processMsg(self):
        """Test processMsg method of TDMACmdProcessor."""
    
        # Test processing of all TDMACmds
        for cmdId in cmdsToTest:    
            cmdMsg = packHeader(testCmds[cmdId].header) + testCmds[cmdId].body
            self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
            if cmdId == TDMACmds['TimeOffset']:
                sourceId = testCmds[cmdId].header['header']['sourceId']
                assert(self.nodeStatus[sourceId-1].timeOffset == testCmds[cmdId].body[0]/100.0)
            elif cmdId == TDMACmds['TimeOffsetSummary']:
                for i in range(len(testCmds[cmdId].cmdData['nodeStatus'])):
                    assert(self.nodeStatus[i].timeOffset == testCmds[cmdId].cmdData['nodeStatus'][i].timeOffset)    
            elif cmdId == TDMACmds['MeshStatus']:
                assert(self.nodeParams.commStartTime == testCmds[cmdId].cmdData['commStartTimeSec'])
        
        # Resend and test that commStartTime is not updated once it has previously been set
        cmdId = TDMACmds['MeshStatus']
        self.nodeParams.commStartTime = testCmds[cmdId].cmdData['commStartTimeSec'] - 1
        cmdMsg = packHeader(testCmds[cmdId].header) + testCmds[cmdId].body
        self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
        assert(self.nodeParams.commStartTime != testCmds[cmdId].cmdData['commStartTimeSec'])
    
    def test_blockTxCmdsProcessing(self):
        """Test processing of block transmit related commands."""
        self.nodeParams.commStartTime = self.nodeParams.clock.getTime() - 1.0
        blockReqID = random.randint(1,255) # just a random "unique" number 
        startTime = int(self.nodeParams.clock.getTime() + 10.0)
        length = self.nodeParams.config.commConfig['maxTxBlockSize']
        txNode = 1      

        ## TDMACmds['BlockTxRequest']
        cmdMsg = Command(TDMACmds['BlockTxRequest'], {'blockReqID': blockReqID, 'startTime': startTime, 'length': length}, [TDMACmds['BlockTxRequest'], txNode, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        
        # Process and check results 
        self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
        assert(len(self.comm.radio.txBuffer) == calcsize(CmdDict[TDMACmds['BlockTxRequestResponse']].packFormat) + calcsize(headers['NodeHeader']['format'])) # response sent
        assert(self.comm.blockTxStatus['blockReqID'] == blockReqID)
        assert(self.comm.blockTxStatus['status'] == TDMABlockTxStatus.pending)
        assert(self.comm.blockTxStatus['txNode'] == txNode)
        assert(self.comm.blockTxStatus['startTime'] == startTime)
        assert(self.comm.blockTxStatus['length'] == length)
        
        ## TDMACmds['BlockTxConfirmed']
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxConfirmed'], {'blockReqID': blockReqID}, [TDMACmds['BlockTxConfirmed'], txNode, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
        assert(self.comm.blockTxStatus['status'] == TDMABlockTxStatus.confirmed) # status updated to confirmed

        ## TDMACmds['BlockTxStatus']
        self.comm.resetBlockTxStatus()
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxStatus'], {'blockReqID': blockReqID, 'startTime': startTime, 'length': length}, [TDMACmds['BlockTxStatus'], txNode, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        # Check status updated
        self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
        assert(len(self.comm.radio.txBuffer) == calcsize(CmdDict[TDMACmds['BlockTxRequestResponse']].packFormat) + calcsize(headers['NodeHeader']['format'])) # response sent
        assert(self.comm.blockTxStatus['blockReqID'] == blockReqID)
        assert(self.comm.blockTxStatus['status'] == TDMABlockTxStatus.confirmed)
        assert(self.comm.blockTxStatus['txNode'] == txNode)
        assert(self.comm.blockTxStatus['startTime'] == startTime)
        assert(self.comm.blockTxStatus['length'] == length)

        # Check status updated to confirmed if only pending
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxStatus'], {'blockReqID': blockReqID, 'startTime': startTime, 'length': length}, [TDMACmds['BlockTxStatus'], txNode, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime()) # update command counter
        self.comm.blockTxStatus['status'] = TDMABlockTxStatus.pending
        self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
        assert(self.comm.blockTxStatus['status'] == TDMABlockTxStatus.confirmed)

        ## TDMACmds['BlockTxRequestResponse']
        time.sleep(0.01)
        self.comm.resetBlockTxStatus()
        self.comm.blockTxStatus['txNode'] = self.nodeParams.config.nodeId # this node requested block transfer
        self.comm.blockTxStatus['status'] = TDMABlockTxStatus.pending
        cmdMsg = Command(TDMACmds['BlockTxRequestResponse'], {'blockReqID': blockReqID, "accept": True}, [TDMACmds['BlockTxRequestResponse'], 1, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        print(self.nodeParams.config.nodeId)
        self.nodeParams.nodeStatus[0].present = True # mark another node as present
        self.comm.populateBlockResponseList() # create block response list

        # Test acceptance marked
        self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
        assert(self.comm.blockTxStatus['blockResponseList'][1] == True)

        # Test rejection marked
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxRequestResponse'], {'blockReqID': blockReqID, "accept": False}, [TDMACmds['BlockTxRequestResponse'], 1, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        self.commProcessor.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock})
        assert(self.comm.blockTxStatus['blockResponseList'][1] == False)
