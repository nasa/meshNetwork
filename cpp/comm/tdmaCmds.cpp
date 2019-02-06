#include "comm/tdmaCmds.hpp"
#include "comm/commands.hpp"
#include <iostream>      
#include <cstring>

using std::vector;
using node::NodeParams;

namespace comm {      

    namespace TDMACmds {
        
    std::vector<uint8_t> cmds = {TDMACmds::MeshStatus, TDMACmds::LinkStatus, TDMACmds::LinkStatusSummary, TDMACmds::TimeOffset, TDMACmds::TimeOffsetSummary, TDMACmds::BlockTxRequest, TDMACmds:: BlockTxRequestResponse, TDMACmds::BlockTxConfirmed, TDMACmds::BlockTxStatus, TDMACmds::BlockData};
    
    std::unordered_map<uint8_t, comm::HeaderType> cmdDict = {{TDMACmds::MeshStatus, comm::SOURCE_HEADER}, {TDMACmds::LinkStatus, comm::SOURCE_HEADER}, {TDMACmds::LinkStatusSummary, comm::MINIMAL_HEADER}, {TDMACmds::TimeOffset, comm::SOURCE_HEADER}, {TDMACmds::TimeOffsetSummary, comm::MINIMAL_HEADER}};

    std::unordered_map<uint8_t, comm::HeaderType> getCmdDict() {
        //loadCmds();
        return cmdDict;
    }
    
    std::vector<uint8_t> getCmds() {
        //loadCmds();
        return cmds;
    }
        
}
    TDMA_MeshStatus::TDMA_MeshStatus(uint32_t commStartTimeSecIn, uint8_t  statusIn, CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::MeshStatus, headerIn, txIntervalIn)
    {
        commStartTimeSec = (uint32_t)commStartTimeSecIn;
        status = (uint8_t)statusIn;
    }

