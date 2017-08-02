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
    
    void TDMAMsgProcessor::processMsg(uint8_t cmdId, vector<uint8_t> & msg, MsgProcessorArgs & args) {
        // Parse command
        //unique_ptr<Command> cmd = deserialize(msg, cmdId);
        Command cmd(msg);

        // Update node message received status
        if (cmd.header.type != NO_HEADER && cmd.header.type != HEADER_UNKNOWN) {
            updateNodeMsgRcvdStatus(cmd.header);
        }

        // Check command counter
        if (cmd.header.type == NODE_HEADER) {
            bool newCmd = checkCmdCounter(cmd, msg, args.relayBuffer);
            if (newCmd == false) { // old command counter value
                return;
            }
        }            

        // Process message by command id
        switch (cmdId) {
            case TDMACmds::TimeOffset:
                {
                    TDMA_TimeOffset timeOffset = TDMA_TimeOffset(msg);
                    if (NodeParams::nodeStatus.size() >= cmd.header.sourceId) {
                        NodeParams::nodeStatus[cmd.header.sourceId-1].timeOffset = timeOffset.timeOffset;
                    }

                    break;
                }

            case TDMACmds::TimeOffsetSummary:
                {
                    TDMA_TimeOffsetSummary timeOffset = TDMA_TimeOffsetSummary(msg);
                
                    break;
                }
            case TDMACmds::MeshStatus:
                {
                    std::cout << "Mesh status message received" << std::endl;
                    TDMA_MeshStatus meshStatus = TDMA_MeshStatus(msg);
                    NodeParams::commStartTime = meshStatus.commStartTimeSec;
                    std::cout << "commStartTime: " << NodeParams::commStartTime << std::endl; 
                    break;
                }
           
            case TDMACmds::LinkStatus:
                {
                    TDMA_LinkStatus linkStatus = TDMA_LinkStatus(msg);
                    
                    // Sending node
                    uint8_t node = linkStatus.header.sourceId;

                    // Store received status
                    NodeParams::linkStatus[node] = linkStatus.linkStatus;
                       
                    break;
                } 
 
            default:
                std::cout << "Invalid message type" << std::endl;
                break;
        }
              
    };
}    
