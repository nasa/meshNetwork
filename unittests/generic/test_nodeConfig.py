from mesh.generic.nodeConfig import NodeConfig
from mesh.generic.nodeTools import isBeaglebone
import json, math
from switch import switch
import socket
import netifaces
from unittests.testConfig import configFilePath

# Load truth data
testConfigFilePath = 'nodeConfig.json'
standardParams = ["platform", "nodeId", "maxNumNodes", "nodeUpdateTimeout", "commType", "uartNumBytesToRead", "parseMsgMax", "rxBufferSize", "FCCommWriteInterval", "meshBaudrate", "FCBaudrate", "numMeshNetworks", "meshDevices", "FCCommDevice", "radios", "msgParsers", "gcsPresent", "cmdInterval", "logInterval", "enablePin", "statusPin", "interface"]
tdmaParams = ["rxLength", "preTxGuardLength", "txLength", "postTxGuardLength", "frameLength", "desiredDataRate", "cycleLength", "slotLength", "fpga", "maxTransferSize", "maxNumSlots", "maxBlockTransferSize", "rxDelay", "transmitSlot"]

class TestNodeConfig:
    

    def setup_method(self, method):
        
        # Populate truth data
        self.configTruthData = json.load(open(configFilePath))

        ### Update truth data to match expected node configuration output
        self.configTruthData.update({'nodeId': 0})
            
        # TDMA comm test
        if method.__name__ == 'test_TDMACommConfigLoad': 
            self.configTruthData['commType'] = 'TDMA'

        # Create node config json input file
        with open(testConfigFilePath, 'w') as outfile:
            json.dump(self.configTruthData, outfile)

        # Create NodeConfig instance
        self.nodeConfig = NodeConfig(testConfigFilePath)
    
    def test_standardConfigLoad(self):
        """Test that standard generic configuration loaded properly."""
        print("Testing generic configuration loading")

        # Test that standar parameters are present
        self.checkConfigEntries(standardParams, True)

    def test_tdmaConfigLoad(self):
        """Test that TDMA comm configuration loaded properly."""
        print("Testing TDMA comm configuration loading.")
        
        if (self.nodeConfig.commType == "TDMA"):
            commEntries = ["preTxGuardLength", "postTxGuardLength", "txLength", "rxLength", "slotLength", "cycleLength", "frameLength", "transmitSlot", "desiredDataRate", "maxNumSlots", "offsetTimeout", "initSyncBound", "operateSyncBound"]
        
            # Check for TDMA config
            assert(type(self.nodeConfig.commConfig == dict))
            self.checkConfigEntries(commEntries, True, list(self.nodeConfig.commConfig.keys()))

    def test_readNodeId(self):
        if isBeaglebone(): # only run test if running on node
            assert(socket.gethostname() == 'node' + str(self.nodeConfig.nodeId)) # confirm hostname
            assert(netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr'] == '192.168.0.' + str(self.nodeConfig.nodeId) + '0')

    def test_calculateHash(self):
        pass

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

        print(('%.*f' % (7, testFloat2)).encode('utf-8'))
        print(('%.*f' % (7, testFloat3)).encode('utf-8'))
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

    def checkConfigEntries(self, testEntries, testCondition, configEntries=None):
        if configEntries == None:
            configEntries = list(self.nodeConfig.__dict__.keys())
        print("Test Entries:", testEntries)
        print("Config Entries:", configEntries)
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

