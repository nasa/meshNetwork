#include "tests/serialComm_UT.hpp"
#include "comm/radio.hpp"
#include "comm/msgParser.hpp"
#include "comm/SLIPMsgParser.hpp"
#include "comm/nodeCmds.hpp"
#include "node/nodeParams.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <cmath>

using std::vector;

namespace {
    serial::Serial ser("/dev/ttyUSB0", 9600, serial::Timeout::simpleTimeout(10));
    comm::RadioConfig config;
    comm::Radio radio(&ser, config);
    comm::MsgParser msgParser(10);
}

namespace comm
{
    SerialComm_UT::SerialComm_UT() 
    {
        // Load configuration and commands for testing
        node::NodeParams::loadParams("nodeConfig.json");   
        std::unordered_map<uint8_t, comm::HeaderType> nodeCmdDict = NodeCmds::getCmdDict();
        Cmds::updateCmdDict(nodeCmdDict);

        m_msgProcessors.push_back(&m_nodeProcessor);
        m_serialComm = SerialComm(m_msgProcessors, &radio, &msgParser);
    }

    void SerialComm_UT::SetUpTestCase(void) {
    }
    
    void SerialComm_UT::SetUp(void)
    {
    }

    TEST_F(SerialComm_UT, readBytes) {
        // Read bytes from serial port
        vector<uint8_t> testData = {1,2,3,4,5};
        ser.write(testData);
        usleep(50*1000);
        m_serialComm.readBytes(false);
        EXPECT_TRUE(m_serialComm.radio->rxBuffer.size() == testData.size());
        vector<uint8_t> out = m_serialComm.radio->getRxBytes();
        for (unsigned int i = 0; i < testData.size(); i++) {
            EXPECT_TRUE(out[i] == testData[i]);
        }
    }

    TEST_F(SerialComm_UT, sendBytes) {
        // Verify sendBytes method
        vector<uint8_t> testData = {1,2,3,4,5};
        EXPECT_TRUE(m_serialComm.sendBytes(testData) == testData.size());
        usleep(50*1000);
        m_serialComm.readBytes(false);
        EXPECT_TRUE(m_serialComm.radio->rxBuffer.size() == testData.size());
        vector<uint8_t> out = m_serialComm.radio->getRxBytes();
        for (unsigned int i = 0; i < testData.size(); i++) {
            EXPECT_TRUE(out[i] == testData[i]);
        }
    }

    TEST_F(SerialComm_UT, sendMsg) {
        vector<uint8_t> testData = {1,2,3,4,5};
        
        // Check initial values
        EXPECT_TRUE(std::abs(m_serialComm.lastMsgSentTime - 0.0) < 1e-6); 
        EXPECT_TRUE(m_serialComm.msgCounter == 0); 

        // Send message
        m_serialComm.sendMsg(testData);
        usleep(50*1000);
        EXPECT_TRUE(m_serialComm.lastMsgSentTime > 0.0); 
        EXPECT_TRUE(m_serialComm.msgCounter == 1);
        vector<uint8_t> readBytes;
        ser.read(readBytes, 100);
        EXPECT_TRUE(readBytes.size() == testData.size());
        
    }
    
    TEST_F(SerialComm_UT, parseMsgs) {
        ser.read(100); // flush serial    
        m_serialComm.radio->clearRxBuffer(); // clear rx buffer
    
        // Need real parser to parse multiple messages
        m_serialComm = SerialComm(m_msgProcessors, &radio, new SLIPMsgParser(10,100));

        SLIPMsgParser slipParser(10,100);
        vector<uint8_t> testData = {1,2,3,4,5};
        vector<uint8_t> encodedMsg = slipParser.encodeMsg(testData);
        m_serialComm.radio->bufferRxMsg(encodedMsg, false); // send twice
        m_serialComm.radio->bufferRxMsg(encodedMsg, true);
        usleep(50*1000);
        
        m_serialComm.parseMsgs();
        EXPECT_TRUE(m_serialComm.msgParser->parsedMsgs.size() == 2);       

        // Verify rx buffer cleared
        EXPECT_TRUE(m_serialComm.radio->rxBuffer.size() == 0);
    }

    TEST_F(SerialComm_UT, readMsgs) {
        // Confirm messages read and parsed
        vector<uint8_t> testData = {1,2,3,4,5};
        ser.write(testData);
        usleep(50*1000);

        m_serialComm.readMsgs(); // calls parseMsgs
        EXPECT_TRUE(m_serialComm.msgParser->parsedMsgs.size() == 1);
        for (unsigned int i = 0; i < m_serialComm.msgParser->parsedMsgs[0].size(); i++) {
            EXPECT_TRUE(m_serialComm.msgParser->parsedMsgs[0][i] == testData[i]);
        }
        ser.write(testData);
        usleep(50*1000);
        m_serialComm.readMsgs();
        EXPECT_TRUE(m_serialComm.msgParser->parsedMsgs.size() == 2);
        EXPECT_TRUE(m_serialComm.radio->rxBuffer.size() == 0); // confirm rx buffer cleared
    }
    
