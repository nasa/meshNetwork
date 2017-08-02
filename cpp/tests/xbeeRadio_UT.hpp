#ifndef __COMM_XBEE_RADIO_UT_HPP__
#define __COMM_XBEE_RADIO_UT_HPP__

#include <gtest/gtest.h>
#include "comm/xbeeRadio.hpp"

namespace comm
{
    class XbeeRadio_UT : public ::testing::Test
    {
      public:  
      
      protected:
        XbeeRadio_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        XbeeRadio m_xbeeRadio;

    };
}

#endif // __COMM_XBEE_RADIO_UT_HPP__
