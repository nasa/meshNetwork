#ifndef COMM_COMM_PROCESSOR_HPP
#define COMM_COMM_PROCESSOR_HPP

#include "comm/command.hpp"
#include "comm/commands.hpp"
#include "comm/msgProcessor.hpp"
#include <unordered_map>
#include <memory>
#include <vector>
#include <string>


namespace comm {

    class CommProcessor {

        public:
            /**
             * Command queue.
             */
            //std::unordered_map<uint8_t, Command> cmdQueue;
            std::unordered_map<uint8_t, std::unique_ptr<Command>> cmdQueue;

            /**
             * Message processors.
             */
            std::vector<MsgProcessor *> msgProcessors;

            /**
             * Default constructor.
             */
            CommProcessor() {};

            /**
             * This constructor takes message processors.
             * @param msgProcessorsIn Vector of message processors.
             */
            CommProcessor(std::vector<MsgProcessor *> msgProcessorsIn);

            /**
             * This function processes received and parsed serial messages.
             * @param msg The parsed bytes of a message.
             * @param args Arguments to use when processing the message.
             * @return Returns -1 if message not processed, otherwise the index of message processor.
             */
            int processMsg(std::vector<uint8_t> & msg, MsgProcessorArgs args);

    };
}
#endif // COMM_COMM_PROCESSOR_HPP
