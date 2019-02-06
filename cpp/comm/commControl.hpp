#ifndef COMM_COMM_CONTROL_HPP
#define COMM_COMM_CONTROL_HPP

#include "node/nodeInterface.hpp"
#include "node/nodeInterface.pb.h"
#include <serial/serial.h>
#include "comm/radio.hpp"
#include "comm/msgParser.hpp"
#include "comm/SLIPMsgParser.hpp"
//#include "comm/commProcessor.hpp"
#include "comm/tdmaMsgProcessor.hpp"
#include "comm/serialComm.hpp"
#include "comm/tdmaComm.hpp"
#include <memory>

namespace comm {

    class CommControl {

        public:

            /** 
             * Node to comm interface comm.
             */
            SerialComm nodeComm;

            /**
             * Node to comm interface message parser.
             */
            std::unique_ptr<MsgParser> nodeMsgParser; 

            /**
             * Serial connection used for mesh network communication.
             */
            serial::Serial ser;

            /**
             * Radio for mesh network communication.
             */
            std::unique_ptr<Radio> radio;

            /**
             * Message parser for mesh network communication.
             */
            std::unique_ptr<MsgParser> msgParser;

            /**
             * Mesh network TDMA message processor.
             */
            TDMAMsgProcessor tdmaMsgProcessor;

            /**
             * Mesh network communication processor.
             */
            //CommProcessor commProcessor = CommProcessor(std::vector<MsgProcessor *>({&tdmaMsgProcessor}));

            /**
             * Mesh network comm instance.
             */
            std::unique_ptr<TDMAComm> comm;

            /**
             * Interthread comm-node interface.
             */
            node::NodeInterface * commInterface;

            /**
             * Latest data received from node control thread.
             */
            nodeInterface::NodeThreadMsg lastData;

            /**
             * Lower time bound for node control execution.
             */
            double minNodeControlTime;

            /**
             * Upper time bound for node control execution.
             */
            double maxNodeControlTime;

            double lastNodeCmdTime;

            /**
             * Constructor.
             * @param meshNum Mesh network ID.
             * @param commInterface Interthread communication interface.
             */
            CommControl(unsigned int meshNum, Radio * radioIn, node::NodeInterface *commInterface);

            /**
             * Runs communication control logic sequence.
             */
            void run();

            /**
             * Executes communication control thread.
             */
            void execute();
    };

}

#endif // COMM_COMM_CONTROL_HPP
