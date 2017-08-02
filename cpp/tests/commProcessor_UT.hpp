#ifndef __COMM_COMM_PROCESSOR_UT_HPP__
#define __COMM_COMM_PROCESSOR_UT_HPP__

#include <gtest/gtest.h>
#include "comm/commProcessor.hpp"

namespace comm
{
    class CommProcessor_UT : public ::testing::Test
    {
      public:  
      
      protected:
        CommProcessor_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        CommProcessor m_commProcessor;

    };
}

#endif // __COMM_COMM_PROCESSOR_UT_HPP__
