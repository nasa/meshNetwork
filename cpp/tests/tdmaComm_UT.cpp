#include "tests/tdmaComm_UT.hpp"
#include "comm/tdmaMsgProcessor.hpp"
#include "comm/serialRadio.hpp"
#include "comm/commProcessor.hpp"
#include "comm/SLIPMsgParser.hpp"
#include "comm/SLIPMsg.hpp"
#include "comm/commands.hpp"
#include "node/nodeConfig.hpp"
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

namespace comm
{
    TDMAComm_UT::TDMAComm_UT() 
    {
        msgProcessors.push_back(&tdmaProcessor);
        util::setupSerial(serOut, "/dev/ttyV3", 9600, 10);
        util::setupSerial(serIn, "/dev/ttyV2", 9600, 10);
        radio = comm::SerialRadio(&serIn, config);
        commProcessor = CommProcessor(msgProcessors);
        msgParser = SLIPMsgParser(10, 100);
    }

    void TDMAComm_UT::SetUpTestCase(void) {
        //Cmds::loadCmdDict();
    }
    
    void TDMAComm_UT::SetUp(void)
    {
        node::NodeConfig config("nodeConfig.json");
        NodeParams::loadParams(config);
        m_tdmaComm = TDMAComm(&commProcessor, &radio, &msgParser);
        m_tdmaComm.initStartTime = -1.0;
        NodeParams::config.nodeId = 1;
    }

    TEST_F(TDMAComm_UT, resetTDMASlot) {
        // Test when slot number provided
        int slotNum = 2;
        m_tdmaComm.slotNum = 3;
        double frameTime = slotNum * m_tdmaComm.slotLength + 0.5*m_tdmaComm.slotLength;
        m_tdmaComm.resetTDMASlot(frameTime, slotNum);
        EXPECT_TRUE(m_tdmaComm.slotNum == (unsigned int)slotNum);
        EXPECT_TRUE(std::abs(m_tdmaComm.slotStartTime - ((slotNum - 1) * m_tdmaComm.slotLength)) < 1.0e-4);
        EXPECT_TRUE(std::abs(m_tdmaComm.slotTime - (frameTime - m_tdmaComm.slotStartTime)) < 1.0e-4);

        // Test without slot number
        m_tdmaComm.resetTDMASlot(0.0);
        EXPECT_TRUE(m_tdmaComm.slotNum == 1);
        frameTime = 0.95*m_tdmaComm.cycleLength;
        m_tdmaComm.resetTDMASlot(frameTime);
        EXPECT_TRUE(m_tdmaComm.slotNum == m_tdmaComm.maxNumSlots);
    } 
    
    TEST_F(TDMAComm_UT, setTDMAMode) {
        m_tdmaComm.receiveComplete = true;
        m_tdmaComm.transmitComplete = true;

        // Set receive
        m_tdmaComm.tdmaMode = TDMA_SLEEP;
        m_tdmaComm.setTDMAMode(TDMA_RECEIVE);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_RECEIVE);
        EXPECT_TRUE(m_tdmaComm.receiveComplete == false);
        EXPECT_TRUE(m_tdmaComm.transmitComplete == true);
        m_tdmaComm.receiveComplete = true;
        m_tdmaComm.setTDMAMode(TDMA_RECEIVE);
        EXPECT_TRUE(m_tdmaComm.receiveComplete == true); // should not be reset

