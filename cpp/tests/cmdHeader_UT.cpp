#include "tests/cmdHeader_UT.hpp"
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
    CmdHeader_UT::CmdHeader_UT()
    {
        node::NodeParams::loadParams("nodeConfig.json");   
        std::unordered_map<uint8_t, comm::HeaderType> nodeCmdDict = NodeCmds::getCmdDict();
        Cmds::updateCmdDict(nodeCmdDict);
    }

    void CmdHeader_UT::SetUpTestCase(void) {
    }
    
    void CmdHeader_UT::SetUp(void)
    {
    }

    TEST_F(CmdHeader_UT, cmdHeaderConstructors) {
        // Test all constructors
        CmdHeader header;
        EXPECT_TRUE(header.type == NO_HEADER);

        uint8_t cmdId = 100;
        header = CmdHeader(cmdId);
        EXPECT_TRUE(header.type == MINIMAL_HEADER);
        EXPECT_TRUE(header.cmdId == cmdId);

        uint8_t sourceId = 2;
        header = CmdHeader(cmdId, sourceId);
        EXPECT_TRUE(header.type == SOURCE_HEADER);
        EXPECT_TRUE(header.cmdId == cmdId);
        EXPECT_TRUE(header.sourceId == sourceId);

        uint16_t cmdCounter = 1600;
        header = CmdHeader(cmdId, sourceId, cmdCounter);
        EXPECT_TRUE(header.type == NODE_HEADER);
        EXPECT_TRUE(header.cmdId == cmdId);
        EXPECT_TRUE(header.sourceId == sourceId);
        EXPECT_TRUE(header.cmdCounter == cmdCounter);
    }

    TEST_F(CmdHeader_UT, packHeader) {
        CmdHeader header;
        std::vector<uint8_t> vec = header.packHeader();
        EXPECT_TRUE(vec.size() == 0);
        
        uint8_t cmdId = 100;
        header = CmdHeader(cmdId);
        vec = header.packHeader();
        EXPECT_TRUE(vec.size() == 1);
        EXPECT_TRUE(vec[0] == cmdId);

        uint8_t sourceId = 2;
        header = CmdHeader(cmdId, sourceId);
        vec = header.packHeader();
        EXPECT_TRUE(vec.size() == 2);
        EXPECT_TRUE(vec[0] == cmdId);
        EXPECT_TRUE(vec[1] == sourceId);
        
        uint16_t cmdCounter = 1600;
        header = CmdHeader(cmdId, sourceId, cmdCounter);
        vec = header.packHeader();
        EXPECT_TRUE(vec.size() == 4);
        EXPECT_TRUE(vec[0] == cmdId);
        EXPECT_TRUE(vec[1] == sourceId);
        uint16_t counterOut;
        memcpy(&counterOut, vec.data() + 2, 2);
        EXPECT_TRUE(counterOut == cmdCounter);
    }

    TEST_F(CmdHeader_UT, unpackHeader) {
        CmdHeader headerIn;
        CmdHeader headerOut;
        uint8_t cmdId = 100;
        uint8_t sourceId = 2;
        uint16_t cmdCounter = 1600;
        std::vector<uint8_t> packed = headerIn.packHeader();

        // Check for proper handling of zero length input
        EXPECT_TRUE(unpackHeader(packed, HEADER_UNKNOWN, headerOut) == 0); 

        // Check for parsing of each header type
        headerIn = CmdHeader(cmdId);
        packed = headerIn.packHeader();
        EXPECT_TRUE(unpackHeader(packed, MINIMAL_HEADER, headerOut) == 1); 
        EXPECT_TRUE(headerOut.cmdId == cmdId);       
 
        headerIn = CmdHeader(cmdId, sourceId);
        packed = headerIn.packHeader();
        EXPECT_TRUE(unpackHeader(packed, SOURCE_HEADER, headerOut) == 2); 
        EXPECT_TRUE(headerOut.cmdId == cmdId);       
        EXPECT_TRUE(headerOut.sourceId == sourceId);       
        
        headerIn = CmdHeader(cmdId, sourceId, cmdCounter);
        packed = headerIn.packHeader();
        EXPECT_TRUE(unpackHeader(packed, NODE_HEADER, headerOut) == 4); 
        EXPECT_TRUE(headerOut.cmdId == cmdId);       
        EXPECT_TRUE(headerOut.sourceId == sourceId);       
        EXPECT_TRUE(headerOut.cmdCounter == cmdCounter);       
        
        // Check header type detection
        EXPECT_TRUE(unpackHeader(packed, HEADER_UNKNOWN, headerOut) == 0); // with unknown cmdId
        headerIn = CmdHeader(NodeCmds::NoOp, sourceId, cmdCounter);
        packed = headerIn.packHeader();
        EXPECT_TRUE(unpackHeader(packed, HEADER_UNKNOWN, headerOut) == 4); 
        EXPECT_TRUE(headerOut.cmdId == NodeCmds::NoOp);       
        EXPECT_TRUE(headerOut.sourceId == sourceId);       
        EXPECT_TRUE(headerOut.cmdCounter == cmdCounter);       
        
    }

    TEST_F(CmdHeader_UT, createHeader) {
        uint8_t cmdId = 163;
        uint8_t sourceId = 2;
        uint16_t cmdCounter = 1600;
        
        // Test with all inputs provided
        CmdHeader headerIn = CmdHeader(cmdId);
        std::vector<uint8_t> packed = headerIn.packHeader();
        CmdHeader headerOut = createHeader(NO_HEADER, packed);
        EXPECT_TRUE(headerOut.type == NO_HEADER); 
    
        headerIn = CmdHeader(cmdId);
        packed = headerIn.packHeader();
        headerOut = createHeader(MINIMAL_HEADER, packed);
        EXPECT_TRUE(headerOut.type == MINIMAL_HEADER); 
        EXPECT_TRUE(headerOut.cmdId == cmdId); 

        headerIn = CmdHeader(cmdId, sourceId);
        packed = headerIn.packHeader();
        headerOut = createHeader(SOURCE_HEADER, packed);
        EXPECT_TRUE(headerOut.type == SOURCE_HEADER); 
        EXPECT_TRUE(headerOut.cmdId == cmdId); 
        EXPECT_TRUE(headerOut.sourceId == sourceId); 
        
        headerIn = CmdHeader(cmdId, sourceId, cmdCounter);
        packed = headerIn.packHeader();
        headerOut = createHeader(NODE_HEADER, packed);
        EXPECT_TRUE(headerOut.type == NODE_HEADER); 
        EXPECT_TRUE(headerOut.cmdId == cmdId); 
        EXPECT_TRUE(headerOut.sourceId == sourceId); 
        EXPECT_TRUE(headerOut.cmdCounter == cmdCounter);

        // Test header type detection
        headerIn = CmdHeader(cmdId, sourceId, cmdCounter); // unknown cmdId
        packed = headerIn.packHeader();
        headerOut = createHeader(cmdId, packed);
        EXPECT_TRUE(headerOut.type == NO_HEADER);
        
        headerIn = CmdHeader(NodeCmds::NoOp, sourceId, cmdCounter); // known cmdId
        packed = headerIn.packHeader();
        headerOut = createHeader(NodeCmds::NoOp, packed);
        EXPECT_TRUE(headerOut.type == NODE_HEADER); 
        EXPECT_TRUE(headerOut.cmdId == NodeCmds::NoOp); 
        EXPECT_TRUE(headerOut.sourceId == sourceId); 
        EXPECT_TRUE(headerOut.cmdCounter == cmdCounter);
        
        // Test with individual inputs
        headerOut = createHeader(NodeCmds::GCSCmd, sourceId, cmdCounter);
        EXPECT_TRUE(headerOut.type == NODE_HEADER); 
        EXPECT_TRUE(headerOut.cmdId == NodeCmds::GCSCmd); 
        EXPECT_TRUE(headerOut.sourceId == sourceId); 
        EXPECT_TRUE(headerOut.cmdCounter == cmdCounter);

    }

}
