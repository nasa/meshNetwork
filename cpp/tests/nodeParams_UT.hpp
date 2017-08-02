#ifndef __COMM_NODE_PARAMS_UT_HPP__
#define __COMM_NODE_PARAMS_UT_HPP__

#include <gtest/gtest.h>
#include "node/nodeParams.hpp"

namespace node
{
    class NodeParams_UT : public ::testing::Test
    {
      public:  
      
      protected:
        NodeParams_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // __COMM_NODE_PARAMS_UT_HPP__
