#ifndef COMM_TEST_MSG_PROCESSOR_HPP
#define COMM_TEST_MSG_PROCESSOR_HPP

#include "comm/msgProcessor.hpp"
#include <vector>
#include <cstdint>

namespace comm {

    class TestMsgProcessor : public MsgProcessor {
   
        public:
            TestMsgProcessor();
 
            virtual void processMsg(uint8_t cmdId, std::vector<uint8_t> & msg, MsgProcessorArgs args);

    };
}
#endif // COMM_TEST_MSG_PROCESSOR_HPP
