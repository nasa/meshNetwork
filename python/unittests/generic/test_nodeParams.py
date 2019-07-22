from mesh.generic.nodeConfig import NodeConfig
from mesh.generic.nodeParams import NodeParams
from mesh.generic.nodeState import LinkStatus
import pytest, time, hashlib, json
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
    
    def test_checkNodeLinks(self):
        nodeId = self.nodeParams.config.nodeId - 1

        # Test for direct link 
        self.nodeParams.nodeStatus[2].present = True
        self.nodeParams.nodeStatus[2].lastMsgRcvdTime = time.time() - 0.90 * self.nodeParams.config.commConfig['linkTimeout']
        self.nodeParams.checkNodeLinks()
        assert(self.nodeParams.linkStatus[nodeId][2] == LinkStatus.GoodLink)

        # Test for indirect link
        self.nodeParams.nodeStatus[2].present = False
        self.nodeParams.nodeStatus[2].updating = True
        self.nodeParams.checkNodeLinks()
        assert(self.nodeParams.linkStatus[nodeId][2] == LinkStatus.IndirectLink)

        # Test for no link
        self.nodeParams.nodeStatus[2].present = False
        self.nodeParams.nodeStatus[2].updating = False
        self.nodeParams.checkNodeLinks()
        assert(self.nodeParams.linkStatus[nodeId][2] == LinkStatus.NoLink)
        
    def test_updateStatus(self):
        """Test updateStatus method of NodeParams."""
        
        # Test without confirmed config
        self.nodeParams.updateStatus()
        assert(self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1].status == 0)

        # Test with confirmed config
        self.nodeParams.configConfirmed = True
        self.nodeParams.updateStatus()
        assert(self.nodeParams.nodeStatus[self.nodeParams.config.nodeId-1].status == 64)

    def test_loadConfig(self):
        """Test loadConfig method of NodeParams."""
        
        # Create new config for update
        newConfig = NodeConfig(configFilePath)
        newConfigHash = newConfig.calculateHash()
        with open (configFilePath, "r") as jsonFile:
            configData = json.load(jsonFile)
        newConfig_pb = NodeConfig.toProtoBuf(configData).SerializeToString()

        # Test update method
        badHash = hashlib.sha1()
        assert(self.nodeParams.loadConfig(newConfig_pb, badHash) == False) # test rejection with bad hash
        assert(self.nodeParams.newConfig == None)
        assert(self.nodeParams.loadConfig(newConfig_pb, newConfigHash) == True) # test acceptance
        assert(self.nodeParams.newConfig != None)

    def test_updateConfig(self):
        """Test updateConfig method of NodeParams."""
        
        # Load valid new config
        newConfig = NodeConfig(configFilePath)
        newConfigHash = newConfig.calculateHash()
        with open (configFilePath, "r") as jsonFile:
            configData = json.load(jsonFile)
        newConfig_pb = NodeConfig.toProtoBuf(configData).SerializeToString()
        self.nodeParams.loadConfig(newConfig_pb, newConfigHash)
       
        # Test successful loading
        self.nodeParams.config.FCBaudrate = newConfig.FCBaudrate / 2.0 # change a parameter to verify loading of new config
        assert(self.nodeParams.config.FCBaudrate != newConfig.FCBaudrate)
        assert(self.nodeParams.updateConfig() == True)
        assert(self.nodeParams.config.FCBaudrate == newConfig.FCBaudrate)
        assert(self.nodeParams.newConfig == None)

        # Expect no load when config missing
        assert(self.nodeParams.updateConfig() == False) 
