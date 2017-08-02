#include "tests/li1Radio_UT.hpp"
#include "GPIOWrapper/GPIOWrapper.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>
#include <vector>
#include <algorithm>
#include "comm/checksum.hpp"
using std::vector;

namespace {
    serial::Serial ser("/dev/ttyV2", 9600, serial::Timeout::simpleTimeout(10));
    serial::Serial serReceive("/dev/ttyV3", 9600, serial::Timeout::simpleTimeout(10));
    comm::RadioConfig config(200,100,100);

    // Test transmit command
    vector<uint8_t> transmitPayload = {1, 2, 3, 9, 8, 7, 140, 150, 160, 195, 185, 175};
    vector<uint8_t> transmitMsgBytes = {72, 101, 16, 3, 0, 12, 31, 85, 1, 2, 3, 9, 8, 7, 140, 150, 160, 195, 185, 175, 158, 44};
    // Test receive command *TODO* get properly formatted received data message
    vector<uint8_t> receivePayload = {192,49,50,51,52,53,54,55,56,57,48,49,50,51,52,53,54,55,56,57,48,192};
    vector<uint8_t> receiveMsgBytes = {72,101,32,4,0,40,76,180,134,162,64,64,64,64,96,156,158,134,130,152,152,225,3,240,192,49,50,51,52,53,54,55,56,57,48,49,50,51,52,53,54,55,56,57,48,192,181,122,227,49};
    
}

namespace comm
{
    Li1Radio_UT::Li1Radio_UT()
        : m_li1Radio(&ser, config)
    {
    }

    void Li1Radio_UT::SetUpTestCase(void) {
        // Clear out serial
        std::vector<uint8_t> temp;
        serReceive.read(temp, 1000);
    }
    
    void Li1Radio_UT::SetUp(void)
    {
    }

    TEST_F(Li1Radio_UT, createHeader) {
        Li1Cmd testCmd(comm::LI1_TRANSMIT, transmitPayload);
        m_li1Radio.createHeader(testCmd);
        ASSERT_TRUE(testCmd.msgBytes.size() == Li1Radio::headerLength);
        for (unsigned int i = 0; i < Li1Radio::headerLength; i++) {
            EXPECT_TRUE(testCmd.msgBytes[i] == transmitMsgBytes[i]);
        }
    }

    TEST_F(Li1Radio_UT, createPayload) {
        Li1Cmd testCmd(comm::LI1_TRANSMIT, transmitPayload);
        m_li1Radio.createHeader(testCmd); // create header so that payload checksum is correct
        m_li1Radio.createPayload(testCmd);
        ASSERT_TRUE(testCmd.msgBytes.size() == transmitMsgBytes.size());
        for (unsigned int i = 0; i < testCmd.msgBytes.size(); i++) {
            EXPECT_TRUE(testCmd.msgBytes[i] == transmitMsgBytes[i]);
        }        
    }
    
    TEST_F(Li1Radio_UT, createCommand) {
        Li1Cmd testCmd(comm::LI1_TRANSMIT, transmitPayload);
        m_li1Radio.createCommand(testCmd);
        ASSERT_TRUE(testCmd.msgBytes.size() == transmitMsgBytes.size());
        for (unsigned int i = 0; i < testCmd.msgBytes.size(); i++) {
            EXPECT_TRUE(testCmd.msgBytes[i] == transmitMsgBytes[i]);
        }        
    }
    
    TEST_F(Li1Radio_UT, createMsg) {
        vector<uint8_t> msgBytes = m_li1Radio.createMsg(transmitPayload);
        ASSERT_TRUE(msgBytes.size() == transmitMsgBytes.size());
        for (unsigned int i = 0; i < msgBytes.size(); i++) {
            EXPECT_TRUE(msgBytes[i] == transmitMsgBytes[i]);
        }
    }        

    TEST_F(Li1Radio_UT, parseCmdHeader) {
        Li1Cmd outCmd;
        EXPECT_TRUE(m_li1Radio.parseCmdHeader(outCmd, receiveMsgBytes));
        EXPECT_TRUE(outCmd.type == LI1_RECEIVED_DATA);
        EXPECT_TRUE(outCmd.header.size() == Li1Radio::headerLength - Li1Radio::lenSyncBytes - Li1Radio::checksumLen);
        ASSERT_TRUE(outCmd.rawHeader.size() == Li1Radio::headerLength - Li1Radio::lenSyncBytes);
        for (unsigned int i = 0; i < Li1Radio::headerLength - Li1Radio::lenSyncBytes; i++ ){
            EXPECT_TRUE(outCmd.rawHeader[i] == receiveMsgBytes[i+Li1Radio::lenSyncBytes]);
        }
    }

