#ifndef __COMM_RADIO_UT_HPP__
#define __COMM_RADIO_UT_HPP__

#include <gtest/gtest.h>
#include "comm/radio.hpp"

namespace comm
{
    class Radio_UT : public ::testing::Test
    {
      public:  
      
      protected:
        Radio_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        Radio m_radio;

    };
}

#endif // __COMM_RADIO_UT_HPP__
