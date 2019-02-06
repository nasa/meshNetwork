#include "comm/nodeMsgProcessor.hpp"

#include <vector>
#include <iostream>
#include "comm/nodeCmds.hpp"
#include "comm/commandUtils.hpp"
#include <map>
#include <string>

using std::vector; 
using node::NodeParams;   

namespace comm {
    

    NodeMsgProcessor::NodeMsgProcessor() 
    {
        cmdIds = NodeCmds::getCmds();
    }
    
    bool NodeMsgProcessor::processMsg(uint8_t cmdId, vector<uint8_t> & msg, MsgProcessorArgs & args) {
        Command cmd(msg);
        bool cmdStatus = processHeader(cmd, msg, args);
        if (cmdStatus == false) { // stale or invalid command
            return cmdStatus;
        }

        // Process message by command id
        switch (cmdId) {
            case NodeCmds::NoOp:
                {
                    cmdStatus = Node_NoOp::isValid(msg);
                    if (cmdStatus) {
                        //args.cmdQueue->insert({NodeCmds::NoOp, std::move(noOp)});
                        args.cmdQueue->insert({NodeCmds::NoOp, msg});
                    }
                    break;
                }
            case NodeCmds::GCSCmd:
                {
                    cmdStatus = Node_GCSCmd::isValid(msg);
                    if (cmdStatus) { 
                        //args.cmdQueue->insert({NodeCmds::GCSCmd, std::move(gcsCmd)});
                        args.cmdQueue->insert({NodeCmds::GCSCmd, msg});
                    }
                    break;
                }
            case NodeCmds::ParamUpdate:
                {
                    std::unique_ptr<Node_ParamUpdate> paramUpdate(new Node_ParamUpdate(msg));
                    cmdStatus = paramUpdate->valid;
                    if (cmdStatus && paramUpdate->destId == NodeParams::config.nodeId) {
                        cmdStatus = NodeParams::config.updateParameter(paramUpdate->paramId, paramUpdate->paramValue);
                    }
                    break;
                }
            case NodeCmds::ConfigRequest:
                {
                    std::unique_ptr<Node_ConfigRequest> configRequest(new Node_ConfigRequest(msg));
                    cmdStatus = configRequest->valid;
                    if (cmdStatus && configRequest->configHash.size() == NodeParams::config.hashSize) {
                        //args.cmdQueue->insert({NodeCmds::ConfigRequest, std::move(configRequest)});
                        args.cmdQueue->insert({NodeCmds::ConfigRequest, msg});
                    }
                    break; 
                }
            
        }
        
        return cmdStatus;
    }
}    