        // Set transmit      
        m_tdmaComm.receiveComplete = true;
        m_tdmaComm.setTDMAMode(TDMA_TRANSMIT);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_TRANSMIT);
        EXPECT_TRUE(m_tdmaComm.transmitComplete == false);
        EXPECT_TRUE(m_tdmaComm.receiveComplete == true);
        m_tdmaComm.transmitComplete = true;
        m_tdmaComm.setTDMAMode(TDMA_TRANSMIT);
        EXPECT_TRUE(m_tdmaComm.transmitComplete == true); // should not be reset
         
    }

    TEST_F(TDMAComm_UT, updateMode_tdmaFailsafe) {
        m_tdmaComm.tdmaMode = TDMA_SLEEP; 
        
        // Test TDMA Failsafe
        NodeParams::tdmaFailsafe = true;
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
        m_tdmaComm.updateMode(m_tdmaComm.slotLength);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_INIT);
        m_tdmaComm.updateMode(m_tdmaComm.slotLength + m_tdmaComm.enableLength);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_RECEIVE);
        m_tdmaComm.updateMode(m_tdmaComm.slotLength + m_tdmaComm.endRxTime);
        EXPECT_TRUE(m_tdmaComm.tdmaMode == TDMA_SLEEP);
        
    }

    TEST_F(TDMAComm_UT, sleep) {
        // Test for frame exceedance
        m_tdmaComm.frameStartTime = util::getTime() - m_tdmaComm.frameLength;
        m_tdmaComm.sleep();
    }

    TEST_F(TDMAComm_UT, sendTDMACmds) {
        NodeParams::commStartTime = util::getTime();
        double flooredStartTime = floor(NodeParams::commStartTime);
        m_tdmaComm.tdmaCmds[TDMACmds::MeshStatus] = std::unique_ptr<Command>(new TDMA_MeshStatus(flooredStartTime, NodeParams::tdmaStatus, CmdHeader(TDMACmds::MeshStatus), NodeParams::config.commConfig.statusTxInterval));
        
        ASSERT_TRUE(m_tdmaComm.radio->txBuffer.size() == 0);
        m_tdmaComm.sendTDMACmds();
        EXPECT_TRUE(m_tdmaComm.radio->txBuffer.size() > 0);
    }

    TEST_F(TDMAComm_UT, syncTDMAFrame) {
        // Set parameters that should be updated by syncTDMAFrame
        m_tdmaComm.frameTime = 0.0;
        m_tdmaComm.frameStartTime = 0.0;
        m_tdmaComm.rxBufferReadPos = 100;
        NodeParams::commStartTime = util::getTime() - 55.12345;
        
        m_tdmaComm.syncTDMAFrame(util::getTime());
        EXPECT_TRUE(m_tdmaComm.rxBufferReadPos == 0);
        EXPECT_TRUE(m_tdmaComm.frameTime > 0.0);
        EXPECT_TRUE(m_tdmaComm.frameStartTime > 0.0);
    }
   
    TEST_F(TDMAComm_UT, updateFrameTime) {
        // Test in cycle
        m_tdmaComm.frameStartTime = 0.0;
        EXPECT_TRUE(m_tdmaComm.updateFrameTime(m_tdmaComm.cycleLength - 0.01) == 0); 

        // Test in sleep
        EXPECT_TRUE(m_tdmaComm.updateFrameTime(m_tdmaComm.cycleLength) == 1); 

    }
 
    TEST_F(TDMAComm_UT, initMesh) {
        ASSERT_TRUE(m_tdmaComm.inited == false);
        ASSERT_TRUE(m_tdmaComm.tdmaCmds.size() == 0);

        NodeParams::config.nodeId = 1;
        m_tdmaComm.initMesh(util::getTime());
        EXPECT_TRUE(m_tdmaComm.tdmaCmds.size() == 3);
        ASSERT_TRUE(m_tdmaComm.inited == true);
    }

    //TEST_F(TDMAComm_UT, checkForInit) {
    //    m_tdmaComm.radio->setMode(OFF);
        
    //    EXPECT_TRUE(m_tdmaComm.radio->mode == RECEIVE); // radio switched to receive
    //}


    TEST_F(TDMAComm_UT, checkForInit) {
        m_tdmaComm.radio->setMode(OFF);

        // Test without receiving message
        m_tdmaComm.checkForInit();
        EXPECT_TRUE(m_tdmaComm.radio->mode == RECEIVE); // radio switched to receive
        EXPECT_TRUE(std::abs(NodeParams::commStartTime - -1.0) < 1e-6); // no comm start time
        
        // Send a mesh status message and check for comm start update
        serOut.read(200); // clear buffer
        double startTime = util::getTime();
        unsigned int flooredTime = floor(startTime);
        TDMA_MeshStatus meshStatus(flooredTime, node::NOMINAL, CmdHeader(TDMACmds::MeshStatus), 0.0);
        vector<uint8_t> encodedMsg = msgParser.encodeMsg(meshStatus.pack());
        serOut.write(encodedMsg);
        m_tdmaComm.checkForInit();
        EXPECT_TRUE(std::abs(NodeParams::commStartTime - flooredTime) < 1e-3); // comm start time stored

    }

    TEST_F(TDMAComm_UT, init_timeout) {
        ASSERT_TRUE(m_tdmaComm.initStartTime == -1.0);
        ASSERT_TRUE(m_tdmaComm.inited == false);
        
        // Init and check for initStartTime update
        double startTime = util::getTime();
        m_tdmaComm.init(startTime);
        EXPECT_TRUE(m_tdmaComm.initStartTime > 0.0);
      
        // Check for initialization after timer expiration
        m_tdmaComm.init(startTime + m_tdmaComm.initTimeToWait);
        EXPECT_TRUE(m_tdmaComm.initStartTime > 0.0);
        EXPECT_TRUE(m_tdmaComm.inited == true);
        
      
    } 

    TEST_F(TDMAComm_UT, init_commStartTime) { // init with comm start time received
        NodeParams::commStartTime = util::getTime(); 
        ASSERT_TRUE(m_tdmaComm.inited == false);
        
        m_tdmaComm.init(util::getTime());
        EXPECT_TRUE(m_tdmaComm.inited == true);
        
    }

    TEST_F(TDMAComm_UT, sendMsg) {
        m_tdmaComm.tdmaMode = TDMA_TRANSMIT;
        m_tdmaComm.transmitComplete = false;
        serOut.read(500); // clear serial buffer

        // Send buffered commands
        TDMA_MeshStatus cmd(1, node::NOMINAL, CmdHeader(TDMACmds::MeshStatus), 0.0);
        unsigned int cmdSize = cmd.pack(util::getTime()).size();
        //cmd.bytes = vector<uint8_t>({1, 2, 3, 4, 5});
        cmd.txInterval = 0;
        m_tdmaComm.cmdBuffer.push_back(cmd);
        cmd.txInterval = 1.0;
        m_tdmaComm.cmdBuffer.push_back(cmd);
        m_tdmaComm.sendMsg();
        EXPECT_TRUE(m_tdmaComm.cmdBuffer.size() == 1); // 1 repeating command 
        EXPECT_TRUE(m_tdmaComm.transmitComplete == true);
        vector<uint8_t> rcvd;
        usleep(10);
        serOut.read(rcvd, 100);
        EXPECT_TRUE(rcvd.size() >= cmdSize*2);

        // Send relay commands
        m_tdmaComm.transmitComplete = false;
        m_tdmaComm.cmdRelayBuffer.push_back(vector<uint8_t>({1, 2, 3, 4, 5}));
        m_tdmaComm.sendMsg();
        EXPECT_TRUE(m_tdmaComm.cmdRelayBuffer.size() == 0); // buffer cleared
        EXPECT_TRUE(m_tdmaComm.transmitComplete == true);
        usleep(10);
        rcvd.clear();
        serOut.read(rcvd, 100);
        EXPECT_TRUE(rcvd.size() >= 5);


        // Send tx buffer
		m_tdmaComm.cmdBuffer.clear();
        vector<uint8_t> msg = {10, 20, 30, 40, 50};
        m_tdmaComm.radio->bufferTxMsg(msg);
        m_tdmaComm.sendMsg();
        usleep(10);
        rcvd.clear();
        serOut.read(rcvd, 100);
        ASSERT_TRUE(rcvd.size() == msg.size() + 1); // message + SLIP_END_TDMA byte
        for (unsigned int i = 0; i < msg.size(); i++) {
            EXPECT_TRUE(rcvd[i] == msg[i]);
        }
        
    }

    TEST_F(TDMAComm_UT, readMsg) {
        vector<uint8_t> msg = {1, 2, 3, 4, 5};
        serOut.write(msg);
        
        // Test for end of transmission found
        bool ret = m_tdmaComm.readMsg();
        EXPECT_TRUE(ret == false);
        msg.push_back(SLIP_END_TDMA);
        serOut.write(msg);
        ret = m_tdmaComm.readMsg();
        EXPECT_TRUE(ret == true);
    }

    TEST_F(TDMAComm_UT, execute) {
        // Test for init
        EXPECT_TRUE(m_tdmaComm.inited == false);
        NodeParams::commStartTime = util::getTime(); 
        m_tdmaComm.execute();
        EXPECT_TRUE(m_tdmaComm.inited == true); // init performed
        EXPECT_TRUE(std::abs(m_tdmaComm.frameTime - 0.0) < 1e-6); // full comm execution not performed

        // Test that full execution performed since now inited
        m_tdmaComm.execute();
        EXPECT_TRUE(std::abs(m_tdmaComm.frameTime - 0.0) > 1e-6);
        
    }

    TEST_F(TDMAComm_UT, executeTDMAComm) {
        
    }

}
