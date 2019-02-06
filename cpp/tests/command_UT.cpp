#include "tests/command_UT.hpp"
#include "node/nodeParams.hpp"
#include "comm/command.hpp"
#include "comm/commands.hpp"
#include "comm/cmdHeader.hpp"
#include "comm/nodeCmds.hpp"
#include <gtest/gtest.h>
#include <unistd.h>

using std::vector;

namespace {
    
}

namespace comm
{
    Command_UT::Command_UT()
    {
        node::NodeParams::loadParams("nodeConfig.json");   
        std::unordered_map<uint8_t, comm::HeaderType> nodeCmdDict = NodeCmds::getCmdDict();
        Cmds::updateCmdDict(nodeCmdDict);
    }

    void Command_UT::SetUpTestCase(void) {
    }
    
    void Command_UT::SetUp(void)
    {
    }

    TEST_F(Command_UT, commandConstructors) {
        // Test all constructors
        Command cmd;
        EXPECT_TRUE(cmd.valid == false);

        cmd = Command(NodeCmds::NoOp); // cmdId only
        EXPECT_TRUE(cmd.valid == false);
        EXPECT_TRUE(cmd.cmdId == NodeCmds::NoOp);
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[NodeCmds::NoOp]); // header type parsed

        CmdHeader header(NodeCmds::NoOp, 1, node::NodeParams::getCmdCounter());
        cmd = Command(NodeCmds::NoOp, header, 1.0); // all inputs provided
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == NodeCmds::NoOp);
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[NodeCmds::NoOp]);
        EXPECT_TRUE(cmd.txInterval == 1.0);

        Command cmdIn(NodeCmds::NoOp, header, 1.0);
        std::vector<uint8_t> packed = header.packHeader(); // NoOp is header only
        cmd = Command(packed); // create from raw message bytes
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.packed.size() == packed.size());

    }

    TEST_F(Command_UT, packBody) {
        // Test proper packing of command body data
        CmdHeader header(NodeCmds::NoOp, 1, node::NodeParams::getCmdCounter());
        Command cmd(NodeCmds::NoOp, header, 1.0);

        std::vector<uint8_t> packed = cmd.packBody();
        //std::vector<uint8_t> packedHeader = header.packHeader(); 
        EXPECT_TRUE(packed.size() == 0); // base class will return nothing
        //for (unsigned int i = 0; i < packed.size(); i++) {
        //    EXPECT_TRUE(packed[i] == packedHeader[i]);
        //}
        
    }

    TEST_F(Command_UT, packData) {
        CmdHeader header(NodeCmds::NoOp, 1, node::NodeParams::getCmdCounter());
        Command cmd(NodeCmds::NoOp, header, 1.0);
        std::vector<uint8_t> dataIn = {1,2,3,4,5};

        // Return data as return value
        std::vector<uint8_t> packed;
        packed = cmd.packData(dataIn.data(), dataIn.size());
        EXPECT_TRUE(packed.size() == dataIn.size());
        for (unsigned int i = 0; i < packed.size(); i++) {
            EXPECT_TRUE(packed[i] == dataIn[i]);
        } 

        // Return data as argument
        std::vector<uint8_t> packed2;
        cmd.packData(dataIn.data(), dataIn.size(), packed2);
        EXPECT_TRUE(packed2.size() == dataIn.size());
        for (unsigned int i = 0; i < packed2.size(); i++) {
            EXPECT_TRUE(packed2[i] == dataIn[i]);
        } 

    }

}
