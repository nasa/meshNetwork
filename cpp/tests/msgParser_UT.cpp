#include "tests/msgParser_UT.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>

namespace comm
{

    MsgParser_UT::MsgParser_UT()
        : m_msgParser(10)
    {
    }

    void MsgParser_UT::SetUpTestCase(void) {
 
    }
    
    void MsgParser_UT::SetUp(void)
    {
    }

    TEST_F(MsgParser_UT, encodeMsg) {
        const unsigned int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        
        std::vector<uint8_t> out = m_msgParser.encodeMsg(dataIn);
        EXPECT_TRUE(out.size() == msgLength);
        for (unsigned int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == out[i]);
        }
        
    }

    TEST_F(MsgParser_UT, parseSerialMsg) {
        const unsigned int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
      
        // Parse entire message 
        m_msgParser.parseSerialMsg(dataIn, 0);
        EXPECT_TRUE(m_msgParser.parsedMsgs.size() == 1);
        EXPECT_TRUE(m_msgParser.parsedMsgs[0].size() == msgLength); 
        for (unsigned int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_msgParser.parsedMsgs[0][i]);
        }
 
        // Parse partial message
        m_msgParser.parseSerialMsg(dataIn, 1);
        EXPECT_TRUE(m_msgParser.parsedMsgs.size() == 2);
        EXPECT_TRUE(m_msgParser.parsedMsgs[1].size() == msgLength-1); 
        for (unsigned int i = 0; i < msgLength-1; i++) {
            EXPECT_TRUE(data[i+1] == m_msgParser.parsedMsgs[1][i]);
        }
    }

    TEST_F(MsgParser_UT, parseMsgs) {
        const unsigned int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        
        m_msgParser.parseMsgs(dataIn);
        EXPECT_TRUE(m_msgParser.parsedMsgs.size() == 1);
        EXPECT_TRUE(m_msgParser.parsedMsgs[0].size() == msgLength); 
        for (unsigned int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_msgParser.parsedMsgs[0][i]);
        }
    }

}
