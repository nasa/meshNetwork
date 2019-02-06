#ifndef __COMM_CMDHEADER_UT_HPP__
#define __COMM_CMDHEADER_UT_HPP__

#include <gtest/gtest.h>

namespace comm
{
    class CmdHeader_UT : public ::testing::Test
    {
      public:  
      
      protected:
        CmdHeader_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // __COMM_CMDHEADER_UT_HPP__
