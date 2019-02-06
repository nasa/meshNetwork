#include "tests/nodeConfig_UT.hpp"
#include <gtest/gtest.h>
#include <iostream>
#include <unistd.h>
#include <vector>
#include <string>

using std::vector;

namespace {
    vector<uint8_t> pixhawkTruthHash = {171, 39, 134, 6, 10, 6, 132, 68, 222, 18, 100, 103, 186, 133, 81, 34, 188, 217, 248, 202}; 
    vector<uint8_t> satFCTruthHash = {178, 113, 109, 91, 28, 157, 193, 113, 170, 101, 180, 243, 248, 134, 88, 77, 81, 141, 171, 227};    
    
    std::string badConfigFilePath = "nodeConfig_bad.json";
    std::string noNodeConfigFilePath = "nodeConfig_noNodeId.json";
}

namespace node
{
    NodeConfig_UT::NodeConfig_UT()
    {
        m_nodeConfig = NodeConfig("nodeConfig.json");
    }

    void NodeConfig_UT::SetUpTestCase(void) {
    }
    
    void NodeConfig_UT::SetUp(void)
    {
    }

    TEST_F(NodeConfig_UT, invalidFileLoad) {
        NodeConfig nodeConfig = NodeConfig("");
        EXPECT_TRUE(nodeConfig.loadSuccess == false);
    }

    TEST_F(NodeConfig_UT, standardConfigLoad) {
        // Check for successful configuration load
        EXPECT_TRUE(m_nodeConfig.loadSuccess == true);
    }
   
    TEST_F(NodeConfig_UT, tdmaConfigLoad) {
        EXPECT_TRUE(m_nodeConfig.commType == TDMA); // tdma config found
        EXPECT_TRUE(m_nodeConfig.commConfig.fpga == true); // fpga config found
        EXPECT_TRUE(m_nodeConfig.loadSuccess == true); // successful load of required parameters
    }
 
    TEST_F(NodeConfig_UT, missingConfigEntry) {
        NodeConfig nodeConfig = NodeConfig(badConfigFilePath);
        EXPECT_TRUE(nodeConfig.loadSuccess == false);

    }

    TEST_F(NodeConfig_UT, readNodeId) {
        NodeConfig nodeConfig = NodeConfig(noNodeConfigFilePath);
        EXPECT_TRUE(nodeConfig.nodeId == 1); // default to 1 when no nodeId provided
    }

    TEST_F(NodeConfig_UT, updateParameter) {
        // Test attempted update of invalid parameter
        std::vector<uint8_t> paramValue({1});
        EXPECT_FALSE(m_nodeConfig.updateParameter(500, paramValue));

        // Test successful update
        EXPECT_TRUE(m_nodeConfig.parseMsgMax != 500);
        uint16_t testValue = 500;
        paramValue.resize(2);
        std::memcpy(paramValue.data(), &testValue, 2);
        EXPECT_TRUE(m_nodeConfig.updateParameter(PARAMID_PARSE_MSG_MAX, paramValue));
        EXPECT_TRUE(m_nodeConfig.parseMsgMax == 500);

    }

    TEST_F(NodeConfig_UT, calculateHash) {
        // Verify that hash does not include unique parameters
        NodeConfig nodeConfig = NodeConfig(noNodeConfigFilePath); // default to node id of 1
        
        EXPECT_TRUE(nodeConfig.nodeId != m_nodeConfig.nodeId); // verify that node id differs

        EXPECT_TRUE(nodeConfig.calculateHash() == m_nodeConfig.calculateHash()); // hash should match
    }    

}
