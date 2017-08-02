#include "comm/tdmaCmds.hpp"
#include "comm/commands.hpp"
#include <iostream>      
#include <cstring>

using std::vector;
using node::NodeParams;

namespace comm {      

    namespace TDMACmds {
        
    std::vector<uint8_t> cmds = {TDMACmds::MeshStatus, TDMACmds::LinkStatus, TDMACmds::LinkStatusSummary, TDMACmds::TimeOffset, TDMACmds::TimeOffsetSummary, TDMACmds::BlockTxRequest, TDMACmds:: BlockTxRequestResponse, TDMACmds::BlockTxConfirmed, TDMACmds::BlockTxStatus, TDMACmds::BlockData};
    
    std::unordered_map<uint8_t, comm::HeaderType> cmdDict = {{TDMACmds::MeshStatus, comm::MINIMAL_HEADER}, {TDMACmds::LinkStatus, comm::SOURCE_HEADER}, {TDMACmds::LinkStatusSummary, comm::MINIMAL_HEADER}};

    std::unordered_map<uint8_t, comm::HeaderType> getCmdDict() {
        //loadCmds();
        return cmdDict;
    }
    
    std::vector<uint8_t> getCmds() {
        //loadCmds();
        return cmds;
    }
        
}
    TDMA_MeshStatus::TDMA_MeshStatus(unsigned int commStartTimeSecIn, unsigned int statusIn, CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::MeshStatus, headerIn, txIntervalIn)
    {
        commStartTimeSec = (uint32_t)commStartTimeSecIn;
        status = (uint8_t)statusIn;
    }

    TDMA_MeshStatus::TDMA_MeshStatus(vector<uint8_t> & msg) :
        Command(TDMACmds::MeshStatus)
    {
        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::MeshStatus], header);
        // Parse body
        memcpy(&commStartTimeSec, msg.data() + msgPos, sizeof(commStartTimeSec));
        msgPos += sizeof(commStartTimeSec);
        memcpy(&status, msg.data() + msgPos, sizeof(status));
    
    }

    vector<uint8_t> TDMA_MeshStatus::serialize() {
        //uint8_t buf[sizeof(c)];
        //memcpy(&c, buf, sizeof(c));
        vector<uint8_t> packed;
        packData(&commStartTimeSec, sizeof(commStartTimeSec), packed);
        packData(&status, sizeof(status), packed);
        
        //cmd.insert(cmd.end(), buf, buf + sizeof(buf));
        //return cmd;
        return packed;
    } 
        

    TDMA_TimeOffset::TDMA_TimeOffset(double offsetIn, CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::TimeOffset, headerIn, txIntervalIn),
        timeOffset(offsetIn)
    {
    }

    TDMA_TimeOffset::TDMA_TimeOffset(vector<uint8_t> & msg) :
        Command(TDMACmds::TimeOffset) 
    {
        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::TimeOffset], header);
        // Parse body
        uint16_t offset;
        memcpy(&offset, msg.data() + msgPos, sizeof(offset));
        timeOffset = offset / 100.0;
    }

    vector<uint8_t> TDMA_TimeOffset::serialize() {
        uint16_t offset = timeOffset*100;
        return packData(&offset, sizeof(offset));
    }

    TDMA_TimeOffsetSummary::TDMA_TimeOffsetSummary() :
        Command(TDMACmds::TimeOffsetSummary)
    {
        // Get offsets from NodeParams
        for (unsigned int i = 0; i < NodeParams::nodeStatus.size(); i++) {
            timeOffset.push_back(NodeParams::nodeStatus[i].timeOffset);
        }
    }
    
    TDMA_TimeOffsetSummary::TDMA_TimeOffsetSummary(vector<double> & offsets) :
        Command(TDMACmds::TimeOffsetSummary)
    {
        for (unsigned int i = 0; i < offsets.size(); i++) {
            timeOffset.push_back(offsets[i]);
        }
    }

    TDMA_TimeOffsetSummary::TDMA_TimeOffsetSummary(vector<uint8_t> & msg) {
        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::TimeOffsetSummary], header);
        // Parse body
        uint8_t numEntries;
        memcpy(&numEntries, msg.data() + msgPos, sizeof(numEntries));
        uint16_t offset;
        for (unsigned int i = 0; i < numEntries; i++) {
            memcpy(&offset, msg.data() + msgPos, sizeof(offset));
            timeOffset.push_back(offset / 100.0);
        }
    }
        
    vector<uint8_t> TDMA_TimeOffsetSummary::serialize() {
        uint16_t offset;
        vector<uint8_t> packed;
        uint8_t numEntries = timeOffset.size();
        packData(&numEntries, sizeof(numEntries), packed);
        for (unsigned int i = 0; i < timeOffset.size(); i++) {
            offset = timeOffset[i]*100;
            packData(&offset, sizeof(offset), packed);
        } 
        
        return packed;
    }
        
    TDMA_LinkStatus::TDMA_LinkStatus(std::vector<uint8_t> & linkStatusIn, CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::LinkStatus, headerIn, txIntervalIn)
    {
        linkStatus = linkStatusIn;
    }

    TDMA_LinkStatus::TDMA_LinkStatus(vector<uint8_t> & msg) :
        Command(TDMACmds::LinkStatus)
    {
        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::LinkStatus], header);
        // Parse body
        if (msg.size() >= msgPos + NodeParams::config.maxNumNodes) {
            memcpy(&linkStatus, msg.data() + msgPos, NodeParams::config.maxNumNodes);
        } 
    }

    vector<uint8_t> TDMA_LinkStatus::serialize() {
        vector<uint8_t> packed;
        if (linkStatus.size() > 0) {
            packData(&linkStatus, linkStatus.size()*sizeof(linkStatus[0]), packed);
        }
        
        return packed;
    } 
        
    TDMA_LinkStatusSummary::TDMA_LinkStatusSummary(std::vector< std::vector<uint8_t> > & linkTableIn, CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::LinkStatusSummary, headerIn, txIntervalIn)
    {
        linkTable = linkTable;
    }

    TDMA_LinkStatusSummary::TDMA_LinkStatusSummary(vector<uint8_t> & msg) {
        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::LinkStatusSummary], header);
        // Parse body
        for (unsigned int i = 0; i < NodeParams::config.maxNumNodes; i++) {
            memcpy(&(linkTable[i]), msg.data() + msgPos, NodeParams::config.maxNumNodes);
            msgPos += NodeParams::config.maxNumNodes;
        }
    }
        
    vector<uint8_t> TDMA_LinkStatusSummary::serialize() {
        vector<uint8_t> packed;
        for (unsigned int i = 0; i < NodeParams::config.maxNumNodes; i++) {
            packData(&(linkTable[i]), NodeParams::config.maxNumNodes, packed);
        } 
        
        return packed;
    }
        
}
