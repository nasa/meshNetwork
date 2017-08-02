#include "tests/SLIPMsg_UT.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>
#include <vector>

using std::vector;

namespace comm
{
    vector<uint8_t> msgIn = {0, 1, SLIP_END, 2, SLIP_ESC, 3, SLIP_END_TDMA, 4, 5};
    vector<uint8_t> msgOut = {SLIP_END, 0, 1, SLIP_ESC, SLIP_ESC_END, 2, SLIP_ESC, SLIP_ESC_ESC, 3, SLIP_ESC, SLIP_ESC_END_TDMA, 4, 5, SLIP_END}; 

    SLIPMsg_UT::SLIPMsg_UT()
        : m_slipmsg(100)
    {
    }

    void SLIPMsg_UT::SetUpTestCase(void) {
 
    }
    
    void SLIPMsg_UT::SetUp(void)
    {
    }

    TEST_F(SLIPMsg_UT, encodeSLIPMsg) {
        vector<uint8_t> encodedMsg = m_slipmsg.encodeSLIPMsg(msgIn);
        
        EXPECT_TRUE(encodedMsg.size() == msgOut.size());

        for (unsigned int i = 0; i < msgOut.size(); i++) {
            EXPECT_TRUE(encodedMsg[i] == msgOut[i]);
        }

    }

    TEST_F(SLIPMsg_UT, decodeSLIPMsgContents) {
        m_slipmsg.decodeSLIPMsgContents(msgOut, 1);
        
        EXPECT_TRUE(m_slipmsg.msg.size() == msgIn.size()); 
        for (unsigned int i = 0; i < msgIn.size(); i++) {
            EXPECT_TRUE(m_slipmsg.msg[i] == msgIn[i]);
        }
        
        EXPECT_TRUE(m_slipmsg.msgEnd == msgOut.size());
    }

    TEST_F(SLIPMsg_UT, decodeSLIPMsg) {
        m_slipmsg.decodeSLIPMsg(msgOut, 0);

        EXPECT_TRUE(m_slipmsg.msgFound == true);
        EXPECT_TRUE(m_slipmsg.msgEnd == msgOut.size());
    
        // Parse message in parts
        vector<uint8_t> partial(msgOut.begin(), msgOut.begin()+5);
        m_slipmsg.decodeSLIPMsg(partial, 0);

        EXPECT_TRUE(m_slipmsg.msgFound == true);
        EXPECT_TRUE(m_slipmsg.msgEnd == 0);
 
        partial = vector<uint8_t>(msgOut.begin()+5, msgOut.end());
        m_slipmsg.decodeSLIPMsg(partial, 0);

        EXPECT_TRUE(m_slipmsg.msgFound == true);
        EXPECT_TRUE(m_slipmsg.msgEnd == partial.size());

    }
}
