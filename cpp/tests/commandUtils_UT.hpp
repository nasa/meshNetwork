#ifndef __COMM_COMMAND_UTILS_UT_HPP__
#define __COMM_COMMAND_UTILS_UT_HPP__

#include <gtest/gtest.h>

namespace comm
{
    class CommandUtils_UT : public ::testing::Test
    {
      public:  
      
      protected:
        CommandUtils_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // __COMM_COMMAND_UTILS_UT_HPP__
