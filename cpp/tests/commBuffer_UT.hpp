#ifndef __COMM_COMM_BUFFER_UT_HPP__
#define __COMM_COMM_BUFFER_UT_HPP__

#include <gtest/gtest.h>
#include "comm/commBuffer.hpp"
#include <vector>

namespace comm
{
    class CommBuffer_UT : public ::testing::Test
    {
      public:  
      
      protected:
        CommBuffer_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        CommBuffer< std::vector<uint8_t> > m_commBuffer;

    };
}

#endif // __COMM_COMM_BUFFER_UT_HPP__
