#ifndef __COMM_TDMA_COMM_UT_HPP__
#define __COMM_TDMA_COMM_UT_HPP__

#include <gtest/gtest.h>
#include "comm/tdmaComm.hpp"
#include "comm/tdmaMsgProcessor.hpp"
#include "comm/serialRadio.hpp"
#include "comm/commProcessor.hpp"
#include "comm/SLIPMsgParser.hpp"
#include <vector>

namespace comm
{
    class TDMAComm_UT : public ::testing::Test
    {
      public:  
         
        comm::TDMAMsgProcessor tdmaProcessor;    
        std::vector<comm::MsgProcessor *> msgProcessors;
        serial::Serial serOut;
        serial::Serial serIn;
        comm::RadioConfig config;
        comm::SerialRadio radio;
        comm::CommProcessor commProcessor;
        comm::SLIPMsgParser msgParser;
      
      protected:
        TDMAComm_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        TDMAComm m_tdmaComm;

    };
}

#endif // __COMM_TDMA_COMM_UT_HPP__
