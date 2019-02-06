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

        EXPECT_TRUE(NodeParams::nodeParamsLoaded);
    }

    TEST_F(NodeParams_UT, getCmdCounter) {
        unsigned int counterValue;
        // Test random counter
        for (unsigned int i = 0; i < 20; i++) {
            counterValue = NodeParams::getCmdCounter();
            EXPECT_TRUE(counterValue >= 0 && counterValue <=65536);
        }
        
    }

}
