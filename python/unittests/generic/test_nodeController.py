import time
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeController import NodeController
from mesh.generic.nodeState import NodeState, LinkStatus
from mesh.generic.formationClock import FormationClock
from mesh.generic.serialComm import SerialComm
from mesh.generic.radio import Radio
from mesh.generic.cmds import NodeCmds
from unittests.testConfig import configFilePath

class TestNodeController:
    
    def setup_method(self, method):
        nodeParams = NodeParams(configFile=configFilePath)
        self.nodeController = NodeController(nodeParams)

    def setup_monitorNodeUpdates(self):    
        # Create nodeStatus to test
        self.nodeStatus = [NodeState(node+1) for node in range(self.nodeController.nodeParams.config.maxNumNodes)]
        clock = FormationClock()
        
        self.nodeStatus[1].lastStateUpdateTime = time.time()
        self.nodeController.nodeParams.nodeStatus = self.nodeStatus
        self.nodeController.clock = clock
        self.nodeController.monitorNodeUpdates()

    def setup_checkNodeLinks(self):
        # Setup indirect link
        self.nodeController.nodeParams.nodeStatus[0].updating = True
        
        # Setup direct link
        self.nodeController.nodeParams.nodeStatus[2].present = True
        self.nodeController.nodeParams.nodeStatus[2].lastMsgRcvdTime = time.time() - self.nodeController.nodeParams.config.commConfig['frameLength']

        # Setup bad link
        self.nodeController.nodeParams.linkStatus[1][3] = LinkStatus.GoodLink 

    def checkNodeUpdates(self):   
        for node in range(2,self.nodeController.nodeParams.config.maxNumNodes):
            assert(self.nodeController.nodeParams.nodeStatus[node].updating == False)
        assert(self.nodeController.nodeParams.nodeStatus[1].updating == True)
 
    def checkNodeLinks(self):
        self.nodeController.checkNodeLinks()
        nodeId = self.nodeController.nodeParams.config.nodeId - 1
        
        # Test link to self
        assert(self.nodeController.nodeParams.linkStatus[nodeId][nodeId] == LinkStatus.GoodLink)        

        # Test direct link
        assert(self.nodeController.nodeParams.linkStatus[nodeId][2] == LinkStatus.GoodLink)        

        # Test indirect link
        assert(self.nodeController.nodeParams.linkStatus[nodeId][0] == LinkStatus.IndirectLink)        

        # Test bad link
        assert(self.nodeController.nodeParams.linkStatus[nodeId][3] == LinkStatus.BadLink)        
        
        # Test bad link
        assert(self.nodeController.nodeParams.linkStatus[nodeId][4] == LinkStatus.NoLink)        

    def test_checkNodeLinks(self):
        self.setup_checkNodeLinks()

        # Test different link status possibilities
        self.checkNodeLinks() 

    def test_monitorNodeUpdates(self):
        self.setup_monitorNodeUpdates()

        # Check that updated node shows True while others show False
        self.checkNodeUpdates()
    
    def test_monitorNetworkStatus(self):
        """Test monitorNetworkStatus method of NodeController."""
        self.setup_monitorNodeUpdates()
        self.setup_checkNodeLinks()
 
        self.checkNodeUpdates()
        self.checkNodeLinks()

    def test_updateStatus(self):
        """Test updateStatus method of NodeController."""
        
        # Test without confirmed config
        self.nodeController.updateStatus()
        assert(self.nodeController.nodeParams.nodeStatus[self.nodeController.nodeParams.config.nodeId-1].status == 0)

        # Test with confirmed config
        self.nodeController.nodeParams.configConfirmed = True
        self.nodeController.updateStatus()
        assert(self.nodeController.nodeParams.nodeStatus[self.nodeController.nodeParams.config.nodeId-1].status == 64)

    def test_processNodeCommands(self):
        """Test processNodeCommands method of NodeController."""
        # Test processing of ConfigRequest command
        configHash = self.nodeController.nodeParams.config.calculateHash()
        radio = Radio([], {'uartNumBytesToRead': 100, 'rxBufferSize': 100})
        comm = SerialComm([], self.nodeController.nodeParams, radio, [])
        comm.cmdQueue[NodeCmds['ConfigRequest']] = configHash

        assert(self.nodeController.nodeParams.configConfirmed == False)
        self.nodeController.processNodeCommands(comm)
        assert(self.nodeController.nodeParams.configConfirmed == True)
