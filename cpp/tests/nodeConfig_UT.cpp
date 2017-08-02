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

    TEST_F(NodeConfig_UT, readNodeId_gpio) {
        std::string temp;
	// This test requires user interaction to change switches
        std::cout << "Testing nodeId load from dip switches." << std::endl;
        std::cout << "Set all switches to zero and hit enter..." << std::endl;
        
//	usleep(5*1e6); // sleep 5 seconds to wait for user
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 0);
        std::cout << "Set switches to 1 and hit enter..." << std::endl;
      	std::getline(std::cin, temp); 
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 1);
        std::cout << "Set switches to 2 and hit enter..." << std::endl;
      	std::getline(std::cin, temp); 
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 2);
        std::cout << "Set switches to 3 and hit enter..." << std::endl;
      	std::getline(std::cin, temp); 
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 3);
        std::cout << "Set switches to 4 and hit enter..." << std::endl;
      	std::getline(std::cin, temp); 
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 4);
        std::cout << "Set switches to 5 and hit enter..." << std::endl;
      	std::getline(std::cin, temp); 
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 5);
        std::cout << "Set switches to 6 and hit enter..." << std::endl;
      	std::getline(std::cin, temp); 
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 6);
        std::cout << "Set switches to 7 and hit enter..." << std::endl;
      	std::getline(std::cin, temp); 
        m_nodeConfig.readNodeId();
        EXPECT_TRUE(m_nodeConfig.nodeId == 7);
    }

    TEST_F(NodeConfig_UT, calculateHash) {
		// Check Pixhawk hash
        m_nodeConfig = NodeConfig("nodeConfig.json");
        std::string hash = m_nodeConfig.calculateHash();
		ASSERT_TRUE(hash.size() == pixhawkTruthHash.size());
		for (unsigned int i = 0; i < hash.size(); i++) {
		    EXPECT_TRUE((uint8_t)hash[i] == pixhawkTruthHash[i]);
        }    

		// Check SatFC hash
        m_nodeConfig = NodeConfig("nodeConfig-sat.json");
        hash = m_nodeConfig.calculateHash();
		ASSERT_TRUE(hash.size() == satFCTruthHash.size());
		for (unsigned int i = 0; i < hash.size(); i++) {
		    EXPECT_TRUE((uint8_t)hash[i] == satFCTruthHash[i]);
        }    
    }    

}
