#ifndef __COMM_SLIPMSGPARSER_UT_HPP__
#define __COMM_SLIPMSGPARSER_UT_HPP__

#include <gtest/gtest.h>
#include "comm/SLIPMsgParser.hpp"

namespace comm
{
    class SLIPMsgParser_UT : public ::testing::Test
    {
      public:  
      
      protected:
        SLIPMsgParser_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        SLIPMsgParser m_slipmsgparser;

    };
}

#endif // __COMM_SLIPMSGPARSER_UT_HPP__
