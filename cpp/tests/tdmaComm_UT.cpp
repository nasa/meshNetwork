#include "tests/tdmaComm_UT.hpp"
#include "comm/tdmaMsgProcessor.hpp"
#include "comm/radio.hpp"
#include "comm/SLIPMsgParser.hpp"
#include "comm/SLIPMsg.hpp"
#include "comm/commands.hpp"
#include "node/nodeParams.hpp"
#include "comm/command.hpp"
#include "comm/tdmaCmds.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <cmath>
#include <memory>
#include "comm/utilities.hpp"

using std::vector;
using node::NodeParams;

namespace {
    serial::Serial ser("/dev/ttyUSB0", 9600, serial::Timeout::simpleTimeout(10));
    comm::RadioConfig config;
    comm::Radio radio(&ser, config);
    comm::SLIPMsgParser msgParser(10, 100);
}

namespace comm
{
    TDMAComm_UT::TDMAComm_UT() 
    {
        // Load configuration
        node::NodeParams::loadParams("nodeConfig.json");

        // Create comm instance
        m_msgProcessors.push_back(&m_tdmaProcessor);
        m_tdmaComm = TDMAComm(m_msgProcessors, &radio, &msgParser);    
    }

    void TDMAComm_UT::SetUpTestCase(void) {
        //Cmds::loadCmdDict();
    }
    
    void TDMAComm_UT::SetUp(void)
    {
    }

    TEST_F(TDMAComm_UT, resetTDMASlot) {
        return;
        double frameTime = 0.0;

        // Test through range of valid slots
        for (unsigned int i = 0; i < m_tdmaComm.maxNumSlots; i++) {
            // Start of slot
            frameTime = m_tdmaComm.slotLength*i;
            m_tdmaComm.resetTDMASlot(frameTime);
            EXPECT_TRUE(std::abs(m_tdmaComm.slotTime) < 1e-5);
            
            // End of slot
            frameTime = m_tdmaComm.slotLength*(i+1) - 0.01;
            m_tdmaComm.resetTDMASlot(frameTime);
            EXPECT_TRUE(std::abs(m_tdmaComm.slotTime - (m_tdmaComm.slotLength - 0.01)) < 1e-5);
            
            // Verify correct slot number
            EXPECT_TRUE(m_tdmaComm.slotNum == i + 1);

        }

        // Test with frame time greater than cycle time
        frameTime = m_tdmaComm.cycleLength;
        m_tdmaComm.resetTDMASlot(frameTime);
        EXPECT_TRUE(m_tdmaComm.slotNum = m_tdmaComm.maxNumSlots);

    } 
    
    TEST_F(TDMAComm_UT, setTDMAMode) {
        m_tdmaComm.receiveComplete = true;
        m_tdmaComm.transmitComplete = true;

        // Test non-transmit/receive mode
        m_tdmaComm.tdmaMode = TDMA_RECEIVE;
        m_tdmaComm.setTDMAMode(TDMA_SLEEP);        
        EXPECT_TRUE(m_tdmaComm.receiveComplete); // flags shouldn't change
        EXPECT_TRUE(m_tdmaComm.transmitComplete);

        // Set receive
        m_tdmaComm.tdmaMode = TDMA_SLEEP;
        m_tdmaComm.setTDMAMode(TDMA_RECEIVE);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_RECEIVE);
        EXPECT_TRUE(m_tdmaComm.receiveComplete == false);
        EXPECT_TRUE(m_tdmaComm.transmitComplete == true); // transmit status not reset
        m_tdmaComm.receiveComplete = true;
        m_tdmaComm.setTDMAMode(TDMA_RECEIVE); // test entering same mode
        EXPECT_TRUE(m_tdmaComm.receiveComplete == true); // should not be reset

