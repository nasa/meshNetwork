#ifndef __COMM_NODE_CMDS_UT_HPP__
#define __COMM_NODE_CMDS_UT_HPP__

#include <gtest/gtest.h>

namespace comm
{
    class NodeCmds_UT : public ::testing::Test
    {
      public:  
      
      protected:
        NodeCmds_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // __COMM_NODE_CMDS_UT_HPP__
