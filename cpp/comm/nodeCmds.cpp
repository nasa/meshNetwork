#include "comm/nodeCmds.hpp"
#include "comm/commands.hpp"
#include <iostream>      
#include <cstring>
#include <algorithm> 

using std::vector;
using node::NodeParams;

namespace comm {      

    namespace NodeCmds {
        
    std::vector<uint8_t> cmds = {NodeCmds::NoOp, NodeCmds::GCSCmd, NodeCmds::ConfigRequest, NodeCmds::ParamUpdate};
    
    std::unordered_map<uint8_t, comm::HeaderType> cmdDict = {{NodeCmds::NoOp, comm::NODE_HEADER}, {NodeCmds::GCSCmd, comm::NODE_HEADER}, {NodeCmds::ConfigRequest, comm::NODE_HEADER}, {NodeCmds::ParamUpdate, comm::NODE_HEADER}};

    std::unordered_map<uint8_t, comm::HeaderType> getCmdDict() {
        //loadCmds();
        return cmdDict;
    }
    
    std::vector<uint8_t> getCmds() {
        //loadCmds();
        return cmds;
    }
        
}
    Node_NoOp::Node_NoOp(CmdHeader headerIn, double txIntervalIn) :
        Command(NodeCmds::NoOp, headerIn, txIntervalIn)
    {
    }

    Node_NoOp::Node_NoOp(vector<uint8_t> & msg) :
        Command(NodeCmds::NoOp)
    {
        if (Node_NoOp::isValid(msg) == false) {
            return;
        }     
        
        // Header only command
        unpackHeader(msg, Cmds::cmdDict[NodeCmds::NoOp], header);
    
        valid = true;
    }
    
    bool Node_NoOp::isValid(vector<uint8_t> & msg) {
        if (msg.size() != headerSize(Cmds::cmdDict[NodeCmds::NoOp])) {
            return false;
        }
        else {
            return true;
        }
    }

    vector<uint8_t> Node_NoOp::packBody() {
        return vector<uint8_t>();
        
    } 
        
    Node_GCSCmd::Node_GCSCmd(uint8_t destIdIn, uint8_t modeIn, CmdHeader headerIn, double txIntervalIn) :
        Command(NodeCmds::GCSCmd, headerIn, txIntervalIn),
        destId(destIdIn),
        mode(modeIn)
    {
    }

    Node_GCSCmd::Node_GCSCmd(vector<uint8_t> & msg) :
        Command(NodeCmds::GCSCmd)
    {
        if (Node_GCSCmd::isValid(msg) == false) {
            valid = false;
            return;
        }     

        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[NodeCmds::GCSCmd], header);

        // Parse body
        std::copy(&msg[msgPos], &msg[msgPos] + sizeof(destId), &destId);
        msgPos += sizeof(destId);
        std::copy(&msg[msgPos], &msg[msgPos] + sizeof(mode), &mode);
    
        valid = true;
    }

    bool Node_GCSCmd::isValid(vector<uint8_t> & msg) {
        if (msg.size() != (headerSize(Cmds::cmdDict[NodeCmds::GCSCmd]) + sizeof(destId) + sizeof(mode))) {
            return false;
        }
        else {
            return true;
        }
    }

    vector<uint8_t> Node_GCSCmd::packBody() {
        vector<uint8_t> packed;
        
        packData(&destId, sizeof(destId), packed);
        packData(&mode, sizeof(mode), packed);
        
        return packed;
    } 
        
    Node_ConfigRequest::Node_ConfigRequest(vector<uint8_t> & configHashIn, CmdHeader headerIn, double txIntervalIn) :
        Command(NodeCmds::ConfigRequest, headerIn, txIntervalIn),
        configHash(configHashIn)
    {
    }

    Node_ConfigRequest::Node_ConfigRequest(vector<uint8_t> & msg) :
        Command(NodeCmds::ConfigRequest)
    {
        if (Node_ConfigRequest::isValid(msg) == false) {
            return;
        }

        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[NodeCmds::ConfigRequest], header);
        // Parse body
        configHash.resize(NodeParams::config.hashSize);
        std::memcpy(configHash.data(), msg.data() + msgPos, NodeParams::config.hashSize);

        valid = true;
    }
    
    bool Node_ConfigRequest::isValid(vector<uint8_t> & msg) {
        if (msg.size() == headerSize(Cmds::cmdDict[NodeCmds::ConfigRequest]) + NodeParams::config.hashSize) { // check for sufficient data
            return true;
        }
        else {
            return false;
        }
    }

    vector<uint8_t> Node_ConfigRequest::packBody() {
        vector<uint8_t> packed;
       
        packData(configHash.data(), configHash.size(), packed);

        return packed;
    } 
        
    Node_ParamUpdate::Node_ParamUpdate(uint8_t destIdIn, uint8_t paramIdIn, uint8_t dataLengthIn, std::vector<uint8_t> & paramValueIn, CmdHeader headerIn, double txIntervalIn) :
        Command(NodeCmds::ParamUpdate, headerIn, txIntervalIn),
        destId(destIdIn),
        paramId(paramIdIn),
        dataLength(dataLengthIn),
        paramValue(paramValueIn)
    {
    }

    Node_ParamUpdate::Node_ParamUpdate(vector<uint8_t> & msg) :
        Command(NodeCmds::ParamUpdate)
    {
        // Parse header
        uint8_t msgPos = unpackHeader(msg, Cmds::cmdDict[NodeCmds::ParamUpdate], header);
        
        // Parse body
        std::memcpy(&destId, msg.data() + msgPos, 1);
        msgPos += 1;
        std::memcpy(&paramId, msg.data() + msgPos, 1);
        msgPos += 1;
        std::memcpy(&dataLength, msg.data() + msgPos, 1);
        msgPos += 1;
        paramValue.resize(dataLength);
        if (msg.size() == unsigned(msgPos + dataLength + 1)) { // correct data bytes not present
            return;
        }
        std::memcpy(paramValue.data(), msg.data() + msgPos, dataLength);
        
        valid = true;
    
    }
    
    bool Node_ParamUpdate::isValid(vector<uint8_t> & msg) {
        if (msg.size() > headerSize(Cmds::cmdDict[NodeCmds::ParamUpdate]) + sizeof(destId) + sizeof(paramId) + sizeof(dataLength)) { // check for sufficient data
            return true;
        }
        else {
            return false;
        } 

    }

    vector<uint8_t> Node_ParamUpdate::packBody() {
        vector<uint8_t> packed;
       
        packData(&destId, 1, packed);
        packData(&paramId, 1, packed);
        packData(&dataLength, 1, packed);
        packData(paramValue.data(), dataLength, packed);

        return packed;
    } 
        
}
