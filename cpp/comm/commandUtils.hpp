#ifndef COMM_COMMAND_UTILS_HPP
#define COMM_COMMAND_UTILS_HPP

#include <vector>
#include <cstdint>
#include <memory>
#include "comm/command.hpp"
#include "comm/cmdHeader.hpp"

namespace comm {

    /**
     * Deserialize received command bytes.
     * @param msg Raw message bytes.
     * @param cmdId Command ID of message.
     */
    std::unique_ptr<Command> deserialize(std::vector<uint8_t> & msg, uint8_t cmdId);

    /**
     * Check command counter of incoming message to see if it is new and if it should be relayed.
     * @param cmd Received command.
     * @param relayBuffer Message bytes vector to place commands to be relayed.
     */
    bool checkCmdCounter(Command & cmd, std::vector<uint8_t> & msg, std::vector< std::vector<uint8_t> > * relayBuffer);

    //CmdHeader parseHeader(std::vector<uint8_t> & msg, uint8_t cmdId);

            
    /**
     * Updates status of message reception from nodes.
     * @param header Command header.
     */
    void updateNodeMsgRcvdStatus(CmdHeader & header);
}

#endif // COMM_COMMAND_UTILS_HPP
