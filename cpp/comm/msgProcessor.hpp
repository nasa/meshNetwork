#ifndef COMM_MSG_PROCESSOR_HPP
#define COMM_MSG_PROCESSOR_HPP

#include <vector>
#include <unordered_map>
#include <cstdint>
#include <memory>
#include "comm/command.hpp"
#include "comm/commands.hpp"

namespace comm {

    struct MsgProcessorArgs { // arguments available to message processors
        /**
         * Command queue for storing processed commands.
         */
        //std::unordered_map<uint8_t, Command> * cmdQueue;
        std::unordered_map<uint8_t, std::unique_ptr<Command>> * cmdQueue;

        /**
         * Relay buffer for commands to be relayed between nodes.
         */
        std::vector< std::vector<uint8_t> > * relayBuffer;

        /**
         * Default constructor
         */
        MsgProcessorArgs() {};

        /**
         Constructor
         @param cmdQueueIn Command queue pointer.
         @param relayBufferIn Relay buffer pointer.
         */
        //MsgProcessorArgs(std::unordered_map<uint8_t, Command> * cmdQueueIn, std::vector< std::vector<uint8_t> > * relayBufferIn) : 
        MsgProcessorArgs(std::unordered_map<uint8_t, std::unique_ptr<Command>> * cmdQueueIn, std::vector< std::vector<uint8_t> > * relayBufferIn) : 
            cmdQueue(cmdQueueIn),
            relayBuffer(relayBufferIn) {};

    };

    class MsgProcessor {

        public:

            /**
             * Vector of command IDs that should be processed by this processor.
             */
            std::vector<uint8_t> cmdIds;

            /**
             * Processes received message bytes.
             * @param cmdId Command ID of received command bytes.
             * @param msg Raw command message bytes.
             * @param args Arguments to be used to process command.
             */
            virtual void processMsg(uint8_t cmdId, std::vector<uint8_t> & msg, MsgProcessorArgs & args) {};

    };

}
#endif // COMM_MSG_PROCESSOR_HPP
