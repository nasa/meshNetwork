#include "tests/SLIPMsgParser_UT.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <vector>
#include "comm/crc.hpp"

using std::vector;

vector<uint8_t> msgIn = {0, 1, comm::SLIP_END, 2, comm::SLIP_ESC, 3, comm::SLIP_END_TDMA, 4, 5};

namespace comm
{

    SLIPMsgParser_UT::SLIPMsgParser_UT()
        : m_slipmsgparser()
    {
    }

    void SLIPMsgParser_UT::SetUpTestCase(void) {
 
    }
    
    void SLIPMsgParser_UT::SetUp(void)
    {
    }

    TEST_F(SLIPMsgParser_UT, encodeMsg) {
        // Test that CRC is appended
        crc_t crc = crc_create(msgIn);
        vector<uint8_t> encoded = m_slipmsgparser.encodeMsg(msgIn);
        m_slipmsgparser.slipMsg.decodeSLIPMsg(encoded, 0);
        EXPECT_TRUE(m_slipmsgparser.slipMsg.msg.size() == msgIn.size() + 2); // length matches
        EXPECT_TRUE(crc == bytesToCrc(m_slipmsgparser.slipMsg.msg, m_slipmsgparser.slipMsg.msg.size()-2)); // crc is correct

    }
    
    TEST_F(SLIPMsgParser_UT, parseSerialMsg) {
        // Test that valid message is parsed
        vector<uint8_t> encoded = m_slipmsgparser.encodeMsg(msgIn);
        m_slipmsgparser.parseSerialMsg(encoded, 0);
        EXPECT_TRUE(m_slipmsgparser.parsedMsgs.size() == 1);
        EXPECT_TRUE(m_slipmsgparser.parsedMsgs[0].size() == msgIn.size());
        for (unsigned int i = 0; i < m_slipmsgparser.parsedMsgs[0].size(); i++) {
            EXPECT_TRUE(m_slipmsgparser.parsedMsgs[0][i] == msgIn[i]);
        }
        
        // Check that new messages are appended
        m_slipmsgparser.parseSerialMsg(encoded, 0);
        EXPECT_TRUE(m_slipmsgparser.parsedMsgs.size() == 2);
        
        // Check that message with invalid CRC is not parsed
        encoded[encoded.size()-1] = encoded[encoded.size()-1] + 1;  
        m_slipmsgparser.parseSerialMsg(encoded, 0);
        EXPECT_TRUE(m_slipmsgparser.parsedMsgs.size() == 2);

    }


}
