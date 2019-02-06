import random, time
from struct import calcsize
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor, validateBlockTxRequest
from mesh.generic.tdmaState import TDMABlockTxStatus
from mesh.generic.cmds import TDMACmds
from mesh.generic.command import Command
from mesh.generic.cmdDict import CmdDict
from mesh.generic.nodeParams import NodeParams
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.radio import Radio
from mesh.generic.nodeState import NodeState
from mesh.generic.tdmaComm import TDMAComm
from mesh.generic.nodeHeader import packHeader, headers
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath

cmdsToTest = [TDMACmds['MeshStatus'], TDMACmds['TimeOffset'], TDMACmds['LinkStatus']]

class TestTDMACmdProcessor:
    
    def setup_method(self, method):
        self.nodeStatus = [NodeState(i+1) for i in range(5)]
        self.nodeParams = NodeParams(configFile=configFilePath)
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        radio = Radio([], {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        self.comm = TDMAComm([TDMACmdProcessor], radio, msgParser, self.nodeParams)
    
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
            assert(self.comm.processMsg(testCmds[cmdId].serialize(), args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
            if cmdId == TDMACmds['TimeOffset']:
                sourceId = testCmds[cmdId].header['header']['sourceId']
                assert(self.nodeStatus[sourceId-1].timeOffset == testCmds[cmdId].cmdData['nodeStatus'].timeOffset) # verify time offset parsed correctly
            elif cmdId == TDMACmds['MeshStatus']:
                assert(self.comm.commStartTime == testCmds[cmdId].cmdData['commStartTimeSec']) # comm start time stored
            elif cmdId == TDMACmds['LinkStatus']:
                msgNodeId = testCmds[cmdId].cmdData['nodeId']
                for i in range(0, self.nodeParams.config.maxNumNodes):
                    assert(self.nodeParams.linkStatus[msgNodeId-1][i] == testCmds[cmdId].cmdData['linkStatus'][msgNodeId-1][i])
        
        # Resend and test that commStartTime is not updated once it has previously been set
        cmdId = TDMACmds['MeshStatus']
        self.comm.commStartTime = testCmds[cmdId].cmdData['commStartTimeSec'] - 1
        assert(self.comm.processMsg(testCmds[cmdId].serialize(), args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
        assert(self.comm.commStartTime != testCmds[cmdId].cmdData['commStartTimeSec']) # comm start time should not have been updated
    
    def test_blockTxCmdsProcessing(self):
        """Test processing of block transmit related commands."""
        return # skip this test    
    
        self.comm.commStartTime = self.nodeParams.clock.getTime() - 1.0
        blockReqID = random.randint(1,255) # just a random "unique" number 
        startTime = int(self.nodeParams.clock.getTime() + 10.0)
        length = self.nodeParams.config.commConfig['maxTxBlockSize']
        txNode = 1      

        ## TDMACmds['BlockTxRequest']
        cmdMsg = Command(TDMACmds['BlockTxRequest'], {'blockReqID': blockReqID, 'startTime': startTime, 'length': length}, [TDMACmds['BlockTxRequest'], txNode, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        
        # Process and check results 
        assert(self.comm.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
        assert(len(self.comm.radio.txBuffer) == calcsize(CmdDict[TDMACmds['BlockTxRequestResponse']].packFormat) + calcsize(headers['NodeHeader']['format'])) # response sent
        assert(self.comm.blockTxStatus['blockReqID'] == blockReqID)
        assert(self.comm.blockTxStatus['status'] == TDMABlockTxStatus.pending)
        assert(self.comm.blockTxStatus['txNode'] == txNode)
        assert(self.comm.blockTxStatus['startTime'] == startTime)
        assert(self.comm.blockTxStatus['length'] == length)
        
        ## TDMACmds['BlockTxConfirmed']
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxConfirmed'], {'blockReqID': blockReqID}, [TDMACmds['BlockTxConfirmed'], txNode, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        assert(self.comm.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
        assert(self.comm.blockTxStatus['status'] == TDMABlockTxStatus.confirmed) # status updated to confirmed

        ## TDMACmds['BlockTxStatus']
        self.comm.resetBlockTxStatus()
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxStatus'], {'blockReqID': blockReqID, 'startTime': startTime, 'length': length}, [TDMACmds['BlockTxStatus'], txNode, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        # Check status updated
        assert(self.comm.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
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
        assert(self.comm.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
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
        assert(self.comm.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
        assert(self.comm.blockTxStatus['blockResponseList'][1] == True)

        # Test rejection marked
        time.sleep(0.01)
        cmdMsg = Command(TDMACmds['BlockTxRequestResponse'], {'blockReqID': blockReqID, "accept": False}, [TDMACmds['BlockTxRequestResponse'], 1, self.nodeParams.get_cmdCounter()]).serialize(self.nodeParams.clock.getTime())
        assert(self.comm.processMsg(cmdMsg, args = {'nodeStatus': self.nodeStatus, 'comm': self.comm, 'clock': self.nodeParams.clock}) == True)
        assert(self.comm.blockTxStatus['blockResponseList'][1] == False)
