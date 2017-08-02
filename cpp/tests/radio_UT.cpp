#include "tests/radio_UT.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>
namespace {
    comm::RadioConfig config;
}

namespace comm
{

    Radio_UT::Radio_UT()
        : m_radio(config)
    {
        config.rxBufferSize = 1000;
        config.numBytesToRead = 400;
    }

    void Radio_UT::SetUpTestCase(void) {
    }
    
    void Radio_UT::SetUp(void)
    {
    }

    TEST_F(Radio_UT, mode_change) {
        EXPECT_TRUE(m_radio.setMode(OFF) == false); // default mode is off so no change expected
        EXPECT_TRUE(m_radio.mode == OFF);
        EXPECT_TRUE(m_radio.setMode(SLEEP) == true);
        EXPECT_TRUE(m_radio.mode == SLEEP);
        EXPECT_TRUE(m_radio.setMode(RECEIVE) == true);
        EXPECT_TRUE(m_radio.mode == RECEIVE);
        EXPECT_TRUE(m_radio.setMode(TRANSMIT) == true);
        EXPECT_TRUE(m_radio.mode == TRANSMIT);
        EXPECT_TRUE(m_radio.setMode(TRANSMIT) == false); // check duplicate mode change
        EXPECT_TRUE(m_radio.mode == TRANSMIT);
    }

    TEST_F(Radio_UT, clearRxBuffer) {
        // Populate rx buffer
        for (int i = 0; i < 5; i++) {
            m_radio.rxBuffer.push_back(i);
        }
        EXPECT_TRUE(m_radio.rxBuffer.size() == 5);

        // Clear buffer
        m_radio.clearRxBuffer();
        EXPECT_TRUE(m_radio.rxBuffer.size() == 0);
        
    } 

    TEST_F(Radio_UT, bufferRxMsg) {
        const int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        
        std::vector<uint8_t> empty;
        EXPECT_TRUE(m_radio.bufferRxMsg(empty, false) == 0); // buffer with no bytes

        EXPECT_TRUE(m_radio.bufferRxMsg(dataIn, false) == msgLength); // no buffer
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_radio.rxBuffer[i]);
        }
        
        EXPECT_TRUE(m_radio.bufferRxMsg(dataIn, false) == msgLength); // repeat no buffer
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength);
        
        EXPECT_TRUE(m_radio.bufferRxMsg(dataIn, true) == msgLength); // buffer
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength*2);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_radio.rxBuffer[i]);
            EXPECT_TRUE(data[i] == m_radio.rxBuffer[i+5]);
        }
    }

    TEST_F(Radio_UT, processRxBytes) {
        const int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        
        EXPECT_TRUE(m_radio.processRxBytes(dataIn, false) == msgLength);
        
    }

    TEST_F(Radio_UT, bufferTxMsg) {
        const int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        
        m_radio.bufferTxMsg(dataIn);
        EXPECT_TRUE(m_radio.txBuffer.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_radio.txBuffer[i]);
        }
       
    }

    TEST_F(Radio_UT, createMsg) {
        const int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        
        std::vector<uint8_t> dataOut = m_radio.createMsg(dataIn);
        EXPECT_TRUE(dataOut.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(dataOut[i] == dataIn[i]);
        }
    }    

}
