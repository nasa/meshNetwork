import time
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeController import NodeController
from mesh.generic.nodeState import NodeState
from mesh.generic.formationClock import FormationClock
from unittests.testConfig import configFilePath

class TestNodeController:
    
    def setup_method(self, method):
        nodeParams = NodeParams(configFile=configFilePath)
        self.nodeController = NodeController(nodeParams)
        pass        
    
    def test_monitorFormationStatus(self):
        """Test monitorFormationStatus method of NodeController."""
        # Create nodeStatus to test
        nodeStatus = [NodeState(node+1) for node in range(5)]
        clock = FormationClock()
        
        nodeStatus[4].lastStateUpdateTime = time.time()
        self.nodeController.nodeParams.nodeStatus = nodeStatus
        self.nodeController.clock = clock
        self.nodeController.monitorFormationStatus()
        # Check that updated node shows True while others show False
        for node in nodeStatus[:-1]:
            assert(node.updating == False)
        assert(self.nodeController.nodeParams.nodeStatus[4].updating == True)

