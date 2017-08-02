#ifndef __COMM_SERIAL_RADIO_UT_HPP__
#define __COMM_SERIAL_RADIO_UT_HPP__

#include <gtest/gtest.h>
#include "comm/serialRadio.hpp"

namespace comm
{
    class SerialRadio_UT : public ::testing::Test
    {
      public:  
      
      protected:
        SerialRadio_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        SerialRadio m_radio;

    };
}

#endif // __COMM_SERIAL_RADIO_UT_HPP__
