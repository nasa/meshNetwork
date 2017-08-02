#include "tests/nodeParams_UT.hpp"
#include <gtest/gtest.h>
#include "node/nodeConfig.hpp"
#include "comm/utilities.hpp"
#include "comm/formationClock.hpp"

using std::vector;

namespace {
    
}

namespace node
{
    NodeParams_UT::NodeParams_UT()
    {
    }

    void NodeParams_UT::SetUpTestCase(void) {
        // Load node params
        NodeConfig config("nodeConfig.json");
        NodeParams::loadParams(config);
    }
    
    void NodeParams_UT::SetUp(void)
    {
    }

    TEST_F(NodeParams_UT, loadParams) {
        // Confirm successful loading of parameters
        EXPECT_TRUE(NodeParams::nodeStatus.size() == NodeParams::config.maxNumNodes);
    }

    TEST_F(NodeParams_UT, getCmdCounter) {
        unsigned int counterValue;
        // Test random counter
        NodeParams::commStartTime = -1.0;
        
        for (unsigned int i = 0; i < 20; i++) {
            counterValue = NodeParams::getCmdCounter();
            EXPECT_TRUE(counterValue >= 0 && counterValue <=65536);
        }

        // Test time based counter
        NodeParams::commStartTime = util::getTime();
        usleep(500*1e3);
        counterValue = NodeParams::getCmdCounter();
        EXPECT_TRUE(counterValue >= 500 && counterValue <= 550);
        
    }

    TEST_F(NodeParams_UT, checkTimeOffset) {
        double offset = comm::FormationClock::invalidOffset;
        NodeParams::config.nodeId = 1;
        NodeParams::config.commConfig.operateSyncBound = 0.1;

        // Check for return when not TDMA
        NodeParams::config.commType = STANDARD;
        EXPECT_TRUE(NodeParams::checkTimeOffset(offset) == -1);
    
        // Check when offset provided
        NodeParams::config.commType = TDMA;
        offset = 0.05;
        EXPECT_TRUE(NodeParams::checkTimeOffset(offset) == 0); // offset within bounds
        EXPECT_TRUE(NodeParams::nodeStatus[NodeParams::config.nodeId-1].timeOffset == offset); // offset stored
        offset = NodeParams::config.commConfig.operateSyncBound + 0.1;
        EXPECT_TRUE(NodeParams::checkTimeOffset(offset) == 1); // offset outside bounds
        offset = -0.05;
        EXPECT_TRUE(NodeParams::checkTimeOffset(offset) == 0); // test with negative value

        //
    }

    TEST_F(NodeParams_UT, checkOffsetFailsafe) {
        // Test with offset failsafe behavior
        NodeParams::config.nodeId = 1;
        NodeParams::config.commConfig.operateSyncBound = 0.1;
        ASSERT_TRUE(NodeParams::tdmaFailsafe == false);
        ASSERT_TRUE(NodeParams::timeOffsetTimer == -1.0);

        EXPECT_TRUE(NodeParams::checkOffsetFailsafe() == 0);    
        EXPECT_TRUE(NodeParams::tdmaFailsafe == false);
        EXPECT_TRUE(NodeParams::timeOffsetTimer >= 0.9*util::getTime()); // timer started

        // Check for offset timeout
        NodeParams::timeOffsetTimer -= NodeParams::config.commConfig.offsetTimeout;
        EXPECT_TRUE(NodeParams::checkOffsetFailsafe() == 2);    
        EXPECT_TRUE(NodeParams::tdmaFailsafe == true);

    }
        
}
