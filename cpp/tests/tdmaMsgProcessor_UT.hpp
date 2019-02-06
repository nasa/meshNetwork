#ifndef __COMM_TDMA_MSG_PROCESSOR_UT_HPP__
#define __COMM_TDMA_MSG_PROCESSOR_UT_HPP__

#include <gtest/gtest.h>
#include "comm/msgProcessor.hpp"
#include "comm/command.hpp"
#include "comm/tdmaMsgProcessor.hpp"
#include <unordered_map>

namespace comm
{
    class TDMAMsgProcessor_UT : public ::testing::Test
    {
      public:  
      
      protected:
        TDMAMsgProcessor_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /*
         * Message processing arguments.
         */
        MsgProcessorArgs m_args;

        /*
         * Command queue.
         */
        std::unordered_map<uint8_t, std::vector<uint8_t> > m_cmdQueue;
        
        /*
         * Command relay buffer.
         */
        std::vector<uint8_t> m_relayBuffer;
        
        /* 
         * The class under test.
         */
        TDMAMsgProcessor m_tdmaMsgProcessor;

    };
}

#endif // __COMM_TDMA_MSG_PROCESSOR_UT_HPP__
