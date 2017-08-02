#include "tests/serialComm_UT.hpp"
#include "comm/testMsgProcessor.hpp"
#include "comm/serialRadio.hpp"
#include "comm/commProcessor.hpp"
#include "comm/msgParser.hpp"
#include "comm/tdmaCmds.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <cmath>

using std::vector;

namespace {
    comm::TestMsgProcessor testProcessor;    
    vector<comm::MsgProcessor *> msgProcessors = {&testProcessor};
    serial::Serial serIn("/dev/ttyV3", 9600, serial::Timeout::simpleTimeout(10));
    serial::Serial ser("/dev/ttyV2", 9600, serial::Timeout::simpleTimeout(10));
    comm::RadioConfig config;
    comm::SerialRadio radio(&ser, config);
    comm::CommProcessor commProcessor(msgProcessors);
    comm::MsgParser msgParser(10);
}

namespace comm
{
    SerialComm_UT::SerialComm_UT() :
        m_serialComm(SerialComm(&commProcessor, &radio, &msgParser))
    {
    }

    void SerialComm_UT::SetUpTestCase(void) {
    }
    
    void SerialComm_UT::SetUp(void)
    {
    }

    TEST_F(SerialComm_UT, readBytes) {
        // Read bytes from serial line
        vector<uint8_t> testData = {1,2,3,4,5};
        serIn.write(testData);
        usleep(50*1000);

        m_serialComm.readBytes(true);
        EXPECT_TRUE(m_serialComm.radio->rxBuffer.size() == testData.size());
    }

    TEST_F(SerialComm_UT, readAndParseMsgs) {
        // Confirm messages read and parsed
        vector<uint8_t> testData = {1,2,3,4,5};
        serIn.write(testData);
        usleep(50*1000);

        m_serialComm.readMsgs();
        EXPECT_TRUE(m_serialComm.msgParser->parsedMsgs.size() == 1);
        serIn.write(testData);
        usleep(50*1000);
        m_serialComm.readMsgs();
        EXPECT_TRUE(m_serialComm.msgParser->parsedMsgs.size() == 2);
        EXPECT_TRUE(m_serialComm.radio->rxBuffer.size() == 0); // confirm rx buffer cleared
    }

    TEST_F(SerialComm_UT, sendMsg) {
        vector<uint8_t> testData = {1,2,3,4,5};
        
        // Check initial values
        EXPECT_TRUE(std::abs(m_serialComm.lastMsgSentTime - 0.0) < 1e-6); 
        EXPECT_TRUE(m_serialComm.msgCounter == 0); 

        // Send message
        m_serialComm.sendMsg(testData);
        EXPECT_TRUE(m_serialComm.lastMsgSentTime > 0.0); 
        EXPECT_TRUE(m_serialComm.msgCounter == 1);
        vector<uint8_t> readBytes;
        serIn.read(readBytes, 100);
        EXPECT_TRUE(readBytes.size() >= 5);
        
    }
    
    TEST_F(SerialComm_UT, bufferTxMsg) {
        m_serialComm.radio->txBuffer.clear(); // clear tx buffer
        vector<uint8_t> testData = {1,2,3,4,5};
        m_serialComm.bufferTxMsg(testData);
        EXPECT_TRUE(m_serialComm.radio->txBuffer.size() >= 5);
    }

    TEST_F(SerialComm_UT, sendBuffer) {
        m_serialComm.radio->txBuffer.clear(); // clear tx buffer
        
        // Buffer bytes
        vector<uint8_t> testData = {1,2,3,4,5};
        m_serialComm.bufferTxMsg(testData);
    
        // Send buffer
        m_serialComm.sendBuffer();
        EXPECT_TRUE(m_serialComm.radio->txBuffer.size() == 0);
    }

    TEST_F(SerialComm_UT, processMsg) {
        vector<uint8_t> msg = {TDMACmds::MeshStatus,2,3,4,5};
        MsgProcessorArgs args;
        EXPECT_TRUE(m_serialComm.processMsg(msg, args) != -1);
    } 
         
}
