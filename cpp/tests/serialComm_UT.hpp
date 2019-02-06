#ifndef __COMM_SERIAL_COMM_UT_HPP__
#define __COMM_SERIAL_COMM_UT_HPP__

#include <gtest/gtest.h>
#include "comm/serialComm.hpp"
#include "comm/msgProcessor.hpp"
#include "comm/nodeMsgProcessor.hpp"
#include <vector>

namespace comm
{
    class SerialComm_UT : public ::testing::Test
    {
      public:  
      
      protected:
        SerialComm_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* 
         * Message processor container.
         */
        std::vector<comm::MsgProcessor *> m_msgProcessors;
    
        /*
         * Message processor for test usage
         */
        NodeMsgProcessor m_nodeProcessor;    
        
        /* 
         * The class under test.
         */
        SerialComm m_serialComm;
        

    };
}

#endif // __COMM_SERIAL_COMM_UT_HPP__
