#ifndef __COMM_MSG_PARSER_UT_HPP__
#define __COMM_MSG_PARSER_UT_HPP__

#include <gtest/gtest.h>
#include "comm/msgParser.hpp"

namespace comm
{
    class MsgParser_UT : public ::testing::Test
    {
      public:  
      
      protected:
        MsgParser_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        MsgParser m_msgParser;

    };
}

#endif // __COMM_MSG_PARSER_UT_HPP__
