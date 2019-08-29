from mesh.generic.nodeParams import NodeParams
from mesh.generic.radio import Radio
from mesh.generic.msgParser import MsgParser
from mesh.generic.hdlcMsg import HDLCMsg
from mesh.generic.tdmaCmdProcessor import TDMACmdProcessor
from mesh.generic.tdmaComm import TDMAComm
from mesh.generic.meshController import MeshController, MeshMsg, MeshMsgType, NetworkPoll, VoteDecision, NetworkVote
from mesh.generic.cmds import TDMACmds, NodeCmds
from unittests.testConfig import configFilePath, testSerialPort
import pytest, time

class TestTDMAComm:
    def setup_method(self, method):

        self.nodeParams = NodeParams(configFile=configFilePath)
        self.nodeParams.config.commConfig['transmitSlot'] = 1
        self.radio = Radio(None, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
        msgParser = MsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax}, HDLCMsg(256))
        self.tdmaComm = TDMAComm([TDMACmdProcessor], self.radio, msgParser, self.nodeParams)
    
        # Test article
        self.meshController = MeshController(self.nodeParams, self.tdmaComm)
    
    def test_getBlockRequestId(self):
        """Test getBlockRequestId method of MeshController."""
        initialCounterValue = self.meshController.blockReqIdCounter

        # Test getting new block request id counter
        newCounter = self.meshController.getBlockRequestId()
        assert(newCounter == initialCounterValue + 1)

        # Test request counter value wrapping
        self.meshController.blockReqIdCounter = 255
        newCounter = self.meshController.getBlockRequestId()
        assert(newCounter == 1)

    def test_sendDataBlock(self):
        """Test sendDataBlock method of MeshController."""
        blockTxBytes = b'1234567890'*10        
        destId = 5

        # Test acceptance of block tx request from host
        assert(TDMACmds['BlockTxRequest'] not in self.tdmaComm.tdmaCmds)
        response = self.meshController.sendDataBlock(destId, blockTxBytes)
        assert(response == True)
        assert(self.meshController.blockTxData == blockTxBytes)
        assert(TDMACmds['BlockTxRequest'] in self.tdmaComm.tdmaCmds)
        assert(self.meshController.blockTxReqPending == True)

        # Test rejection when request already pending
        assert(self.meshController.blockTxAccepted == False)
        response = self.meshController.sendDataBlock(destId, blockTxBytes)
        assert(response == False)
       
        # Test rejection if a previous request has already been accepted by network
        self.meshController.blockTxReqPending = False
        self.meshController.blockTxAccepted = True 
        response = self.meshController.sendDataBlock(destId, blockTxBytes)
        assert(response == False)

    def test_sendMsg(self):
        """Test sendMsg method of MeshController."""
        destId = 5
        
        # Test message that meets size restriction
        assert(len(self.tdmaComm.meshQueueIn) == 0)
        msg = b'1' * self.nodeParams.config.commConfig['msgPayloadMaxLength']
        assert(self.meshController.sendMsg(destId, msg) == True)
        assert(len(self.tdmaComm.meshQueueIn) == 1) # message added to queue
        assert(self.tdmaComm.meshQueueIn[0].msgBytes == msg)
        assert(self.tdmaComm.meshQueueIn[0].destId == destId)

        # Test rejection of message that is too large
        msg = b'2' * (self.nodeParams.config.commConfig['msgPayloadMaxLength'] + 1)
        assert(self.meshController.sendMsg(destId, msg) == False)
        assert(len(self.tdmaComm.meshQueueIn) == 1) # message not added to queue

    def test_getMsgs(self):
        """Test getMsgs method of MeshController."""        
        meshTraffic = b'1234567890'
        blockTxData = b'111222333444555666777888999000'

        # Test retrieval of received messages
        self.meshController.meshMsgs.append(MeshMsg(MeshMsgType.CmdResponse))
        self.tdmaComm.hostBuffer = meshTraffic
        self.tdmaComm.blockTxOut = {'dataComplete': True, 'data': blockTxData}

        msgs = self.meshController.getMsgs()
        assert(len(msgs) == 3)
        assert(msgs[0].msgType == MeshMsgType.CmdResponse)
        assert(msgs[1].msgType == MeshMsgType.MsgBytes)
        assert(msgs[1].msgBytes == meshTraffic)
        assert(msgs[2].msgType == MeshMsgType.BlockData)
        assert(msgs[2].status == True)
        assert(msgs[2].msgBytes == blockTxData)

        # Test return of nothing
        msgs = self.meshController.getMsgs()
        assert(len(msgs) == 0)

    def test_processNetworkMsgs(self):
        """Test processNetworkMsgs method of MeshController."""
        destId = 1
        sourceId = 2
        cmdId1 = 100
        cmdCounter1 = 999
        cmdId2 = 101
        cmdCounter2 = 1000

        # Test poll creation
        self.meshController.comm.networkMsgQueue = [{'msgContents': {'destId': destId}, 'header': {'sourceId': sourceId, 'cmdId': cmdId1, 'cmdCounter': cmdCounter1}}, {'msgContents': {'dummyValue': 1}, 'header': {'sourceId': sourceId, 'cmdId': cmdId2, 'cmdCounter': cmdCounter2}}]

        assert(len(self.meshController.networkPolls) == 0)
        self.meshController.processNetworkMsgs()
        assert(len(self.meshController.networkPolls) == 2)
        assert(len(self.meshController.comm.networkMsgQueue) == 0)
        
        # Verify poll contents
        assert(self.meshController.networkPolls[0].cmdId == cmdId1)
        assert(self.meshController.networkPolls[0].cmdCounter == cmdCounter1)
        assert(self.meshController.networkPolls[0].exclusions == [destId])
        assert(self.meshController.networkPolls[1].cmdId == cmdId2)
        assert(self.meshController.networkPolls[1].cmdCounter == cmdCounter2)
        assert(self.meshController.networkPolls[1].exclusions == [])

    def test_executeNetworkAction(self):
        """Test executeNetworkAction method of MeshController."""
        sourceId = 1
        cmdCounter = 1000
        startTime = time.time()
        numNodes = self.nodeParams.config.maxNumNodes

        ## Test NetworkRestart poll actions
        restartTime = startTime + 100.0
        destId = 5
        
        # Restart not for this node
        assert(self.nodeParams.restartRequested == False)
        assert(self.nodeParams.restartTime == None)
        poll = NetworkPoll(sourceId, TDMACmds['NetworkRestart'], cmdCounter, {'destId': destId, 'restartTime': restartTime}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == False)
        assert(self.nodeParams.restartRequested == False)
        assert(self.nodeParams.restartTime == None)
        
        # Restart for entire network
        destId = 0
        poll = NetworkPoll(sourceId, TDMACmds['NetworkRestart'], cmdCounter, {'destId': destId, 'restartTime': restartTime}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == True)
        assert(self.nodeParams.restartRequested == True)
        assert(self.nodeParams.restartTime == restartTime)

        # Restart for this node only
        self.nodeParams.restartRequested = False
        self.nodeParams.restartTime = None
        destId = self.nodeParams.config.nodeId
        poll = NetworkPoll(sourceId, TDMACmds['NetworkRestart'], cmdCounter, {'destId': destId, 'restartTime': restartTime}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == True)
        assert(self.nodeParams.restartRequested == True)
        assert(self.nodeParams.restartTime == restartTime)

        ## Test ConfigUpdate poll actions
        destId = 5
        
        # Update not for this node
        assert(self.nodeParams.newConfig == None)
        poll = NetworkPoll(sourceId, TDMACmds['ConfigUpdate'], cmdCounter, {'destId': destId, 'config': 'config'}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == False)

        # Update for entire network
        destId = 0
        poll = NetworkPoll(sourceId, TDMACmds['ConfigUpdate'], cmdCounter, {'destId': destId, 'config': 'config'}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == True)
        assert(self.nodeParams.newConfig != None)

        # Update for this node only
        destId = self.nodeParams.config.nodeId
        self.nodeParams.newConfig = None
        poll = NetworkPoll(sourceId, TDMACmds['ConfigUpdate'], cmdCounter, {'destId': destId, 'config': 'config'}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == True)
        assert(self.nodeParams.newConfig != None)

        ## Test BlockTxRequest poll actions
        blockStartTime = time.time()
        sourceId = self.nodeParams.config.nodeId
        blockTxData = b'1234567890'*10
        self.meshController.blockTxData = blockTxData

        # Test poll rejection
        poll = NetworkPoll(sourceId, TDMACmds['BlockTxRequest'], cmdCounter, {'startTime': blockStartTime}, numNodes, None, startTime)
        poll.decision = VoteDecision.No
        assert(len(self.meshController.meshMsgs) == 0)
        assert(self.meshController.executeNetworkAction(poll) == False)
        assert(len(self.meshController.meshMsgs) == 1) # sender passes poll status to host
        assert(self.meshController.blockTxData == None) 
        
        # Test success as sender
        self.meshController.blockTxData = blockTxData
        assert(self.meshController.blockTxAccepted == False)
        assert(self.meshController.blockTx == None)
        
        self.meshController.meshMsgs = [] # clear messages
        poll = NetworkPoll(sourceId, TDMACmds['BlockTxRequest'], cmdCounter, {'startTime': blockStartTime}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == True)
        assert(len(self.meshController.meshMsgs) == 1) # sender passes poll status to host
        assert(self.meshController.blockTxAccepted == True)
        assert(self.meshController.blockTx != None)
        assert(self.meshController.blockTx['startTime'] == blockStartTime)
        assert(self.meshController.blockTx['blockData'] == blockTxData)
        assert(self.meshController.blockTx['sourceId'] == sourceId)

        # Test as receiver
        sourceId = 1
        self.meshController.blockTxData = blockTxData
        self.meshController.blockTxAccepted = False
        self.meshController.blockTx = None
        self.meshController.meshMsgs = [] # clear messages
        poll = NetworkPoll(sourceId, TDMACmds['BlockTxRequest'], cmdCounter, {'startTime': blockStartTime}, numNodes, None, startTime)
        poll.decision = VoteDecision.Yes
        assert(self.meshController.executeNetworkAction(poll) == True)
        assert(len(self.meshController.meshMsgs) == 0) # not source, so no response to host
        assert(self.meshController.blockTxAccepted == True)
        assert(self.meshController.blockTx != None)

    def test_checkPolling(self):
        """Test checkPolling method of MeshController."""

        # Test response sent on pending polls
        self.nodeParams.nodeStatus[0].updating = True # set at least one not updating to prevent poll from being removed
        self.nodeParams.nodeStatus[5].updating = True
        sourceId = self.nodeParams.config.nodeId
        startTime = time.time()
        cmdCounter = 1000
        numNodes = self.nodeParams.config.maxNumNodes
        poll = NetworkPoll(sourceId, TDMACmds['NetworkRestart'], cmdCounter, None, numNodes, [], startTime)
        self.meshController.networkPolls.append(poll)
        print(self.meshController.networkPolls)
        assert(self.meshController.networkPolls[0].voteSent == False)
        self.meshController.checkPolling()
        assert(self.meshController.networkPolls[0].voteSent == True)
        assert(NodeCmds['CmdResponse'] in self.tdmaComm.tdmaCmds)
        
        # Test rejection of block tx request when block tx already accepted
        poll = NetworkPoll(sourceId, TDMACmds['BlockTxRequest'], cmdCounter, None, numNodes, [], startTime)
        self.meshController.networkPolls[0] = poll
        self.meshController.blockTxAccepted = True
        self.tdmaComm.tdmaCmds = dict() # clear poll previous response
        self.meshController.checkPolling()
        assert(self.meshController.networkPolls[0].voteSent == True)
        assert(NodeCmds['CmdResponse'] in self.tdmaComm.tdmaCmds)
        assert(self.tdmaComm.tdmaCmds[NodeCmds['CmdResponse']].cmdData['cmdResponse'] == False)
        
        # Test processing of poll responses received
        responseNode = 1
        poll = NetworkPoll(sourceId, TDMACmds['BlockTxRequest'], cmdCounter, None, numNodes, [], startTime)
        self.meshController.networkPolls[0] = poll
        self.nodeParams.cmdResponse[cmdCounter] = dict() # create command response list for this command
        self.nodeParams.cmdResponse[cmdCounter][responseNode] = 1
        assert(self.meshController.networkPolls[0].votes[responseNode-1] == NetworkVote.NotReceived)
        self.meshController.checkPolling()
        assert(self.meshController.networkPolls[0].votes[responseNode-1] == NetworkVote.Yes)

        # Test execution of completed polls
        poll = NetworkPoll(sourceId, TDMACmds['NetworkRestart'], cmdCounter, {'destId': 0, 'restartTime': time.time()}, numNodes, [], startTime)
        self.meshController.networkPolls[0] = poll
        self.nodeParams.cmdResponse[cmdCounter] = dict() # create command response list for this command
        self.nodeParams.cmdResponse[cmdCounter][1] = 1 # provide positive response from updating nodes
        self.nodeParams.cmdResponse[cmdCounter][6] = 1
        assert(self.nodeParams.restartRequested == False)
        self.meshController.checkPolling()
        assert(self.nodeParams.restartRequested == True) # restart accepted and executed

        # Test expiration of polls
        poll = NetworkPoll(sourceId, TDMACmds['NetworkRestart'], cmdCounter, {'destId': 0, 'restartTime': time.time()}, numNodes, [], time.time() - self.nodeParams.config.commConfig['pollTimeout'])
        self.meshController.networkPolls.append(poll)
        self.nodeParams.cmdResponse = dict() # clear any command responses
        self.meshController.checkPolling()
        assert(len(self.meshController.networkPolls) == 0) # polls cleared

    def test_monitorNodeUpdates(self):
        """Test monitorNodeUpdates method of MeshController."""

        # Test that nodes with known paths are set as updating
        self.tdmaComm.meshPaths = [[1, 2], [2], [], [], [5, 1], []]
        self.meshController.monitorNodeUpdates()
        assert(self.nodeParams.nodeStatus[0].updating == True)
        assert(self.nodeParams.nodeStatus[1].updating == True)
        assert(self.nodeParams.nodeStatus[2].updating == False)
        assert(self.nodeParams.nodeStatus[3].updating == False)
        assert(self.nodeParams.nodeStatus[4].updating == True)
        assert(self.nodeParams.nodeStatus[5].updating == False)

    def test_monitorNetworkStatus(self):
        """Test monitorNetworkStatus method of MeshController."""

        # Test network init
        self.nodeParams.newConfig = self.nodeParams.config
        self.tdmaComm.networkConfigConfirmed = False
        self.tdmaComm.networkConfigRcvd = True
        self.meshController.monitorNetworkStatus()
        assert(self.nodeParams.newConfig == None) # new configuration cleared after updating 
        
        # Test network restart        
        self.nodeParams.restartRequested = True
        self.nodeParams.restartTime = time.time() - 1.0
        self.meshController.monitorNetworkStatus()
        assert(self.nodeParams.restartRequested == False) # restart status cleared after completed           
        # Test block transmit
        self.meshController.blockTxAccepted = True
        self.meshController.blockTx = {'blockReqId': 100, 'destId': 1, 'sourceId': 6, 'startTime': time.time() - 1.0, 'length': 2, 'blockData': b'1234567890'}
        self.meshController.monitorNetworkStatus()
        assert(self.meshController.blockTxAccepted == False) # status cleared after start of block tx
    
         
