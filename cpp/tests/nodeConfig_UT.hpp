#ifndef __COMM_NODE_CONFIG_UT_HPP__
#define __COMM_NODE_CONFIG_UT_HPP__

#include <gtest/gtest.h>
#include "node/nodeConfig.hpp"

namespace node
{
    class NodeConfig_UT : public ::testing::Test
    {
      public:  
      
      protected:
        NodeConfig_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        // The class under test.
        node::NodeConfig m_nodeConfig;

    };
}

#endif // __COMM_NODE_CONFIG_UT_HPP__
