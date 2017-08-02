#ifndef __COMM_SLIPMSG_UT_HPP__
#define __COMM_SLIPMSG_UT_HPP__

#include <gtest/gtest.h>
#include "comm/SLIPMsg.hpp"

namespace comm
{
    class SLIPMsg_UT : public ::testing::Test
    {
      public:  
      
      protected:
        SLIPMsg_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        SLIPMsg m_slipmsg;

    };
}

#endif // __COMM_SLIPMSG_UT_HPP__