    TDMA_MeshStatus::TDMA_MeshStatus(vector<uint8_t> & msg) :
        Command(TDMACmds::MeshStatus)
    {
        if (TDMA_MeshStatus::isValid(msg) == false) {
            return;
        }

        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::MeshStatus], header);
        // Parse body
        memcpy(&commStartTimeSec, msg.data() + msgPos, sizeof(commStartTimeSec));
        msgPos += sizeof(commStartTimeSec);
        memcpy(&status, msg.data() + msgPos, sizeof(status));
    
        valid = true;
    }
    
    bool TDMA_MeshStatus::isValid(vector<uint8_t> & msg) {
        if (msg.size() != (headerSize(Cmds::cmdDict[TDMACmds::MeshStatus]) + sizeof(commStartTimeSec) + sizeof(status))) {
            return false;
        }
        else {
            return true;
        }
    }

    vector<uint8_t> TDMA_MeshStatus::packBody() {
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
        if (TDMA_TimeOffset::isValid(msg) == false) {
            return;
        }

        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::TimeOffset], header);
        // Parse body
        uint16_t offset;
        memcpy(&offset, msg.data() + msgPos, sizeof(offset));
        timeOffset = offset / 100.0;
        
        valid = true;
    }

    bool TDMA_TimeOffset::isValid(vector<uint8_t> & msg) {
        if (msg.size() != (headerSize(Cmds::cmdDict[TDMACmds::TimeOffset]) + sizeof(uint16_t))) {
            return false;
        }
        else {
            return true;
        }
    }
    
    vector<uint8_t> TDMA_TimeOffset::packBody() {
        uint16_t offset = timeOffset*100;
        return packData(&offset, sizeof(offset));
    }

    TDMA_TimeOffsetSummary::TDMA_TimeOffsetSummary(CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::TimeOffsetSummary, headerIn, txIntervalIn)
    {
        // Get offsets from NodeParams
        for (unsigned int i = 0; i < NodeParams::nodeStatus.size(); i++) {
            timeOffset.push_back(NodeParams::nodeStatus[i].timeOffset);
        }
    }
    
    TDMA_TimeOffsetSummary::TDMA_TimeOffsetSummary(vector<double> & offsets, CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::TimeOffsetSummary, headerIn, txIntervalIn)
    {
        for (unsigned int i = 0; i < offsets.size(); i++) {
            timeOffset.push_back(offsets[i]);
        }
    }

    TDMA_TimeOffsetSummary::TDMA_TimeOffsetSummary(vector<uint8_t> & msg) :
        Command(TDMACmds::TimeOffsetSummary)
    {
        if (TDMA_TimeOffsetSummary::isValid(msg) == false) {
            return;
        }

        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::TimeOffsetSummary], header);
        // Parse body
        uint16_t offset;
        for (unsigned int i = 0; i < NodeParams::config.maxNumNodes; i++) {
            memcpy(&offset, msg.data() + msgPos, sizeof(offset));
            timeOffset.push_back(offset / 100.0);
            msgPos = msgPos + sizeof(offset);
        }
        
        valid = true;
    }
        
    bool TDMA_TimeOffsetSummary::isValid(vector<uint8_t> & msg) {
        if (msg.size() != (headerSize(Cmds::cmdDict[TDMACmds::TimeOffsetSummary]) + sizeof(uint16_t)*NodeParams::config.maxNumNodes)) {
            return false;
        }
        else {
            return true;
        }
    }
    
    vector<uint8_t> TDMA_TimeOffsetSummary::packBody() {
        uint16_t offset;
        vector<uint8_t> packed;
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
        if (TDMA_LinkStatus::isValid(msg) == false) {
            return;
        }

        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::LinkStatus], header);
        // Parse body
        linkStatus.resize(NodeParams::config.maxNumNodes);
        memcpy(linkStatus.data(), msg.data() + msgPos, NodeParams::config.maxNumNodes);
        valid = true;
    }

    bool TDMA_LinkStatus::isValid(vector<uint8_t> & msg) {
        if (msg.size() != (headerSize(Cmds::cmdDict[TDMACmds::LinkStatus]) + NodeParams::config.maxNumNodes)) {
            return false;
        }
        else {
            return true;
        }
    }
    
    vector<uint8_t> TDMA_LinkStatus::packBody() {
        vector<uint8_t> packed;
        if (linkStatus.size() > 0) {
            packData(linkStatus.data(), linkStatus.size()*sizeof(linkStatus[0]), packed);
        }
        
        return packed;
    } 
        
    TDMA_LinkStatusSummary::TDMA_LinkStatusSummary(std::vector< std::vector<uint8_t> > & linkTableIn, CmdHeader headerIn, double txIntervalIn) :
        Command(TDMACmds::LinkStatusSummary, headerIn, txIntervalIn)
    {
        linkTable = linkTableIn;
    }

    TDMA_LinkStatusSummary::TDMA_LinkStatusSummary(vector<uint8_t> & msg) :
        Command(TDMACmds::LinkStatusSummary)
    {
        if (TDMA_LinkStatusSummary::isValid(msg) == false) {
            return;
        }

        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[TDMACmds::LinkStatusSummary], header);
        // Parse body
        linkTable.resize(NodeParams::config.maxNumNodes);
        for (unsigned int i = 0; i < NodeParams::config.maxNumNodes; i++) {
            linkTable[i].resize(NodeParams::config.maxNumNodes);
            memcpy(linkTable[i].data(), msg.data() + msgPos, NodeParams::config.maxNumNodes);
            msgPos += NodeParams::config.maxNumNodes;
        }
        
        valid = true;
    }
        
    bool TDMA_LinkStatusSummary::isValid(vector<uint8_t> & msg) {
        if (msg.size() != (headerSize(Cmds::cmdDict[TDMACmds::LinkStatusSummary]) + NodeParams::config.maxNumNodes*NodeParams::config.maxNumNodes)) {
            return false;
        }
        else {
            return true;
        }
    }
    
    vector<uint8_t> TDMA_LinkStatusSummary::packBody() {
        vector<uint8_t> packed;
        for (unsigned int i = 0; i < NodeParams::config.maxNumNodes; i++) {
            packData(linkTable[i].data(), NodeParams::config.maxNumNodes, packed);
        } 
        
        return packed;
    }
        
}
