#include "node/nodeCmds.hpp"
#include "comm/commands.hpp"
#include <iostream>      
#include <cstring>

using std::vector;
using comm::Command;
using comm::CmdHeader;

namespace node {      
    // Node Commands
    std::vector<uint8_t> NodeCmds::cmds = {NodeCmds::GCSCmd, NodeCmds::FormationCmd,
        NodeCmds::ParamUpdate, NodeCmds::ConfigRequest, NodeCmds::ConfigHash};

    std::unordered_map<uint8_t, comm::HeaderType> NodeCmds::cmdDict = {};
    
    Node_GCSCmd::Node_GCSCmd(FormationMode modeIn, comm::CmdHeader headerIn, double txIntervalIn) :
        Command(NodeCmds::GCSCmd, headerIn, txIntervalIn),
        mode(modeIn)
    {} 
    
    Node_GCSCmd::Node_GCSCmd(vector<uint8_t> & msg) :
        Command(NodeCmds::GCSCmd)
    {}

    vector<uint8_t> Node_GCSCmd::serialize() {
        vector<uint8_t> packed;
        return packed;
    }
    
    Node_ParamUpdate::Node_ParamUpdate(ParamName nameIn, vector<uint8_t> valueIn, comm::CmdHeader headerIn, double txIntervalIn) :
        Command(NodeCmds::ParamUpdate, headerIn, txIntervalIn),
        name(nameIn),
        value(valueIn)
    {} 
    
    Node_ParamUpdate::Node_ParamUpdate(vector<uint8_t> & msg) :
        Command(NodeCmds::ParamUpdate)
    {}

    vector<uint8_t> Node_ParamUpdate::serialize() {
        vector<uint8_t> packed;
        return packed;
    }
            
    Node_ConfigRequest::Node_ConfigRequest(std::string hashIn, comm::CmdHeader headerIn, double txIntervalIn) :
        Command(NodeCmds::ConfigRequest, headerIn, txIntervalIn),
        hash(hashIn)
    {} 
    
    Node_ConfigRequest::Node_ConfigRequest(vector<uint8_t> & msg) :
        Command(NodeCmds::ConfigRequest)
    {}

    vector<uint8_t> Node_ConfigRequest::serialize() {
        vector<uint8_t> packed;
        return packed;
    }

}
