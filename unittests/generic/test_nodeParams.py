from mesh.generic.nodeConfig import NodeConfig
from mesh.generic.nodeParams import NodeParams
from mesh.generic.customExceptions import InvalidCmdCounter
import pytest, time
from unittests.testConfig import configFilePath

class TestNodeParams:
    

    def setup_method(self, method):
        
        # Create NodeConfig instance
        self.nodeConfig = NodeConfig(configFilePath)

        if method.__name__ != "test_init":
            self.nodeParams = NodeParams(config=self.nodeConfig) # Create NodeParams instance
            

    def test_init(self):
        """Test NodeParams init function."""

        # Test that init function loads node configuration from file
        print("Testing init with configFile")
        nodeParams = NodeParams(configFile=configFilePath)
        assert(nodeParams.config.__dict__ == self.nodeConfig.__dict__)

        # Test that init function loads node configuration from provided config
        nodeParams = NodeParams(config=self.nodeConfig)
        assert(nodeParams.config.__dict__ == self.nodeConfig.__dict__)
    
    def test_getCmdCounter(self):
        """Test NodeParams command counter get function."""

        # Test getting random command counter
        counter = self.nodeParams.get_cmdCounter()
        assert(counter >= 1) # value within range
        assert(counter <= 65536) # value within range
        
        # Test getting time-based command counter (NOTE: time-based counter commented out)
        #self.nodeParams.commStartTime = time.time()
        #time.sleep(0.5)
        #counter = self.nodeParams.get_cmdCounter()
        #assert(counter >= 0.5 * 1000)
        #assert(counter <= 0.6 * 1000)
