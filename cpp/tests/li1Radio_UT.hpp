#ifndef __COMM_LI1_RADIO_UT_HPP__
#define __COMM_LI1_RADIO_UT_HPP__

#include <gtest/gtest.h>
#include "comm/li1Radio.hpp"

namespace comm
{
    class Li1Radio_UT : public ::testing::Test
    {
      public:  
      
      protected:
        Li1Radio_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        Li1Radio m_li1Radio;

    };
}

#endif // __COMM_LI1_RADIO_UT_HPP__
