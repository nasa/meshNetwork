#ifndef COMM_CRC_UT_HPP
#define COMM_CRC_UT_HPP

#include <gtest/gtest.h>

namespace comm
{
    class crc_UT : public ::testing::Test
    {
      public:  
      
      protected:
        crc_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // COMM_CRC_UT_HPP