        // Set transmit      
        m_tdmaComm.receiveComplete = true;
        m_tdmaComm.setTDMAMode(TDMA_TRANSMIT);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_TRANSMIT);
        EXPECT_TRUE(m_tdmaComm.transmitComplete == false);
        EXPECT_TRUE(m_tdmaComm.receiveComplete == true); // receive status should be reset
        m_tdmaComm.transmitComplete = true;
        m_tdmaComm.setTDMAMode(TDMA_TRANSMIT); // test entering same mode
        EXPECT_TRUE(m_tdmaComm.transmitComplete == true); // should not be reset
        
    }

    TEST_F(TDMAComm_UT, checkForInit) {
        // Confirm radio is initially off
        EXPECT_TRUE(radio.mode == RADIO_OFF);
        
        // Test not receiving message 
        m_tdmaComm.checkForInit();
        EXPECT_TRUE(radio.mode == RADIO_RECEIVE);
        EXPECT_TRUE(m_tdmaComm.commStartTime < 0);

        // Test receiving MeshStatus message
        uint8_t sourceId = 5;
        uint32_t startTime = (int)util::getTime();
        TDMA_MeshStatus meshStatus(startTime, TDMASTATUS_NOMINAL, createHeader(TDMACmds::MeshStatus, sourceId, node::NodeParams::getCmdCounter()));
        std::vector<uint8_t> msg = meshStatus.serialize();    
        m_tdmaComm.bufferTxMsg(msg); // send MeshStatus out via loopback
        m_tdmaComm.sendBuffer();
        usleep(100000);
        m_tdmaComm.checkForInit();
        EXPECT_TRUE(std::abs(m_tdmaComm.commStartTime - startTime) < 1e-5);
        
    }

    TEST_F(TDMAComm_UT, checkTimeOffset) {
        // Check with in bounds time offset
        double offset = NodeParams::config.commConfig.operateSyncBound - 0.001;
        EXPECT_TRUE(m_tdmaComm.checkTimeOffset(offset) == 0); // offset in bounds
        EXPECT_TRUE(node::NodeParams::nodeStatus[node::NodeParams::config.nodeId-1].timeOffset == offset);
        EXPECT_TRUE(m_tdmaComm.timeOffsetTimer < 0); // timer cleared

        // Check with out of bounds value
        offset = NodeParams::config.commConfig.operateSyncBound + 0.001;
        EXPECT_TRUE(m_tdmaComm.checkTimeOffset(offset) == 1); // offset not in bounds

        // Check with no offset available
        m_tdmaComm.checkTimeOffset(); // offset not in bounds
        EXPECT_TRUE(node::NodeParams::nodeStatus[node::NodeParams::config.nodeId-1].timeOffset == comm::FormationClock::invalidOffset);
        EXPECT_TRUE(m_tdmaComm.timeOffsetTimer >= 0); // timer started

        // Test timer clear
        offset = NodeParams::config.commConfig.operateSyncBound;
        m_tdmaComm.checkTimeOffset(offset);
        EXPECT_TRUE(m_tdmaComm.timeOffsetTimer < 0); // timer cleared

        // Check elapsed timer
        m_tdmaComm.timeOffsetTimer = NodeParams::config.commConfig.offsetTimeout + 1.0;
        EXPECT_TRUE(m_tdmaComm.checkTimeOffset() == 2);
        EXPECT_TRUE(m_tdmaComm.tdmaFailsafe);
    }

    TEST_F(TDMAComm_UT, initMesh) {
        double testTime = util::getTime();
        m_tdmaComm.commStartTime = testTime - 10.0;
        m_tdmaComm.rxBufferReadPos = 10;

        // Confirm pre-test conditions
        ASSERT_TRUE(m_tdmaComm.inited == false);
        ASSERT_TRUE(m_tdmaComm.tdmaCmds.size() == 0);

        // Call method and check results
        m_tdmaComm.initMesh(testTime);
        EXPECT_TRUE(m_tdmaComm.inited == true);
        std::unordered_map<uint8_t, std::unique_ptr<Command> >::iterator it;
        it = m_tdmaComm.tdmaCmds.find(TDMACmds::MeshStatus);
        EXPECT_TRUE(it != m_tdmaComm.tdmaCmds.end()); // command present
        it = m_tdmaComm.tdmaCmds.find(TDMACmds::LinkStatus);
        EXPECT_TRUE(it != m_tdmaComm.tdmaCmds.end()); // command present
        it = m_tdmaComm.tdmaCmds.find(TDMACmds::TimeOffset);
        EXPECT_TRUE(it != m_tdmaComm.tdmaCmds.end()); // command present
        EXPECT_TRUE(m_tdmaComm.rxBufferReadPos == 0);
    }

    TEST_F(TDMAComm_UT, syncTDMAFrame) {
        // Set parameters that should be updated by syncTDMAFrame
        double testTime = 5.0;
        m_tdmaComm.frameStartTime = 0.0;
        m_tdmaComm.rxBufferReadPos = 100;
        m_tdmaComm.commStartTime = testTime - 0.5*m_tdmaComm.frameLength;
        m_tdmaComm.initMesh(util::getTime());
        dynamic_cast<TDMA_MeshStatus *>(m_tdmaComm.tdmaCmds[TDMACmds::MeshStatus].get())->status = TDMASTATUS_BLOCK_TX;
        dynamic_cast<TDMA_TimeOffset *>(m_tdmaComm.tdmaCmds[TDMACmds::TimeOffset].get())->timeOffset = 10.0;
        std::vector<uint8_t> dummyStatus(NodeParams::config.maxNumNodes, 5);
        dynamic_cast<TDMA_LinkStatus *>(m_tdmaComm.tdmaCmds[TDMACmds::LinkStatus].get())->linkStatus = dummyStatus;
        
        // Call method under test
        m_tdmaComm.syncTDMAFrame(testTime);
        EXPECT_TRUE(m_tdmaComm.rxBufferReadPos == 0);
        EXPECT_TRUE(m_tdmaComm.frameTime == 0.5*m_tdmaComm.frameLength);
        EXPECT_TRUE(m_tdmaComm.frameStartTime == testTime - m_tdmaComm.frameTime);

        // Check that outgoing messages were properly updated
        EXPECT_TRUE(dynamic_cast<TDMA_MeshStatus *>(m_tdmaComm.tdmaCmds[TDMACmds::MeshStatus].get())->status == TDMASTATUS_NOMINAL);
        EXPECT_TRUE(dynamic_cast<TDMA_TimeOffset *>(m_tdmaComm.tdmaCmds[TDMACmds::TimeOffset].get())->timeOffset != 10.0);
        for (unsigned int i = 0; i < dummyStatus.size(); i++) {
            EXPECT_TRUE(dummyStatus[i] != dynamic_cast<TDMA_LinkStatus *>(m_tdmaComm.tdmaCmds[TDMACmds::LinkStatus].get())->linkStatus[i]);
        }

        // Check that rx buffer position reset
        EXPECT_TRUE(m_tdmaComm.rxBufferReadPos == 0);

        // Verify time offset checked
        EXPECT_TRUE(m_tdmaComm.timeOffsetTimer >= 0.0);
    }
   
    TEST_F(TDMAComm_UT, updateFrameTime) {
        // Test in cycle
        double testTime = util::getTime();
        m_tdmaComm.commStartTime = testTime;
        m_tdmaComm.frameStartTime = testTime - 0.5*m_tdmaComm.cycleLength;
        EXPECT_TRUE(m_tdmaComm.updateFrameTime(testTime) == 0); 

        // Test in sleep
        EXPECT_TRUE(m_tdmaComm.updateFrameTime(testTime + 0.5*m_tdmaComm.cycleLength + 0.01) == 1); 

    }

    TEST_F(TDMAComm_UT, initComm) {
        double testTime = util::getTime();
        
        // Confirm starting conditions
        radio.setMode(RADIO_OFF);
        ASSERT_TRUE(m_tdmaComm.initStartTime < 0.0);
        
        // Check radio change to receive
        m_tdmaComm.initComm(testTime);
        EXPECT_TRUE(m_tdmaComm.initStartTime == testTime);
        m_tdmaComm.initComm(testTime + 0.01);
        EXPECT_TRUE(radio.mode == RADIO_RECEIVE);
        
        // Send MeshStatus message and confirm commStartTime update
        uint32_t commStartTime = (int)testTime;
        uint8_t sourceId = 1;
        uint8_t tdmaStatus = TDMASTATUS_NOMINAL;        
        CmdHeader header = createHeader(TDMACmds::MeshStatus, sourceId, node::NodeParams::getCmdCounter());
        TDMA_MeshStatus cmd = TDMA_MeshStatus(commStartTime, tdmaStatus, header);
        std::vector<uint8_t> msg = cmd.serialize();
        m_tdmaComm.bufferTxMsg(msg);
        m_tdmaComm.sendBuffer();
        usleep(100000);
        m_tdmaComm.initComm(testTime);
        EXPECT_TRUE((int)m_tdmaComm.commStartTime == commStartTime);
        
    }

    TEST_F(TDMAComm_UT, initCommTimeout) {
        // Test init timer elapsed
        double testTime = util::getTime();
        m_tdmaComm.initComm(testTime);
        ASSERT_TRUE(m_tdmaComm.initStartTime == testTime);
        ASSERT_TRUE(m_tdmaComm.inited == false);

        // Elapse timer and confirm response
        m_tdmaComm.initComm(testTime + m_tdmaComm.initTimeToWait);
        EXPECT_TRUE(m_tdmaComm.inited == true);
        EXPECT_TRUE(m_tdmaComm.commStartTime == ceil(testTime + m_tdmaComm.initTimeToWait));
    }
 
    TEST_F(TDMAComm_UT, updateMode_tdmaFailsafe) {
        m_tdmaComm.tdmaMode = TDMA_SLEEP; 
        
        // Test TDMA Failsafe
        m_tdmaComm.tdmaFailsafe = true;
        ASSERT_TRUE(m_tdmaComm.tdmaMode != TDMA_FAILSAFE);
        m_tdmaComm.updateMode(0.0);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_FAILSAFE);
    }

    TEST_F(TDMAComm_UT, updateMode_endOfCycle) {
        // Test end of cycle
        m_tdmaComm.tdmaMode = TDMA_RECEIVE;
        m_tdmaComm.updateMode(m_tdmaComm.cycleLength);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_SLEEP);
    }

    TEST_F(TDMAComm_UT, updateMode_blockTransmit) {
        // Test block transmit
        m_tdmaComm.tdmaMode = TDMA_SLEEP; 
        m_tdmaComm.blockTxStatus.status = BLOCKTX_ACTIVE;
        m_tdmaComm.blockTxStatus.txNode = NodeParams::config.nodeId;
        m_tdmaComm.updateMode(0.0);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_BLOCKTX); // transmitting node
        m_tdmaComm.blockTxStatus.txNode = NodeParams::config.nodeId + 1;
        m_tdmaComm.updateMode(0.0);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_BLOCKRX); // receiving node
    }

    TEST_F(TDMAComm_UT, updateMode_normal) {
        m_tdmaComm.tdmaMode = TDMA_SLEEP; 
        m_tdmaComm.transmitSlot = 1;        

        // Transmit slot
        m_tdmaComm.updateMode(0.0);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_INIT);
        m_tdmaComm.updateMode(m_tdmaComm.enableLength);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_INIT);
        m_tdmaComm.updateMode(m_tdmaComm.beginTxTime);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_TRANSMIT);
        m_tdmaComm.updateMode(m_tdmaComm.endTxTime);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_SLEEP);

        // Receive slot
        ASSERT_TRUE(m_tdmaComm.slotNum == 1);
        m_tdmaComm.updateMode(m_tdmaComm.slotLength);
        EXPECT_TRUE(m_tdmaComm.slotNum == 2);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_INIT);
        m_tdmaComm.updateMode(m_tdmaComm.slotLength + m_tdmaComm.enableLength);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_RECEIVE);
        m_tdmaComm.updateMode(m_tdmaComm.slotLength + m_tdmaComm.endRxTime);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_SLEEP);
        
    }

    TEST_F(TDMAComm_UT, sleep) {
        // Test for frame exceedance
        m_tdmaComm.frameStartTime = util::getTime() - m_tdmaComm.frameLength - 0.011;
        ASSERT_TRUE(m_tdmaComm.frameExceedanceCount == 0);
        m_tdmaComm.sleep();
        EXPECT_TRUE(m_tdmaComm.frameExceedanceCount == 1);
    }

    TEST_F(TDMAComm_UT, sendTDMACmds) {
        m_tdmaComm.commStartTime = util::getTime();
        double flooredStartTime = floor(m_tdmaComm.commStartTime);
        m_tdmaComm.tdmaCmds[TDMACmds::MeshStatus] = std::unique_ptr<Command>(new TDMA_MeshStatus(flooredStartTime, m_tdmaComm.tdmaStatus, CmdHeader(TDMACmds::MeshStatus), 0.5));
        
        // Check command properly buffered
        ASSERT_TRUE(m_tdmaComm.radio->txBuffer.size() == 0);
        m_tdmaComm.sendTDMACmds();
        EXPECT_TRUE(m_tdmaComm.radio->txBuffer.size() > 0);
        
        // Wait for resend
        m_tdmaComm.radio->txBuffer.clear();
        usleep(100000);
        ASSERT_TRUE(m_tdmaComm.radio->txBuffer.size() == 0);
        m_tdmaComm.sendTDMACmds(); // should not send
        EXPECT_TRUE(m_tdmaComm.radio->txBuffer.size() == 0);
        usleep(400000);
        m_tdmaComm.sendTDMACmds(); // should send
        EXPECT_TRUE(m_tdmaComm.radio->txBuffer.size() > 0);
        
    }

    TEST_F(TDMAComm_UT, sendMsg) {
        m_tdmaComm.transmitComplete = false;
        ser.read(500); // clear serial buffer
        radio.txBuffer.clear();

        // Test send only when conditions are met   
        std::vector<uint8_t> testMsg = {1,2,3,4,5};
        m_tdmaComm.tdmaMode = TDMA_RECEIVE;
        m_tdmaComm.enabled = false;
        ASSERT_TRUE(m_tdmaComm.radio->txBuffer.size() == 0);
        m_tdmaComm.radio->bufferTxMsg(testMsg);
        m_tdmaComm.sendMsg();
        EXPECT_TRUE(m_tdmaComm.radio->txBuffer.size() > 0); // message not sent
        EXPECT_TRUE(m_tdmaComm.transmitComplete == false);
        m_tdmaComm.enabled = true;
        m_tdmaComm.sendMsg();
        EXPECT_TRUE(m_tdmaComm.radio->txBuffer.size() > 0); // message still not sent
        m_tdmaComm.tdmaMode = TDMA_TRANSMIT;
        m_tdmaComm.sendMsg();
        EXPECT_TRUE(m_tdmaComm.radio->txBuffer.size() == 0); // message sent
        EXPECT_TRUE(m_tdmaComm.transmitComplete == true); // transmitComplete flat set

        // Test transmission of periodic commands
        ASSERT_TRUE(m_tdmaComm.cmdBuffer.size() == 0);
        ASSERT_TRUE(m_tdmaComm.cmdRelayBuffer.size() == 0);
        m_tdmaComm.tdmaCmds[TDMACmds::MeshStatus] = std::unique_ptr<Command>(new TDMA_MeshStatus(1, TDMASTATUS_NOMINAL, CmdHeader(TDMACmds::MeshStatus), 0.5));
        m_tdmaComm.sendMsg();
        usleep(100000);
        m_tdmaComm.readBytes();
        std::vector<uint8_t> serBytes = m_tdmaComm.radio->getRxBytes();
        EXPECT_TRUE(serBytes.size() > 0);
        EXPECT_TRUE(serBytes.back() == SLIP_END_TDMA);

        // Test command relay buffer
        std::vector<uint8_t> msg = {1,2,3,4,5,6,7,8,9,0};
        m_tdmaComm.radio->clearRxBuffer();
        m_tdmaComm.cmdRelayBuffer.insert(m_tdmaComm.cmdRelayBuffer.end(), msg.begin(), msg.end());
        m_tdmaComm.sendMsg();
        usleep(100000);
        m_tdmaComm.readBytes();
        serBytes = m_tdmaComm.radio->getRxBytes();
        EXPECT_TRUE(serBytes.size() == msg.size() + 1);
        for (unsigned int i = 0; i < msg.size(); i++) {
            EXPECT_TRUE(serBytes[i] == msg[i]);
        }
        EXPECT_TRUE(serBytes.back() == SLIP_END_TDMA);

        // Test command buffer
        m_tdmaComm.radio->clearRxBuffer();
        m_tdmaComm.cmdBuffer[TDMACmds::MeshStatus] = msg;
        m_tdmaComm.sendMsg();
        EXPECT_TRUE(m_tdmaComm.cmdBuffer.size() == 0); // command buffer flushed out
        usleep(100000);
        m_tdmaComm.readBytes();
        EXPECT_TRUE(m_tdmaComm.radio->getRxBytes().size() > 0);

    }

    TEST_F(TDMAComm_UT, readMsgs) {
        vector<uint8_t> msg = {1, 2, 3, 4, 5};
        ser.write(msg);
       
        // Test for end of transmission not found
        m_tdmaComm.radio->clearRxBuffer(); 
        m_tdmaComm.rxBufferReadPos = 0;
        m_tdmaComm.sendBytes(msg);
        usleep(100000);
        EXPECT_TRUE(m_tdmaComm.readMsgs() == false);

        // Test for end of transmission found
        m_tdmaComm.radio->clearRxBuffer(); 
        m_tdmaComm.rxBufferReadPos = 0;
        msg.push_back(SLIP_END_TDMA);
        m_tdmaComm.sendBytes(msg);
        usleep(100000);
        EXPECT_TRUE(m_tdmaComm.readMsgs());
    }

    TEST_F(TDMAComm_UT, executeTDMAComm) {
        m_tdmaComm.transmitSlot = 2;
        m_tdmaComm.radio->clearRxBuffer();
        std::vector<uint8_t> testMsg = {1,2,3,4,5,6,7,8,9,0};
        
        // Test times
        std::vector<double> times = {0.0, m_tdmaComm.beginRxTime + 0.0001, m_tdmaComm.beginRxTime + 0.5*(m_tdmaComm.endRxTime - m_tdmaComm.beginRxTime), m_tdmaComm.endRxTime + 0.0001, m_tdmaComm.slotLength + 0.0001, m_tdmaComm.slotLength + m_tdmaComm.beginTxTime + 0.0001, m_tdmaComm.slotLength + 0.5*(m_tdmaComm.endTxTime - m_tdmaComm.beginRxTime), m_tdmaComm.slotLength + m_tdmaComm.endRxTime + 0.0001};
        // Test truth modes
        std::vector<uint8_t> truthModes = {TDMA_INIT, TDMA_RECEIVE, TDMA_RECEIVE, TDMA_SLEEP, TDMA_INIT, TDMA_TRANSMIT, TDMA_TRANSMIT, TDMA_SLEEP};

        // Force init to setup test
        m_tdmaComm.inited = true;
        m_tdmaComm.commStartTime = 0.0;
        m_tdmaComm.initMesh();
        usleep(1000000); // sleep to ensure periodic commands get queued
        m_tdmaComm.frameStartTime = 0.0;

        // Loop through test conditions
        for (unsigned int i = 0; i < times.size(); i++) {
            m_tdmaComm.executeTDMAComm(times[i]);
            EXPECT_TRUE(m_tdmaComm.tdmaMode == truthModes[i]);
            
            // Receive slot conditions
            if (i == 1) { // prep for read
                EXPECT_TRUE(m_tdmaComm.radio->mode == RADIO_RECEIVE);
                EXPECT_TRUE(m_tdmaComm.radio->rxBuffer.size() == 0);
                m_tdmaComm.sendBytes(testMsg); // send test message
                std::vector<uint8_t> endTDMA = {SLIP_END_TDMA};
                m_tdmaComm.sendBytes(endTDMA);
                usleep(100000);
            }
            else if (i == 2) { // post receive
                EXPECT_TRUE(m_tdmaComm.radio->mode == RADIO_SLEEP); // receive terminated once end byte received
                EXPECT_TRUE(m_tdmaComm.radio->rxBuffer.size() > 0);
            }

            // Transmit slot conditions
            else if (i == 4) { // begin of transmit slot
                m_tdmaComm.radio->clearRxBuffer();
                EXPECT_TRUE(m_tdmaComm.transmitComplete == false);
            }
            else if (i == 5) { // prep for transmit
                EXPECT_TRUE(m_tdmaComm.radio->mode == RADIO_TRANSMIT);
                m_tdmaComm.bufferTxMsg(testMsg); // buffer a message for transmission
            }
            else if (i == 6) { // post transmit
                EXPECT_TRUE(m_tdmaComm.radio->mode == RADIO_SLEEP);
                EXPECT_TRUE(m_tdmaComm.transmitComplete == true);
                usleep(100000); // delay to ensure transmission has been sent out
                
                // Check if bytes transmitted
                m_tdmaComm.readBytes();
                EXPECT_TRUE(m_tdmaComm.radio->rxBuffer.size() > 0);
            }
        }

        // Test non-time based modes
        // Failsafe
        m_tdmaComm.tdmaMode = TDMA_FAILSAFE;
        m_tdmaComm.radio->setMode(RADIO_SLEEP);
        m_tdmaComm.executeTDMAComm(0.0);
        EXPECT_TRUE(m_tdmaComm.radio->mode == RADIO_RECEIVE);
    
    }
    
    TEST_F(TDMAComm_UT, execute) {
        // Test for init start
        EXPECT_TRUE(m_tdmaComm.inited == false);
        m_tdmaComm.commStartTime = util::getTime(); 
        m_tdmaComm.execute();
        EXPECT_TRUE(m_tdmaComm.inited == true); // init performed

        // Test that full execution performed once inited
        m_tdmaComm.tdmaFailsafe = true; // set failsafe for easy indication
        m_tdmaComm.radio->setMode(RADIO_SLEEP);
        m_tdmaComm.execute();
        EXPECT_TRUE(m_tdmaComm.radio->mode == RADIO_RECEIVE); // radio to receive in failsafe   
     
    }

}
