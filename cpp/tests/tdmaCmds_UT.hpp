#ifndef __COMM_TDMA_CMDS_UT_HPP__
#define __COMM_TDMA_CMDS_UT_HPP__

#include <gtest/gtest.h>

namespace comm
{
    class TDMACmds_UT : public ::testing::Test
    {
      public:  
      
      protected:
        TDMACmds_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // __COMM_TDMA_CMDS_UT_HPP__
