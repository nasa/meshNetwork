#include "tests/radio_UT.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>

namespace {
    comm::RadioConfig config;
}

namespace comm
{
    serial::Serial ser("/dev/ttyUSB0", 9600, serial::Timeout::simpleTimeout(10));


    Radio_UT::Radio_UT()
        : m_radio(&ser, config)
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
        EXPECT_TRUE(m_radio.setMode(RADIO_OFF) == false); // default mode is off so no change expected
        EXPECT_TRUE(m_radio.mode == RADIO_OFF);
        EXPECT_TRUE(m_radio.setMode(RADIO_SLEEP) == true);
        EXPECT_TRUE(m_radio.mode == RADIO_SLEEP);
        EXPECT_TRUE(m_radio.setMode(RADIO_RECEIVE) == true);
        EXPECT_TRUE(m_radio.mode == RADIO_RECEIVE);
        EXPECT_TRUE(m_radio.setMode(RADIO_TRANSMIT) == true);
        EXPECT_TRUE(m_radio.mode == RADIO_TRANSMIT);
        EXPECT_TRUE(m_radio.setMode(RADIO_TRANSMIT) == false); // check duplicate mode change
        EXPECT_TRUE(m_radio.mode == RADIO_TRANSMIT);
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

        // No buffering
        EXPECT_TRUE(m_radio.bufferRxMsg(dataIn, false) == msgLength);
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_radio.rxBuffer[i]);
        }
        
        EXPECT_TRUE(m_radio.bufferRxMsg(dataIn, false) == msgLength); // repeat no buffer
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength);
        
        // Buffer with existing bytes
        EXPECT_TRUE(m_radio.bufferRxMsg(dataIn, true) == msgLength);
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength*2);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_radio.rxBuffer[i]);
            EXPECT_TRUE(data[i] == m_radio.rxBuffer[i+5]);
        }
    }

    TEST_F(Radio_UT, getRxBytes) {

        // Test that rx buffer is returned
        std::vector<uint8_t> data({1,2,3,4,5});
        unsigned int msgLength = data.size();
        m_radio.bufferRxMsg(data, true);
        std::vector<uint8_t> out = m_radio.getRxBytes();
        EXPECT_TRUE(out.size() == msgLength);
        for(unsigned int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(out[i] == data[i]);
        }
        
    }

    TEST_F(Radio_UT, processRxBytes) {
        // Base class method just buffers bytes
        std::vector<uint8_t> data({1,2,3,4,5});
        int msgLength = data.size();
        EXPECT_TRUE(m_radio.rxBuffer.size() == 0);
        EXPECT_TRUE(m_radio.processRxBytes(data, false) == msgLength);
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength);
        std::vector<uint8_t> out = m_radio.getRxBytes();
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(out[i] == data[i]);
        }
        
    }

    TEST_F(Radio_UT, sendMsg) {
        // Send a message
        std::vector<uint8_t> data({1,2,3,4,5});
        int msgLength = data.size();
        m_radio.sendMsg(data);
        usleep(50*1000);
        m_radio.readBytes(true);
        std::vector<uint8_t> rcvd = m_radio.getRxBytes();
        EXPECT_TRUE(rcvd.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(rcvd[i] == data[i]);
        }
    }
    
    TEST_F(Radio_UT, bufferTxMsg) {
        std::vector<uint8_t> data({1,2,3,4,5});
        int msgLength = data.size();
        
        m_radio.bufferTxMsg(data);
        EXPECT_TRUE(m_radio.txBuffer.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(data[i] == m_radio.txBuffer[i]);
        }

        // Confirm new bytes appended to buffer
        m_radio.bufferTxMsg(data);
        EXPECT_TRUE(m_radio.txBuffer.size() == 2*msgLength);
       
    }

    TEST_F(Radio_UT, createMsg) {
        std::vector<uint8_t> data({1,2,3,4,5});
        unsigned int msgLength = data.size();
        
        std::vector<uint8_t> dataOut = m_radio.createMsg(data);
        EXPECT_TRUE(dataOut.size() == msgLength);
        for(unsigned int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(dataOut[i] == data[i]);
        }
    }    

    TEST_F(Radio_UT, readBytes) {
        // Test read of bytes
        std::vector<uint8_t> data({1,2,3,4,5});
        int msgLength = data.size();
        ser.write(data);
        usleep(50*1000);
        EXPECT_TRUE(m_radio.readBytes(false) == msgLength);
        std::vector<uint8_t> dataOut = m_radio.getRxBytes();
        EXPECT_TRUE(dataOut.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(dataOut[i] == data[i]);
        }

        // Write again and verify buffer is not kept
        data.push_back(6); 
        msgLength = data.size();
        ser.write(data);
        usleep(50*1000);
        EXPECT_TRUE(m_radio.readBytes(false) == msgLength);
        dataOut = m_radio.getRxBytes();
        EXPECT_TRUE(dataOut.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(dataOut[i] == data[i]);
        }

        // Write again and confirm buffer is kept
        ser.write(data);
        usleep(50*1000);
        EXPECT_TRUE(m_radio.readBytes(true) == msgLength);
        dataOut = m_radio.getRxBytes();
        EXPECT_TRUE(dataOut.size() == 2*msgLength);
 
    }

    TEST_F(Radio_UT, sendBuffer) {
        // Check that buffered bytes are sent
        std::vector<uint8_t> data({1,2,3,4,5});
        int msgLength = data.size();
        
        m_radio.bufferTxMsg(data);
        EXPECT_TRUE(m_radio.sendBuffer() == 0);
        EXPECT_TRUE(m_radio.txBuffer.size() == 0); // buffer should be cleared
        usleep(50*1000);
        EXPECT_TRUE(m_radio.readBytes(true) == msgLength);
        std::vector<uint8_t> out = m_radio.getRxBytes();
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(out[i] == data[i]);
        }

        // Test max buffer send
        m_radio.bufferTxMsg(data);
        int shortLength = 2;
        m_radio.sendBuffer(shortLength);
        usleep(50*1000);
        EXPECT_TRUE(m_radio.readBytes(true) == shortLength);
        out = m_radio.getRxBytes();
        EXPECT_TRUE(m_radio.txBuffer.size() == (msgLength - shortLength));
        for(int i = 0; i < shortLength; i++) {
            EXPECT_TRUE(out[i] == data[i]);
        }


    }

}
