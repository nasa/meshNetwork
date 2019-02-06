#include "tests/tdmaMsgProcessor_UT.hpp"
#include "comm/tdmaCmds.hpp"
#include "comm/tdmaComm.hpp"
#include "comm/cmdHeader.hpp"
#include "comm/commands.hpp"
#include "node/nodeParams.hpp"
#include "node/nodeState.hpp"
#include <gtest/gtest.h>
#include <cmath>
#include <unistd.h>

using std::vector;

namespace {

}

namespace comm
{
    TDMAMsgProcessor_UT::TDMAMsgProcessor_UT() 
    {
        // Load configuration
        node::NodeParams::loadParams("nodeConfig.json");

        // Populate message processor args
        m_args.cmdQueue = &m_cmdQueue;
        m_args.relayBuffer = &m_relayBuffer;

        // Load command dictionary for use
        std::unordered_map<uint8_t, comm::HeaderType> tdmaCmdDict = TDMACmds::getCmdDict();
        Cmds::updateCmdDict(tdmaCmdDict);
        
    }

    void TDMAMsgProcessor_UT::SetUpTestCase(void) {
    }
    
    void TDMAMsgProcessor_UT::SetUp(void)
    {
    }

    TEST_F(TDMAMsgProcessor_UT, processMsg) {
        // Test all commands processed by NodeMsgProcessor
        std::vector<uint8_t> header;
        std::vector<uint8_t> msgBytes;
        
        // TDMACmds::TimeOffset
        uint8_t sourceId = 1;
        double offset = 2.1;
        CmdHeader cmdHeader = createHeader(TDMACmds::TimeOffset, sourceId);
        TDMA_TimeOffset timeOffset(offset, cmdHeader);
        msgBytes = timeOffset.serialize(); 
        EXPECT_TRUE(m_tdmaMsgProcessor.processMsg(TDMACmds::TimeOffset, msgBytes, m_args));
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].timeOffset == offset);

        // TDMACmds::TimeOffsetSummary

        // TDMACmds::MeshStatus
        cmdHeader = createHeader(TDMACmds::MeshStatus, sourceId);
        unsigned int startTime = ceil(node::NodeParams::clock.getTime());
        TDMA_MeshStatus meshStatus(startTime, TDMASTATUS_NOMINAL, cmdHeader);
        msgBytes = meshStatus.serialize(); 
        EXPECT_TRUE(m_tdmaMsgProcessor.processMsg(TDMACmds::MeshStatus, msgBytes, m_args));
        EXPECT_TRUE(m_cmdQueue.find(TDMACmds::MeshStatus) != m_cmdQueue.end()); // command put in queue

        // TDMACmds::LinkStatus
        cmdHeader = createHeader(TDMACmds::LinkStatus, sourceId);
        std::vector<uint8_t> statusIn = {node::NoLink, node::IndirectLink, node::GoodLink, node::BadLink, node::NoLink, node::NoLink};
        TDMA_LinkStatus linkStatus(statusIn, cmdHeader);
        msgBytes = linkStatus.serialize();
        EXPECT_TRUE(m_tdmaMsgProcessor.processMsg(TDMACmds::LinkStatus, msgBytes, m_args));
        for (unsigned int i = 0; i < node::NodeParams::linkStatus[sourceId-1].size(); i++) {
            EXPECT_TRUE(node::NodeParams::linkStatus[sourceId-1][i] == statusIn[i]);
        } 

        // TDMACmds::LinkStatusSummary

    }

}
