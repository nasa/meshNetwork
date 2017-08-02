#ifndef COMM_CHECKSUM_UT_HPP
#define COMM_CHECKSUM_UT_HPP

#include <gtest/gtest.h>

namespace comm
{
    class checksum_UT : public ::testing::Test
    {
      public:  
      
      protected:
        checksum_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // COMM_CHECKSUM_UT_HPP
