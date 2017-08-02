#include "comm/commandUtils.hpp"
#include "comm/commands.hpp"
#include "comm/tdmaCmds.hpp"
#include <algorithm>

using std::vector;
using std::unique_ptr;
using node::NodeParams;

namespace comm {

    unique_ptr<Command> deserialize(vector<uint8_t> & msg, uint8_t cmdId) {
        unique_ptr<Command> retCmd(new Command());

        // Switch on command type to deserialize
        switch (cmdId) {
            case TDMACmds::MeshStatus:
                retCmd = unique_ptr<Command>(new TDMA_MeshStatus(msg));
                break;

            default:
                break;
        }

        return retCmd;

    }


    bool checkCmdCounter(Command & cmd, vector<uint8_t> & msg, vector< vector<uint8_t> > * relayBuffer) {
        if (NodeParams::cmdHistory.find(cmd.header.cmdCounter) == false) { // counter value not found
            // Add new counter value to history
            NodeParams::cmdHistory.push(cmd.header.cmdCounter);

            // Add command to buffer if to be relayed
            if (std::find(Cmds::cmdsToRelay.begin(), Cmds::cmdsToRelay.end(), cmd.header.cmdId) != Cmds::cmdsToRelay.end()) {
                relayBuffer->push_back(msg);
            }

            return true;
        }
        else { // old command
            return false;
        }
    }

    /*CmdHeader parseHeader(vector<uint8_t> & msg, uint8_t cmdId, CmdHeader & retHeader) {
        if (Cmds::cmdDict.find(cmdId) != Cmds::cmdDict.end()) { // cmd id found
            return unpackHeader(msg, Cmds::cmdDict[cmdId], retHeader);
        }

        return 0;

    }*/
    
    void updateNodeMsgRcvdStatus(CmdHeader & header) {
        if (std::find(Cmds::cmdsToRelay.begin(), Cmds::cmdsToRelay.end(), header.cmdId) == Cmds::cmdsToRelay.end()) { // relayed commands will have sourceId of original sender, so ignore
            unsigned int source = header.sourceId;
            
            if (NodeParams::nodeStatus[source].present == false) {
                NodeParams::nodeStatus[source].present = true; // first message received from this node
            }

            NodeParams::nodeStatus[source].lastMsgRcvdTime = NodeParams::clock.getTime();
        }
    }
}
