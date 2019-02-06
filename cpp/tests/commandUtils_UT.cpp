#include "tests/commandUtils_UT.hpp"
#include "node/nodeParams.hpp"
#include "comm/commands.hpp"
#include "comm/cmdHeader.hpp"
#include "comm/nodeCmds.hpp"
#include "comm/commandUtils.hpp"
#include "comm/msgProcessor.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <cmath>

using std::vector;

namespace {
    
}

namespace comm
{
    CommandUtils_UT::CommandUtils_UT()
    {
        // Load configuration and commands for testing
        node::NodeParams::loadParams("nodeConfig.json");   
        std::unordered_map<uint8_t, comm::HeaderType> nodeCmdDict = NodeCmds::getCmdDict();
        Cmds::updateCmdDict(nodeCmdDict);
    }

    void CommandUtils_UT::SetUpTestCase(void) {
    }
    
    void CommandUtils_UT::SetUp(void)
    {
    }

    TEST_F(CommandUtils_UT, checkCmdCounter) {
        // Create relay buffer
        std::vector<uint8_t> relayBuffer;

        // Test that command counter processed correctly
        // Test with command that shouldn't be relayed
        CmdHeader cmdHeader = createHeader(NodeCmds::NoOp, 1, node::NodeParams::getCmdCounter());
        Node_NoOp noOp(cmdHeader);
        vector<uint8_t> msg = noOp.serialize(); 
        EXPECT_TRUE(checkCmdCounter(noOp, msg, &relayBuffer));
        EXPECT_TRUE(relayBuffer.size() == 0); // command should not have been added
        EXPECT_TRUE(node::NodeParams::cmdHistory.find(cmdHeader.cmdCounter) == true);
            
        // Test with duplicate command counter
        EXPECT_FALSE(checkCmdCounter(noOp, msg, &relayBuffer));

        // Test with new command counter
        noOp.header.cmdCounter = node::NodeParams::getCmdCounter();
        EXPECT_TRUE(checkCmdCounter(noOp, msg, &relayBuffer));
        
        // Test with a command that should be relayed        
        std::vector<uint8_t> relayCmds = {NodeCmds::GCSCmd};
        Cmds::updateRelayCmds(relayCmds);
        cmdHeader = createHeader(NodeCmds::GCSCmd, 1, node::NodeParams::getCmdCounter());
        Node_GCSCmd gcsCmd(0, 0, cmdHeader);
        msg = gcsCmd.serialize(); 
        EXPECT_TRUE(checkCmdCounter(gcsCmd, msg, &relayBuffer));
        EXPECT_TRUE(relayBuffer.size() == msg.size()); // command should have been added

    }

    TEST_F(CommandUtils_UT, updateNodeMsgRcvdStatus) {
        // Test node comm status updated
        uint8_t sourceId = 1;
        CmdHeader cmdHeader = createHeader(NodeCmds::NoOp, sourceId, node::NodeParams::getCmdCounter());
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].present == false);
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].lastMsgRcvdTime < node::NodeParams::clock.getTime());
        updateNodeMsgRcvdStatus(cmdHeader);
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].present == true);
        EXPECT_TRUE(fabs(node::NodeParams::nodeStatus[sourceId-1].lastMsgRcvdTime - node::NodeParams::clock.getTime()) < 0.1);

        // Test node comm status not updated if a relayed command
        sourceId = 2;
        cmdHeader = createHeader(NodeCmds::GCSCmd, sourceId, node::NodeParams::getCmdCounter());
        updateNodeMsgRcvdStatus(cmdHeader);
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].present == false);
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].lastMsgRcvdTime < node::NodeParams::clock.getTime());
        
    }

    TEST_F(CommandUtils_UT, processHeader) {
        MsgProcessorArgs args;
        
        // Test for node comm status and command history update
        uint8_t sourceId = 3;
        CmdHeader cmdHeader = createHeader(NodeCmds::NoOp, sourceId, node::NodeParams::getCmdCounter());
        Node_NoOp noOp(cmdHeader);
        vector<uint8_t> msg = noOp.serialize(); 
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].present == false);
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].lastMsgRcvdTime < node::NodeParams::clock.getTime());
        EXPECT_TRUE(processHeader(noOp, msg, args));
        EXPECT_TRUE(node::NodeParams::nodeStatus[sourceId-1].present == true);
        EXPECT_TRUE(fabs(node::NodeParams::nodeStatus[sourceId-1].lastMsgRcvdTime - node::NodeParams::clock.getTime()) < 0.1);
        EXPECT_TRUE(node::NodeParams::cmdHistory.find(cmdHeader.cmdCounter) == true);

        // Test for stale command counter check
        EXPECT_FALSE(processHeader(noOp, msg, args));

    }

}
