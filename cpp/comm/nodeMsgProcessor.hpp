#ifndef COMM_NODE_MSG_PROCESSOR_HPP
#define COMM_NODE_MSG_PROCESSOR_HPP

#include "comm/msgProcessor.hpp"
#include <vector>
#include <cstdint>

namespace comm {

    class NodeMsgProcessor : public MsgProcessor {
   
        public:
            NodeMsgProcessor();
 
            /**
             * Processes received node command messages.
             * @param cmdId Command ID of received command bytes.
             * @param msg Raw command message bytes.
             * @param args Arguments to be used to process command.
             */
            virtual bool processMsg(uint8_t cmdId, std::vector<uint8_t> & msg, MsgProcessorArgs & args);

    };
}
#endif // COMM_NODE_MSG_PROCESSOR_HPP
