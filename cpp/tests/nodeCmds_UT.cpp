#include "tests/nodeCmds_UT.hpp"
#include "node/nodeParams.hpp"
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
    NodeCmds_UT::NodeCmds_UT()
    {
        node::NodeParams::loadParams("nodeConfig.json");   
        std::unordered_map<uint8_t, comm::HeaderType> nodeCmdDict = NodeCmds::getCmdDict();
        Cmds::updateCmdDict(nodeCmdDict);
    }

    void NodeCmds_UT::SetUpTestCase(void) {
    }
    
    void NodeCmds_UT::SetUp(void)
    {
    }

    TEST_F(NodeCmds_UT, node_noOp) {
        uint8_t sourceId = 1;
        CmdHeader header(NodeCmds::NoOp, sourceId, node::NodeParams::getCmdCounter());

        // Test constructors
        Node_NoOp noOp = Node_NoOp(header); // all inputs provided
        EXPECT_TRUE(noOp.valid == true);
        EXPECT_TRUE(noOp.cmdId == NodeCmds::NoOp);
        EXPECT_TRUE(noOp.header.type == Cmds::cmdDict[NodeCmds::NoOp]);
        
        // Test isValid method
        std::vector<uint8_t> packedHeader = header.packHeader();
        EXPECT_TRUE(Node_NoOp::isValid(packedHeader));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(Node_NoOp::isValid(empty));
        
        // Test unpacking constructor
        noOp = Node_NoOp(packedHeader); // unpacking constructor
        EXPECT_TRUE(noOp.valid == true);
        EXPECT_TRUE(noOp.cmdId == NodeCmds::NoOp);
        EXPECT_TRUE(noOp.header.type == Cmds::cmdDict[NodeCmds::NoOp]);
        EXPECT_FALSE(Node_NoOp(empty).valid);

        // Test packBody method
        EXPECT_TRUE(noOp.packBody().size() == 0); // header only command
        
    }
    
    TEST_F(NodeCmds_UT, node_gcsCmd) {
        uint8_t sourceId = 1;
        uint8_t destId = 2;
        uint8_t mode = 3;
        CmdHeader header(NodeCmds::GCSCmd, sourceId, node::NodeParams::getCmdCounter());
        std::vector<uint8_t> packedHeader = header.packHeader();

        // Test constructor
        Node_GCSCmd gcsCmd(destId, mode, header); // all inputs provided
        EXPECT_TRUE(gcsCmd.valid == true);
        EXPECT_TRUE(gcsCmd.cmdId == NodeCmds::GCSCmd);
        EXPECT_TRUE(gcsCmd.header.type == Cmds::cmdDict[NodeCmds::GCSCmd]);
        EXPECT_TRUE(gcsCmd.destId = destId);
        EXPECT_TRUE(gcsCmd.mode = mode);
        
        // Test packBody method
        std::vector<uint8_t> packedBody = gcsCmd.packBody();
        EXPECT_TRUE(packedBody.size() == 2);        

        // Test serialize method of base Command class
        std::vector<uint8_t> packed = gcsCmd.serialize();
        EXPECT_TRUE(packed.size() == packedBody.size() + packedHeader.size());
        for(unsigned int i = 0; i < packed.size(); i++) {
            if (i < packedHeader.size()) { // compare header bytes
                EXPECT_TRUE(packed[i] == packedHeader[i]);
            }
            else { // compared body bytes
                EXPECT_TRUE(packed[i] == packedBody[i - packedHeader.size()]);
            }
        }
   
        // Test isValid function
        EXPECT_TRUE(Node_GCSCmd::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(Node_GCSCmd::isValid(empty));
        
        // Test unpacking constructor
        gcsCmd = Node_GCSCmd(packed);
        EXPECT_TRUE(gcsCmd.valid == true);
        EXPECT_TRUE(gcsCmd.cmdId == NodeCmds::GCSCmd);
        EXPECT_TRUE(gcsCmd.header.type == Cmds::cmdDict[NodeCmds::GCSCmd]);
        EXPECT_TRUE(gcsCmd.destId = destId);
        EXPECT_TRUE(gcsCmd.mode = mode);

        EXPECT_FALSE(Node_GCSCmd(empty).valid);

    }

    TEST_F(NodeCmds_UT, node_configRequest) {
        uint8_t sourceId = 1;
        std::vector<uint8_t> configHash = node::NodeParams::config.calculateHash();
        CmdHeader header = createHeader(NodeCmds::ConfigRequest, sourceId, node::NodeParams::getCmdCounter());
        std::vector<uint8_t> packedHeader = header.packHeader();

        // Test constructor
        Node_ConfigRequest configRequest(configHash, header);
        EXPECT_TRUE(configRequest.header.type == Cmds::cmdDict[NodeCmds::ConfigRequest]);
        EXPECT_TRUE(configHash.size() == configRequest.configHash.size());
        for (unsigned int i = 0; i < configHash.size(); i ++) {
            EXPECT_TRUE(configHash[i] == configRequest.configHash[i]);
        }
        
        // Test packBody method
        EXPECT_TRUE(configRequest.packBody().size() == node::NodeParams::config.hashSize);
    
        // Test isValid method
        std::vector<uint8_t> packed = configRequest.serialize();
        EXPECT_TRUE(Node_ConfigRequest::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(Node_ConfigRequest::isValid(empty));
        
        // Test unpacking constructor
        configRequest = Node_ConfigRequest(packed);
        EXPECT_TRUE(configRequest.valid == true);
        EXPECT_TRUE(configRequest.cmdId == NodeCmds::ConfigRequest);
        EXPECT_TRUE(configRequest.header.type == Cmds::cmdDict[NodeCmds::ConfigRequest]);
        EXPECT_TRUE(configHash.size() == configRequest.configHash.size());
        for (unsigned int i = 0; i < configHash.size(); i ++) {
            EXPECT_TRUE(configHash[i] == configRequest.configHash[i]);
        }

        EXPECT_FALSE(Node_ConfigRequest(empty).valid);

    }

    TEST_F(NodeCmds_UT, node_paramUpdate) {
        uint8_t sourceId = 1;
        uint8_t destId = 2;
        uint8_t paramId = node::PARAMID_PARSE_MSG_MAX;
        uint16_t paramVal = 500;
        uint8_t dataLength = 2;
        std::vector<uint8_t> paramBytes(dataLength);
        std::memcpy(paramBytes.data(), &paramVal, 2);
        CmdHeader header = createHeader(NodeCmds::ParamUpdate, sourceId, node::NodeParams::getCmdCounter());
        std::vector<uint8_t> packedHeader = header.packHeader();

        // Test constructor
        Node_ParamUpdate paramUpdate(destId, paramId, dataLength, paramBytes, header); 
        EXPECT_TRUE(paramUpdate.valid == true);
        EXPECT_TRUE(paramUpdate.cmdId == NodeCmds::ParamUpdate);
        EXPECT_TRUE(paramUpdate.destId == destId);
        EXPECT_TRUE(paramUpdate.header.type == Cmds::cmdDict[NodeCmds::ParamUpdate]);
        EXPECT_TRUE(paramUpdate.dataLength == dataLength);
        EXPECT_TRUE(paramUpdate.paramValue.size() == dataLength);
        for (unsigned int i = 0; i < paramBytes.size(); i++) {
            EXPECT_TRUE(paramBytes[i] == paramUpdate.paramValue[i]);
        }
        
        // Test packBody method
        EXPECT_TRUE(paramUpdate.packBody().size() == (unsigned)3 + paramUpdate.dataLength);

        // Test isValid method
        std::vector<uint8_t> packed = paramUpdate.serialize();
        EXPECT_TRUE(Node_ParamUpdate::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(Node_ParamUpdate::isValid(empty));

        // Test unpacking constructor
        paramUpdate = Node_ParamUpdate(packed);
        EXPECT_TRUE(paramUpdate.valid == true);
        EXPECT_TRUE(paramUpdate.cmdId == NodeCmds::ParamUpdate);
        EXPECT_TRUE(paramUpdate.destId == destId);
        EXPECT_TRUE(paramUpdate.header.type == Cmds::cmdDict[NodeCmds::ParamUpdate]);
        EXPECT_TRUE(paramUpdate.dataLength == dataLength);
        EXPECT_TRUE(paramUpdate.paramValue.size() == dataLength);
        for (unsigned int i = 0; i < paramBytes.size(); i++) {
            EXPECT_TRUE(paramBytes[i] == paramUpdate.paramValue[i]);
        }

    }

}
