#include "comm/tdmaMsgProcessor.hpp"

#include <vector>
#include <iostream>
#include <memory>
#include "comm/commandUtils.hpp"
#include "comm/commands.hpp"
#include "comm/tdmaCmds.hpp"

using std::vector;    
using std::unique_ptr;
using node::NodeParams;

namespace comm {
    

    TDMAMsgProcessor::TDMAMsgProcessor() 
    {
        //TDMACmds::loadCmds();
        std::vector<uint8_t> tdmaCmds = TDMACmds::getCmds();
        cmdIds.insert(cmdIds.end(), tdmaCmds.begin(), tdmaCmds.end());
    }
    
    bool TDMAMsgProcessor::processMsg(uint8_t cmdId, vector<uint8_t> & msg, MsgProcessorArgs & args) {
        // Parse command header
        //unique_ptr<Command> cmd = deserialize(msg, cmdId);
        Command cmd(msg);
        bool cmdStatus = processHeader(cmd, msg, args);
        if (cmdStatus == false) { // stale or invalid command
            return false;
        }

        // Process message by command id
        switch (cmdId) {
            case TDMACmds::TimeOffset:
                {
                    std::unique_ptr<TDMA_TimeOffset> timeOffset(new TDMA_TimeOffset(msg));
                    cmdStatus = timeOffset->valid;
                    if (cmdStatus && NodeParams::nodeStatus.size() >= cmd.header.sourceId) {
                        NodeParams::nodeStatus[cmd.header.sourceId-1].timeOffset = timeOffset->timeOffset;
                    }

                    break;
                }

            case TDMACmds::TimeOffsetSummary:
                {
                    std::unique_ptr<TDMA_TimeOffsetSummary> timeOffset(new TDMA_TimeOffsetSummary(msg));
                    cmdStatus = timeOffset->valid;
                    if (cmdStatus) {
                        //args.cmdQueue->insert({TDMACmds::TimeOffsetSummary, std::move(timeOffset)});
                        args.cmdQueue->insert({TDMACmds::TimeOffsetSummary, msg});
                    }
                    break;
                }
            case TDMACmds::MeshStatus:
                {
                    std::cout << "Mesh status message received" << std::endl;
                    std::unique_ptr<TDMA_MeshStatus> meshStatus(new TDMA_MeshStatus(msg));
                    cmdStatus = meshStatus->valid;
                    if (cmdStatus) {
                        //args.queueMsg(TDMACmds::MeshStatus, std::move(meshStatus));
                        args.cmdQueue->insert({TDMACmds::MeshStatus, msg});
                    }
                    // TODO: UPDATE
                    //NodeParams::commStartTime = meshStatus.commStartTimeSec;
                    //std::cout << "commStartTime: " << NodeParams::commStartTime << std::endl; 
                    break;
                }
           
            case TDMACmds::LinkStatus:
                {
                    
                    std::unique_ptr<TDMA_LinkStatus> linkStatus(new TDMA_LinkStatus(msg));
                    cmdStatus = linkStatus->valid;
                    
                    // Sending node
                    uint8_t node = linkStatus->header.sourceId - 1;

                    // Store received status
                    if (cmdStatus) {
                        NodeParams::linkStatus[node] = linkStatus->linkStatus;
                    }
                       
                    break;
                } 
 
            default:
                std::cout << "Invalid message type" << std::endl;
                break;
        }

        return cmdStatus;
              
    };
}    
