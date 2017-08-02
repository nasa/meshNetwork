#ifndef COMM_TDMA_MSG_PROCESSOR_HPP
#define COMM_TDMA_MSG_PROCESSOR_HPP

#include "comm/msgProcessor.hpp"
#include <vector>
#include <cstdint>

namespace comm {

    class TDMAMsgProcessor : public MsgProcessor {

        public:
            /**
             * Default constructor.
             */
            TDMAMsgProcessor();

            /**
             * Processes received TDMA command messages.
             * @param cmdId Command ID of message.
             * @param msg Command message bytes.
             * @param args Message processor arguments.
             */
            virtual void processMsg(uint8_t cmdId, std::vector<uint8_t> & msg, MsgProcessorArgs & args);

    };
}
#endif // COMM_TDMA_MSG_PROCESSOR_HPP