    TEST_F(SerialComm_UT, bufferTxMsg) {
        m_serialComm.radio->txBuffer.clear(); // clear tx buffer

        // Update message parser to verify bufferTxMsg encodes messages
        m_serialComm = SerialComm(m_msgProcessors, &radio, new SLIPMsgParser(10,100));

        vector<uint8_t> testData = {1,2,3,4,5};
        m_serialComm.bufferTxMsg(testData);
        EXPECT_TRUE(m_serialComm.radio->txBuffer.size() >= 5); // encoded length should be larger
    }

    TEST_F(SerialComm_UT, sendBuffer) {
        m_serialComm.radio->txBuffer.clear(); // clear tx buffer
        
        // Buffer bytes
        vector<uint8_t> testData = {1,2,3,4,5};
        m_serialComm.bufferTxMsg(testData);
        EXPECT_TRUE(m_serialComm.radio->txBuffer.size() > 0);
    
        // Send buffer
        m_serialComm.sendBuffer();
        usleep(50*1000);
        EXPECT_TRUE(m_serialComm.radio->txBuffer.size() == 0);
    
        // Verify sent message
        m_serialComm.readBytes(false);
        vector<uint8_t> out = m_serialComm.radio->getRxBytes();
        for (unsigned int i = 0; i < testData.size(); i++) {
            EXPECT_TRUE(out[i] == testData[i]);
        }
        
    }

    TEST_F(SerialComm_UT, processMsg) {
        // Create NoOp command for processing
        
        CmdHeader cmdHeader = createHeader(NodeCmds::NoOp, 1, node::NodeParams::getCmdCounter());
        Node_NoOp noOp(cmdHeader);
        vector<uint8_t> msg = noOp.serialize(); 
        MsgProcessorArgs args;
        args.cmdQueue = &(m_serialComm.cmdQueue);
        args.relayBuffer = &(m_serialComm.cmdRelayBuffer);
        EXPECT_TRUE(m_serialComm.processMsg(msg, args));
    } 

    TEST_F(SerialComm_UT, processMsgs) {
        // Create two different commands to test processMsgs method
        m_serialComm = SerialComm(m_msgProcessors, &radio, new SLIPMsgParser(10,100)); // need real parser for multiple messages
        
        CmdHeader cmdHeader = createHeader(NodeCmds::NoOp, 1, node::NodeParams::getCmdCounter());
        Node_NoOp noOp(cmdHeader);
        vector<uint8_t> msg1 = noOp.serialize(); 
        cmdHeader = createHeader(NodeCmds::ConfigRequest, 1, node::NodeParams::getCmdCounter());
        vector<uint8_t> configHash = node::NodeParams::config.calculateHash();
        Node_ConfigRequest configRequest(configHash, cmdHeader);
        vector<uint8_t> msg2 = configRequest.serialize(); 
        
        // Test processing of multiple messages
        m_serialComm.sendMsg(msg1);
        m_serialComm.sendMsg(msg2);
        usleep(50*1000);

        MsgProcessorArgs args;
        args.cmdQueue = &(m_serialComm.cmdQueue);
        args.relayBuffer = &(m_serialComm.cmdRelayBuffer);
        m_serialComm.processMsgs(args);
        EXPECT_TRUE(m_serialComm.cmdQueue.find(NodeCmds::NoOp) != m_serialComm.cmdQueue.end());
        EXPECT_TRUE(m_serialComm.cmdQueue.find(NodeCmds::ConfigRequest) != m_serialComm.cmdQueue.end());
    }
        
    TEST_F(SerialComm_UT, processBuffers) {
        // Test command relay buffer
        vector<uint8_t> testData = {1,2,3,4,5};
        m_serialComm.cmdRelayBuffer.insert(m_serialComm.cmdRelayBuffer.end(), testData.begin(), testData.end());
        m_serialComm.processBuffers();
        EXPECT_TRUE(m_serialComm.cmdRelayBuffer.size() == 0); // buffer flushed
        EXPECT_TRUE(m_serialComm.radio->txBuffer.size() == testData.size()); // buffer queued for transmit
        m_serialComm.radio->txBuffer.clear();

        // Test command buffer
        m_serialComm.cmdBuffer.insert({200, testData});
        m_serialComm.processBuffers();
        EXPECT_TRUE(m_serialComm.cmdBuffer.size() == 0); // buffer flushed
        EXPECT_TRUE(m_serialComm.radio->txBuffer.size() == testData.size()); // buffer queued for transmit
        
    }
 
}
