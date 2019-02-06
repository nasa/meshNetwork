#ifndef COMM_MSG_PROCESSOR_HPP
#define COMM_MSG_PROCESSOR_HPP

#include <vector>
#include <unordered_map>
#include <cstdint>
#include <memory>
#include "comm/command.hpp"
#include "comm/commands.hpp"

namespace comm {

    class MsgProcessorArgs { // arguments available to message processors
        public:

        /**
         * Command queue for storing processed commands.
         */
        //std::unordered_map<uint8_t, Command> * cmdQueue;
        //std::unordered_map<uint8_t, std::unique_ptr<Command> > * cmdQueue;
        std::unordered_map<uint8_t, std::vector<uint8_t> > * cmdQueue;

        /**
         * Relay buffer for commands to be relayed between nodes.
         */
        std::vector<uint8_t> * relayBuffer;

        /**
         * Default constructor
         */
        MsgProcessorArgs() {};

        /**
         Constructor
         @param cmdQueueIn Command queue pointer.
         @param relayBufferIn Relay buffer pointer.
         */
        MsgProcessorArgs(std::unordered_map<uint8_t, std::vector<uint8_t> > * cmdQueueIn, std::vector<uint8_t> * relayBufferIn) : 
        //MsgProcessorArgs(std::unordered_map<uint8_t, std::unique_ptr<Command>> * cmdQueueIn, std::vector<uint8_t> * relayBufferIn) : 
            cmdQueue(cmdQueueIn),
            relayBuffer(relayBufferIn) {};
        
        MsgProcessorArgs(std::vector<uint8_t> * relayBufferIn) :
            relayBuffer(relayBufferIn) {};
        
            
            /**bool queueMsg(uint8_t cmdId, std::unique_ptr<Command> cmdMsg) {
                 if (cmdQueue != NULL) {
                    cmdQueue->insert({cmdId, std::move(cmdMsg)});
                    return true;
                }

                return false;
            }**/
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
             * @return Returns true if message successfully processed.
             */
            virtual bool processMsg(uint8_t cmdId, std::vector<uint8_t> & msg, MsgProcessorArgs & args) {return false;};


    };

}
#endif // COMM_MSG_PROCESSOR_HPP
