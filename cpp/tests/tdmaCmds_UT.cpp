#include "tests/tdmaCmds_UT.hpp"
#include "node/nodeParams.hpp"
#include "comm/commands.hpp"
#include "comm/cmdHeader.hpp"
#include "comm/tdmaCmds.hpp"
#include "comm/tdmaComm.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <cmath>

using std::vector;

namespace {
    
}

namespace comm
{
    TDMACmds_UT::TDMACmds_UT()
    {
        node::NodeParams::loadParams("nodeConfig.json");   
        std::unordered_map<uint8_t, comm::HeaderType> cmdDict = TDMACmds::getCmdDict();
        Cmds::updateCmdDict(cmdDict);
    }

    void TDMACmds_UT::SetUpTestCase(void) {
    }
    
    void TDMACmds_UT::SetUp(void)
    {
    }

    TEST_F(TDMACmds_UT, tdma_meshStatus) {
        uint8_t sourceId = 1;
        uint32_t commStartTime = floor(node::NodeParams::clock.getTime());
        uint8_t tdmaStatus = TDMASTATUS_NOMINAL;        
        CmdHeader header = createHeader(TDMACmds::MeshStatus, sourceId, node::NodeParams::getCmdCounter());

        // Test constructors
        TDMA_MeshStatus cmd = TDMA_MeshStatus(commStartTime, tdmaStatus, header);
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::MeshStatus);
        EXPECT_TRUE(cmd.commStartTimeSec == commStartTime);
        EXPECT_TRUE(cmd.status == tdmaStatus);
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::MeshStatus]);
        
        // Test isValid method
        std::vector<uint8_t> packed = cmd.serialize();
        EXPECT_TRUE(TDMA_MeshStatus::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(TDMA_MeshStatus::isValid(empty));
        
        // Test unpacking constructor
        cmd = TDMA_MeshStatus(packed); // unpacking constructor
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::MeshStatus);
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::MeshStatus]);
        EXPECT_FALSE(TDMA_MeshStatus(empty).valid);

        // Test packBody method
        std::vector<uint8_t> packedBody = cmd.packBody();
        EXPECT_TRUE(packedBody.size() == sizeof(cmd.commStartTimeSec) + sizeof(cmd.status));        
        
    }
    
    TEST_F(TDMACmds_UT, tdma_linkStatus) {
        uint8_t sourceId = 1;
        std::vector<uint8_t> linkStatus;
        for (unsigned int i = 0; i < node::NodeParams::config.maxNumNodes; i++) {
            linkStatus.push_back(i+1);
        }
        CmdHeader header = createHeader(TDMACmds::LinkStatus, sourceId, node::NodeParams::getCmdCounter());

        // Test constructors
        TDMA_LinkStatus cmd = TDMA_LinkStatus(linkStatus, header);
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::LinkStatus);
        EXPECT_TRUE(cmd.linkStatus.size() == linkStatus.size());
        for (unsigned int i = 0; i < linkStatus.size(); i++) {
            EXPECT_TRUE(linkStatus[i] == cmd.linkStatus[i]);
        }
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::LinkStatus]);
        
        // Test isValid method
        std::vector<uint8_t> packed = cmd.serialize();
        EXPECT_TRUE(TDMA_LinkStatus::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(TDMA_LinkStatus::isValid(empty));
        
        // Test unpacking constructor
        cmd = TDMA_LinkStatus(packed); // unpacking constructor
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::LinkStatus);
        EXPECT_TRUE(cmd.linkStatus.size() == linkStatus.size());
        for (unsigned int i = 0; i < linkStatus.size(); i++) {
            EXPECT_TRUE(linkStatus[i] == cmd.linkStatus[i]);
        }
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::LinkStatus]);
        EXPECT_FALSE(TDMA_LinkStatus(empty).valid);

        // Test packBody method
        std::vector<uint8_t> packedBody = cmd.packBody();
        EXPECT_TRUE(packedBody.size() == cmd.linkStatus.size());        
        
    }
    
    TEST_F(TDMACmds_UT, tdma_linkStatusSummary) {
        uint8_t sourceId = 1;
        std::vector<std::vector <uint8_t> > linkStatusSummary;
        for (unsigned int i = 0; i < node::NodeParams::config.maxNumNodes; i++) {
            std::vector<uint8_t> newEntry; 
            for (unsigned int j = 0; j < node::NodeParams::config.maxNumNodes; j++) {
                newEntry.push_back(i+(j+1));
            }
            linkStatusSummary.push_back(newEntry);
        }
        CmdHeader header = createHeader(TDMACmds::LinkStatusSummary, sourceId, node::NodeParams::getCmdCounter());

        // Test constructors
        TDMA_LinkStatusSummary cmd = TDMA_LinkStatusSummary(linkStatusSummary, header);
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::LinkStatusSummary);
        EXPECT_TRUE(cmd.linkTable.size()*cmd.linkTable.size() == linkStatusSummary.size()*linkStatusSummary.size());
        for (unsigned int i = 0; i < linkStatusSummary.size(); i++) {
            EXPECT_TRUE(linkStatusSummary[i] == cmd.linkTable[i]);
        }
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::LinkStatusSummary]);
        
        // Test isValid method
        std::vector<uint8_t> packed = cmd.serialize();
        EXPECT_TRUE(TDMA_LinkStatusSummary::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(TDMA_LinkStatusSummary::isValid(empty));
        
        // Test unpacking constructor
        cmd = TDMA_LinkStatusSummary(packed); // unpacking constructor
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::LinkStatusSummary);
        EXPECT_TRUE(cmd.linkTable.size()*cmd.linkTable.size() == linkStatusSummary.size()*linkStatusSummary.size());
        for (unsigned int i = 0; i < linkStatusSummary.size(); i++) {
            EXPECT_TRUE(linkStatusSummary[i] == cmd.linkTable[i]);
        }
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::LinkStatusSummary]);
        EXPECT_FALSE(TDMA_LinkStatusSummary(empty).valid);

        // Test packBody method
        std::vector<uint8_t> packedBody = cmd.packBody();
        EXPECT_TRUE(packedBody.size() == cmd.linkTable.size()*cmd.linkTable.size());        
        
    }

    TEST_F(TDMACmds_UT, tdma_timeOffset) {
        uint8_t sourceId = 1;
        double offset = 5.0;
        CmdHeader header = createHeader(TDMACmds::TimeOffset, sourceId, node::NodeParams::getCmdCounter());

        // Test constructors
        TDMA_TimeOffset cmd = TDMA_TimeOffset(offset, header);
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::TimeOffset);
        EXPECT_TRUE(cmd.timeOffset == offset);
        
        // Test packBody method
        std::vector<uint8_t> packedBody = cmd.packBody();
        EXPECT_TRUE(packedBody.size() == sizeof(uint16_t));        
        
        // Test isValid method
        std::vector<uint8_t> packed = cmd.serialize();
        EXPECT_TRUE(TDMA_TimeOffset::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(TDMA_TimeOffset::isValid(empty));
        
        // Test unpacking constructor
        cmd = TDMA_TimeOffset(packed); // unpacking constructor
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::TimeOffset);
        EXPECT_TRUE(cmd.timeOffset == offset);
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::TimeOffset]);
        EXPECT_FALSE(TDMA_TimeOffset(empty).valid);

    }
    
    TEST_F(TDMACmds_UT, tdma_timeOffsetSummary) {
        uint8_t sourceId = 1;
        std::vector<double> offsetSummary(node::NodeParams::config.maxNumNodes);
        for (unsigned int i = 0; i < node::NodeParams::config.maxNumNodes; i++) {
            node::NodeParams::nodeStatus[i].timeOffset = i*5.0;
            offsetSummary[i] = 2*i*5.0;
        }
        CmdHeader header = createHeader(TDMACmds::TimeOffsetSummary, sourceId, node::NodeParams::getCmdCounter());

        // Test constructors
        TDMA_TimeOffsetSummary cmd = TDMA_TimeOffsetSummary(header); // offset not provided
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::TimeOffsetSummary);
        EXPECT_TRUE(cmd.timeOffset.size() == node::NodeParams::config.maxNumNodes);
        for (unsigned int i = 0; i < node::NodeParams::config.maxNumNodes; i++) {
            EXPECT_TRUE(node::NodeParams::nodeStatus[i].timeOffset == cmd.timeOffset[i]);
        }
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::TimeOffsetSummary]);
        
        cmd = TDMA_TimeOffsetSummary(offsetSummary, header); // offset provided
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::TimeOffsetSummary);
        EXPECT_TRUE(cmd.timeOffset.size() == node::NodeParams::config.maxNumNodes);
        for (unsigned int i = 0; i < node::NodeParams::config.maxNumNodes; i++) {
            EXPECT_TRUE(offsetSummary[i] == cmd.timeOffset[i]);
        }
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::TimeOffsetSummary]);
        
        // Test packBody method
        std::vector<uint8_t> packedBody = cmd.packBody();
        EXPECT_TRUE(packedBody.size() == sizeof(uint16_t) * cmd.timeOffset.size());        
        
        // Test isValid method
        std::vector<uint8_t> packed = cmd.serialize();
        EXPECT_TRUE(TDMA_TimeOffsetSummary::isValid(packed));
        std::vector<uint8_t> empty;
        EXPECT_FALSE(TDMA_TimeOffsetSummary::isValid(empty));
        
        // Test unpacking constructor
        cmd = TDMA_TimeOffsetSummary(packed); // unpacking constructor
        EXPECT_TRUE(cmd.valid == true);
        EXPECT_TRUE(cmd.cmdId == TDMACmds::TimeOffsetSummary);
        EXPECT_TRUE(cmd.timeOffset.size() == offsetSummary.size());
        for (unsigned int i = 0; i < offsetSummary.size(); i++) {
            EXPECT_TRUE(offsetSummary[i] == cmd.timeOffset[i]);
        }
        EXPECT_TRUE(cmd.header.type == Cmds::cmdDict[TDMACmds::TimeOffsetSummary]);
        EXPECT_FALSE(TDMA_TimeOffsetSummary(empty).valid);

        
    }
}