    TEST_F(Li1Radio_UT, parseCmdPayload) {
        Li1Cmd outCmd;
        // Populate raw header bytes (for proper checksum calculation)
        outCmd.rawHeader = vector<uint8_t>(receiveMsgBytes.begin() + Li1Radio::lenSyncBytes, receiveMsgBytes.begin() + Li1Radio::headerLength);
       
         // Test parsing of good data
        EXPECT_TRUE(m_li1Radio.parseCmdPayload(outCmd, receiveMsgBytes[5], vector<uint8_t>(receiveMsgBytes.begin() + Li1Radio::headerLength, receiveMsgBytes.end())) == receiveMsgBytes[5] + Li1Radio::checksumLen);
        ASSERT_TRUE(outCmd.payload.size() == receivePayload.size());
        for(unsigned int i = 0; i < outCmd.payload.size(); i++) {
            EXPECT_TRUE(outCmd.payload[i] == receivePayload[i]);
        }

        // Test incomplete data
        outCmd = Li1Cmd();
        EXPECT_TRUE(m_li1Radio.parseCmdPayload(outCmd, receiveMsgBytes[5], vector<uint8_t>(receiveMsgBytes.begin() + Li1Radio::headerLength, receiveMsgBytes.end()-1)) == receiveMsgBytes[5] + Li1Radio::checksumLen - 1);
        EXPECT_TRUE(outCmd.payload.size() == 0);
    } 

    TEST_F(Li1Radio_UT, parseCommand) {
        Li1Cmd outCmd;
        EXPECT_TRUE(m_li1Radio.parseCommand(outCmd, receiveMsgBytes) == receiveMsgBytes.size());
        EXPECT_TRUE(outCmd.type == LI1_RECEIVED_DATA);
        EXPECT_TRUE(outCmd.valid == true);
        
        // Check all parsed components
        ASSERT_TRUE(outCmd.rawHeader.size() == Li1Radio::headerLength - Li1Radio::lenSyncBytes);
        for (unsigned int i = 0; i < Li1Radio::headerLength - Li1Radio::lenSyncBytes; i++ ){
            EXPECT_TRUE(outCmd.rawHeader[i] == receiveMsgBytes[i+Li1Radio::lenSyncBytes]);
        }
        
        ASSERT_TRUE(outCmd.payload.size() == receivePayload.size());
        for(unsigned int i = 0; i < outCmd.payload.size(); i++) {
            EXPECT_TRUE(outCmd.payload[i] == receivePayload[i]);
        }
       
        // Pad input bytes and retest
        outCmd = Li1Cmd();
        vector<uint8_t> inputBytes = {10,20,30,40,50};
        inputBytes.insert(inputBytes.end(), receiveMsgBytes.begin(), receiveMsgBytes.end());
        EXPECT_TRUE(m_li1Radio.parseCommand(outCmd, inputBytes) == inputBytes.size());
        EXPECT_TRUE(outCmd.valid == true);
 
    }

    TEST_F(Li1Radio_UT, processRxBytes) {
        ASSERT_TRUE(m_li1Radio.rxBuffer.size() == 0); // confirm that rx buffer is empty

        // Test processing with buffering
        m_li1Radio.processRxBytes(receiveMsgBytes, true);
        EXPECT_TRUE(m_li1Radio.rxBuffer.size() == receivePayload.size());
        EXPECT_TRUE(m_li1Radio.cmdBuffer.size() == 1);
        
        m_li1Radio.processRxBytes(receiveMsgBytes, true);
        EXPECT_TRUE(m_li1Radio.rxBuffer.size() == 2*receivePayload.size());
        EXPECT_TRUE(m_li1Radio.cmdBuffer.size() == 2);
       
        // Test without buffering 
        m_li1Radio.processRxBytes(receiveMsgBytes, false);
        EXPECT_TRUE(m_li1Radio.rxBuffer.size() == receivePayload.size());

        // Test command rx buffer overflow
        m_li1Radio.cmdRxBuffer.push_back(1); // put dummy data into buffer
        ASSERT_TRUE(m_li1Radio.cmdRxBuffer.size() > 0);
        vector<uint8_t> dummyData(m_li1Radio.config.cmdRxBufferSize+1);
        std::fill(dummyData.begin(), dummyData.end(), 5);
        m_li1Radio.processRxBytes(dummyData, true);
        EXPECT_TRUE(m_li1Radio.cmdRxBuffer.size() == 0);
        

    }

    TEST_F(Li1Radio_UT, sendMsg) {
        // Transmit message
        EXPECT_TRUE(m_li1Radio.sendMsg(transmitPayload) == 1);
        
        // Check "transmitted" message
        vector<uint8_t> rcvdBytes;
        serReceive.read(rcvdBytes, 100);
        ASSERT_TRUE(rcvdBytes.size() == transmitMsgBytes.size());
        for (unsigned int i = 0; i < rcvdBytes.size(); i++) {
            EXPECT_TRUE(rcvdBytes[i] == transmitMsgBytes[i]);
        }        
        
        // Send amount larger than max payload
        vector<uint8_t> dummyData(Li1Radio::maxPayload+1);
        std::fill(dummyData.begin(), dummyData.end(), 5);
        EXPECT_TRUE(m_li1Radio.sendMsg(dummyData) == 2);
    }

}
