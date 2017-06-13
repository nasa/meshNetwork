from mesh.generic.nodeParams import NodeParams
from mesh.generic.tdmaComm import TDMAComm
from mesh.generic.cmdProcessor import checkCmdCounter
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.commProcessor import CommProcessor
from mesh.generic.cmds import PixhawkCmds
from mesh.generic.nodeHeader import packHeader
from unittests.testHelpers import createEncodedMsg
from copy import deepcopy
from unittests.testCmds import testCmds
from unittests.testConfig import configFilePath

class TestCmdProcessor:
    
    def setup_method(self, method):
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.commProcessor = CommProcessor([], self.nodeParams)
        msgParser = SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax})
        self.comm = TDMAComm([], [], msgParser, self.nodeParams)
        #self.comm = TDMAComm([], [], [], self.nodeParams)
    
    def test_checkCmdCounter(self):
        """Test checkCmdCounter method."""

        # Check that command relay buffer is empty
        assert(self.comm.cmdRelayBuffer == bytearray())

        ### Test method with command that includes a command counter
        cmdMsg = packHeader(testCmds[PixhawkCmds['GCSCmd']].header) + testCmds[PixhawkCmds['GCSCmd']].body
        checkCmdCounter(self.commProcessor, testCmds[PixhawkCmds['GCSCmd']].header['header'], cmdMsg, self.comm)
        encodedMsg = createEncodedMsg(cmdMsg)
        assert(self.comm.cmdRelayBuffer == encodedMsg)
 
        # Resend with new counter to check cmd is appended to buffer
        cmdCounter = testCmds[PixhawkCmds['GCSCmd']].header['header']['cmdCounter'] 
        header, cmdMsg = self.updateCmdCounterValue(cmdCounter+1, deepcopy(testCmds[PixhawkCmds['GCSCmd']].header), testCmds[PixhawkCmds['GCSCmd']].body)
        checkCmdCounter(self.commProcessor, header['header'], cmdMsg, self.comm)
        encodedMsg2 = createEncodedMsg(cmdMsg)
        assert(self.comm.cmdRelayBuffer == encodedMsg + encodedMsg2)
    
        ## Test various counter values to test acceptance behavior
        # Command counter == 1, stored counter == 0
        self.comm.cmdRelayBuffer = bytearray()
        self.nodeParams.cmdHistory.append(0) # place known cmd counter value in history
        header, cmdMsg = self.updateCmdCounterValue(1, deepcopy(testCmds[PixhawkCmds['GCSCmd']].header), testCmds[PixhawkCmds['GCSCmd']].body)
        checkCmdCounter(self.commProcessor, header['header'], cmdMsg, self.comm)
        assert(len(self.comm.cmdRelayBuffer) > 0) # cmd put in relay buffer 

        # Command counter == 1, stored counter == 1
        self.comm.cmdRelayBuffer = bytearray()
        checkCmdCounter(self.commProcessor, header['header'], cmdMsg, self.comm)
        assert(len(self.comm.cmdRelayBuffer) == 0) # cmd not put in relay buffer    
        
        # Command counter == 255, stored counter == 1
        self.comm.cmdRelayBuffer = bytearray()
        header, cmdMsg = self.updateCmdCounterValue(255, deepcopy(testCmds[PixhawkCmds['GCSCmd']].header), testCmds[PixhawkCmds['GCSCmd']].body)
        checkCmdCounter(self.commProcessor, header['header'], cmdMsg, self.comm)
        assert(len(self.comm.cmdRelayBuffer) > 0) # cmd put in relay buffer 
    
        # Command counter == 1, stored counter == 255
        header, cmdMsg = self.updateCmdCounterValue(1, deepcopy(testCmds[PixhawkCmds['GCSCmd']].header), testCmds[PixhawkCmds['GCSCmd']].body)
        checkCmdCounter(self.commProcessor, header['header'], cmdMsg, self.comm)
        assert(len(self.comm.cmdRelayBuffer) > 0) # cmd put in relay buffer 

        # Command counter == cmdCounterThreshold, storedcounter == 255 (DEPRECATED)
        #self.nodeParams.set_cmdCounter(255)
        #self.comm.cmdRelayBuffer = bytearray()
        #header, cmdMsg = self.updateCmdCounterValue(self.nodeParams.cmdCounterThreshold, deepcopy(testCmds[PixhawkCmds['GCSCmd']].header), testCmds[PixhawkCmds['GCSCmd']].body)
        #assert(len(self.comm.cmdRelayBuffer) == 0) # cmd not put in relay buffer    
        

        ### Send command that should not be relayed
        self.comm.cmdRelayBuffer = bytearray()
        self.nodeParams._cmdCounter = 0
        cmdMsg = packHeader(testCmds[PixhawkCmds['FormationCmd']].header) + testCmds[PixhawkCmds['FormationCmd']].body
        checkCmdCounter(self.commProcessor, testCmds[PixhawkCmds['FormationCmd']].header['header'], cmdMsg, self.comm)
        assert(len(self.comm.cmdRelayBuffer) == 0) # cmd not put in relay buffer    
        

    def updateCmdCounterValue(self, newCounter, header, body):
        header['header']['cmdCounter'] = newCounter
        return header, packHeader(header) + body
        
