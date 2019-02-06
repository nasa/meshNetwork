#include "tests/nodeMsgProcessor_UT.hpp"
#include "comm/nodeCmds.hpp"
#include "comm/cmdHeader.hpp"
#include "comm/commands.hpp"
#include "node/nodeParams.hpp"
#include <gtest/gtest.h>
#include <unistd.h>

using std::vector;

namespace {

}

namespace comm
{
    NodeMsgProcessor_UT::NodeMsgProcessor_UT() 
    {
        // Load configuration
        node::NodeParams::loadParams("nodeConfig.json");

        // Populate message processor args
        m_args.cmdQueue = &m_cmdQueue;
        m_args.relayBuffer = &m_relayBuffer;

        // Load command dictionary for use
        std::unordered_map<uint8_t, comm::HeaderType> nodeCmdDict = NodeCmds::getCmdDict();
        Cmds::updateCmdDict(nodeCmdDict);
        
    }

    void NodeMsgProcessor_UT::SetUpTestCase(void) {
    }
    
    void NodeMsgProcessor_UT::SetUp(void)
    {
    }

    TEST_F(NodeMsgProcessor_UT, processMsg) {
        // Test all commands processed by NodeMsgProcessor
        std::vector<uint8_t> header;
        std::vector<uint8_t> msgBytes;
        
        // NodeCmds:NoOp
        CmdHeader cmdHeader = createHeader(NodeCmds::NoOp, 1);
        Node_NoOp noOp(cmdHeader);
        msgBytes = noOp.serialize(); 
        EXPECT_TRUE(m_nodeMsgProcessor.processMsg(NodeCmds::NoOp, msgBytes, m_args));

        // NodeCmds::GCSCmd
        cmdHeader = createHeader(NodeCmds::GCSCmd, 1, node::NodeParams::getCmdCounter());
        Node_GCSCmd gcsCmd(node::NodeParams::config.nodeId, 0, cmdHeader);
        msgBytes = gcsCmd.serialize(); 
        EXPECT_TRUE(m_nodeMsgProcessor.processMsg(NodeCmds::GCSCmd, msgBytes, m_args));

        // NodeCmds::ParamUpdate
        uint16_t paramVal = 500;
        std::vector<uint8_t> paramValue(2);
        std::memcpy(paramValue.data(), &paramVal, 2);
        cmdHeader = createHeader(NodeCmds::ParamUpdate, 1, node::NodeParams::getCmdCounter());
        Node_ParamUpdate paramUpdate(node::NodeParams::config.nodeId, node::PARAMID_PARSE_MSG_MAX, 2, paramValue, cmdHeader);
        msgBytes = paramUpdate.serialize(); 
        EXPECT_FALSE(node::NodeParams::config.parseMsgMax == paramVal); // original value of parameter is different
        EXPECT_TRUE(m_nodeMsgProcessor.processMsg(NodeCmds::ParamUpdate, msgBytes, m_args)); // command successfully processed
        EXPECT_TRUE(node::NodeParams::config.parseMsgMax == paramVal); // parameter value updated to expected value

        // NodeCmds::ConfigRequest
        cmdHeader = createHeader(NodeCmds::ConfigRequest, 1, node::NodeParams::getCmdCounter());
        std::vector<uint8_t> configHash = node::NodeParams::config.calculateHash();
        Node_ConfigRequest configRequest(configHash, cmdHeader);
        msgBytes = configRequest.serialize(); 
        EXPECT_TRUE(m_nodeMsgProcessor.processMsg(NodeCmds::ConfigRequest, msgBytes, m_args)); // command successfully processed
        EXPECT_TRUE(m_cmdQueue.find(NodeCmds::ConfigRequest) != m_cmdQueue.end());

    }

    TEST_F(NodeMsgProcessor_UT, malformedCmd) {
        // Send an invalid command (correct header, missing body)
        CmdHeader cmdHeader = createHeader(NodeCmds::GCSCmd, 1, node::NodeParams::getCmdCounter());
        std::vector<uint8_t> msgBytes = cmdHeader.packHeader();
        EXPECT_FALSE(m_nodeMsgProcessor.processMsg(NodeCmds::GCSCmd, msgBytes, m_args));


    }
}
