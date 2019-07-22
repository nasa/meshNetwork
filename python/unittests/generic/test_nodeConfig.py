from mesh.generic.nodeConfig import NodeConfig, ParamId
import json, math
from switch import switch
import socket
from unittests.testConfig import configFilePath, badConfigFilePath, noNodeConfigFilePath
import mesh.generic.customExceptions as customExceptions
import pytest 

# Load truth data
testConfigFilePath = 'nodeConfig.json'
standardParams = ["nodeId", "gcsPresent", "gcsNodeId", "maxNumNodes", "nodeUpdateTimeout", "uartNumBytesToRead", "parseMsgMax", "rxBufferSize", "FCCommWriteInterval", "meshBaudrate", "FCBaudrate", "numMeshNetworks", "meshDevices", "FCCommDevice", "radios", "msgParsers", "gcsPresent", "cmdInterval", "logInterval", "commType", "interface", "commConfig", "platform"]
tdmaParams = ["rxLength", "preTxGuardLength", "txLength", "postTxGuardLength", "frameLength", "desiredDataRate", "cycleLength", "slotLength", "fpga", "maxTransferSize", "maxNumSlots", "maxBlockTransferSize", "rxDelay", "transmitSlot"]

class TestNodeConfig:
    

    def setup_method(self, method):
        
        # Populate truth data
        #self.configTruthData = json.load(open(configFilePath))

        ### Update truth data to match expected node configuration output
        #self.configTruthData.update({'nodeId': 0})
            
        # TDMA comm test
        #if method.__name__ == 'test_TDMACommConfigLoad': 
        #    self.configTruthData['commType'] = 'TDMA'

        # Create node config json input file
        #with open(testConfigFilePath, 'w') as outfile:
        #    json.dump(self.configTruthData, outfile)

        # Create NodeConfig instance
        self.nodeConfig = NodeConfig(configFilePath)
   
    def test_noFileLoad(self):
        """Test for failed load of configuration due to no file provided."""
        nodeConfig = NodeConfig("")
        assert(nodeConfig.nodeId == -1)
        assert(nodeConfig.loadSuccess == False)
 
    def test_invalidFileLoad(self):
        """Test for failed load due to bad configuration file."""
        with pytest.raises(customExceptions.NodeConfigFileError) as e:
            nodeConfig = NodeConfig("invalidFile")
 
    def test_standardConfigLoad(self):
        """Test that standard generic configuration loaded properly."""
        print("Testing generic configuration loading")

        # Test that standard parameters are present
        self.checkConfigEntries(standardParams, True)

    def test_tdmaConfigLoad(self):
        """Test that TDMA comm configuration loaded properly."""
        print("Testing TDMA comm configuration loading.")
        
        if (self.nodeConfig.commType == "TDMA"):
            commEntries = ["preTxGuardLength", "postTxGuardLength", "txLength", "rxLength", "slotLength", "cycleLength", "frameLength", "transmitSlot", "desiredDataRate", "maxNumSlots", "offsetTimeout", "offsetTxInterval", "statusTxInterval", "linksTxInterval", "maxTxBlockSize", "blockTxRequestTimeout", "minBlockTxDelay", "fpga", "initSyncBound", "initTimeToWait", "operateSyncBound"]
        
            # Check for TDMA config
            assert(type(self.nodeConfig.commConfig == dict))
            self.checkConfigEntries(commEntries, True, list(self.nodeConfig.commConfig.keys()))

            # Check FPGA config specific parameters
            if (self.nodeConfig.commConfig['fpga'] == True):
                fpgaParams = ["fpgaFailsafePin", "fpgaFifoSize"] 
                self.checkConfigEntries(commEntries, True, list(self.nodeConfig.commConfig.keys()))

    def test_missingConfigEntry(self):
        """Test for missing configuration entry in configuration file."""
        with pytest.raises(KeyError) as e:
            nodeConfig = NodeConfig(badConfigFilePath)
        pass  

    def test_readNodeId(self):
        """Test proper call of readNodeId method of NodeConfig."""
        nodeConfig = NodeConfig(noNodeConfigFilePath)
        assert(nodeConfig.nodeId == 1) # defaults to node 1 when no nodeId provided

    def test_updateParameter(self):
        """Test updateParameter method of NodeConfig."""
        # Test attempted update of invalid parameter
        assert(self.nodeConfig.updateParameter("BadParam", 1) == False)

        # Test successful update
        assert(self.nodeConfig.parseMsgMax != 500)
        assert(self.nodeConfig.updateParameter(ParamId.parseMsgMax, 500))
        assert(self.nodeConfig.parseMsgMax == 500)

    def test_calculateHash(self):
        """Test calculateHash method of NodeConfig."""
        # Verify that hash value does not change when unique parameters are different
        nodeConfig = NodeConfig(noNodeConfigFilePath)

        assert(nodeConfig.calculateHash() == self.nodeConfig.calculateHash())

    def test_hashElem(self):
        """Test hashElem function to ensure proper handling of all data types."""
        
        import hashlib 

        ### Test hashing of floats
        testFloat1 = 51.1234567
        testFloat2 = 51.12345674
        testFloat3 = 51.12345676
        testInt1 = 51
        testHash1 = hashlib.sha1()
        testHash2 = hashlib.sha1()

        # Test proper truncation of floats
        self.nodeConfig.hashElem(testHash1, testFloat1)
        self.nodeConfig.hashElem(testHash2, testFloat2) 
        hash1Value = testHash1.digest()
        hash2Value = testHash2.digest()
        assert(hash1Value == hash2Value) # Test float round down
        
        testHash2 = hashlib.sha1()
        self.nodeConfig.hashElem(testHash2, testFloat3) 
        hash2Value = testHash2.digest()
        assert(hash1Value != hash2Value) # Test float round up

        # Test hashing of ints vs floats    
        testHash2 = hashlib.sha1()
        self.nodeConfig.hashElem(testHash2, testInt1)   
        hash2Value = testHash2.digest()
        assert(hash1Value != hash2Value) # Test float not truncated

    def test_protobufConversion(self):
        """Tests conversion between json and protobuf configuration representations."""

        # Convert json data to protobuf format
        with open (configFilePath, "r") as jsonFile:
            configData = json.load(jsonFile)
        #protobuf = self.nodeConfig.toProtoBuf(configData)
        protobuf = NodeConfig.toProtoBuf(configData)

        # Convert back to json representation
        #fromProtobuf = self.nodeConfig.fromProtoBuf(protobuf.SerializeToString())
        fromProtobuf = NodeConfig.fromProtoBuf(protobuf.SerializeToString())
        
        # Hash config instance from conversion and compare to initial configuration
        nc_protobuf = NodeConfig(configData=fromProtobuf)

        assert(self.nodeConfig.calculateHash() == nc_protobuf.calculateHash())

    def checkConfigEntries(self, testEntries, testCondition, configEntries=None):
        if configEntries == None:
            configEntries = list(self.nodeConfig.__dict__.keys())
        for key in testEntries:
            # Check if key in configuration
            print("Testing " + str(key) + " in " + str(configEntries))
            assert ((key in configEntries) == testCondition)
            ## Check for any subkeys
            #if list(testEntries[i]): # Check if entry is a list of entries
            #   for subkey in testEntries[i]:
            #       print(eval('self.nodeConfig.' + entries[i]), truthEntries[i])
            #       assert (subkey in eval('self.nodeConfig.' + key) == testCondition)
    
            
    def updateTestNodeConfigData(self, platform):
        """Update appropriate config data prior to testing."""
        configTruthData['platform'] = platform

