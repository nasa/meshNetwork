#include "tests/serialRadio_UT.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>

namespace {
    comm::RadioConfig config;
}
namespace comm
{
    serial::Serial serIn("/dev/ttyV3", 9600, serial::Timeout::simpleTimeout(10));
    serial::Serial ser("/dev/ttyV2", 9600, serial::Timeout::simpleTimeout(10));

    SerialRadio_UT::SerialRadio_UT()
        : m_radio(&ser, config)
    {
        config.rxBufferSize = 1000;
        config.numBytesToRead = 400;
    }

    void SerialRadio_UT::SetUpTestCase(void) {
        // Clear out serial
        std::vector<uint8_t> temp;
        serIn.read(temp, 1000);
    }
    
    void SerialRadio_UT::SetUp(void)
    {
    }

    TEST_F(SerialRadio_UT, readBytes) { // NOT COMPLETE
        // Send test bytes
        const int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        serIn.write(dataIn);
        usleep(50*1000);

                

        // Read bytes (no buffer)
        EXPECT_TRUE(m_radio.readBytes(false, 100) == msgLength);
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength);
        
        // Read with buffer
        serIn.write(dataIn);
        usleep(50*1000);
        EXPECT_TRUE(m_radio.readBytes(true, 100) == msgLength);
        EXPECT_TRUE(m_radio.rxBuffer.size() == msgLength*2);

    }
    
    TEST_F(SerialRadio_UT, sendMsg) {
        const int msgLength = 5;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
        
        m_radio.sendMsg(dataIn);
        std::vector<uint8_t> msgRcvd;
        EXPECT_TRUE(serIn.read(msgRcvd, 100) == msgLength);
        EXPECT_TRUE(msgRcvd.size() == msgLength);
        for(int i = 0; i < msgLength; i++) {
            EXPECT_TRUE(msgRcvd[i] == data[i]);
        }
    } 

    TEST_F(SerialRadio_UT, sendBuffer) {
        const int msgLength = 5;
        unsigned int maxLength = 1;
        uint8_t data[msgLength] = {1,2,3,4,5};
        std::vector<uint8_t> dataIn(data, data + msgLength);
       
        // Send with no max
        m_radio.bufferTxMsg(dataIn); 
        m_radio.sendBuffer();
        std::vector<uint8_t> msgRcvd;
        EXPECT_TRUE(serIn.read(msgRcvd, 100) == msgLength);

        // Send with max    
        m_radio.bufferTxMsg(dataIn); 
        m_radio.sendBuffer(maxLength);
        EXPECT_TRUE(serIn.read(msgRcvd, 100) == maxLength);

        // Send remainder of message
        m_radio.sendBuffer();
        EXPECT_TRUE(serIn.read(msgRcvd, 100) == msgLength - maxLength);
    } 
}
