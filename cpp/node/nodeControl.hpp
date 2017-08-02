#ifndef NODE_NODE_CONTROL_HPP
#define NODE_NODE_CONTROL_HPP

#include "node/nodeInterface.hpp"
#include <serial/serial.h>
#include "comm/radio.hpp"
#include "comm/msgParser.hpp"
#include "comm/comm.hpp"
#include "node/nodeController.hpp"
#include "node/nodeExecutive.hpp"
#include <fstream>
#include <memory>

namespace node {

    class NodeControl {

        public:

            serial::Serial FCSer;
            std::unique_ptr<comm::Comm> FCComm;
            std::vector<std::unique_ptr<comm::Comm>> comms;
            std::unique_ptr<comm::Radio> FCRadio;
            std::vector<std::unique_ptr<comm::MsgParser>> msgParsers;
            std::unique_ptr<comm::MsgParser> FCMsgParser;
            NodeInterface * commInterface;
            std::unique_ptr<NodeController> nodeController;
            std::unique_ptr<NodeExecutive> nodeExecutive;

            NodeControl(unsigned int meshNum, comm::Radio * radioIn, NodeInterface * commInterfaceIn, std::ofstream * nodeLogFile, std::ofstream * fcLogFile, std::ofstream * cmdLogFile);

            void run();
            
            /**
             * Executes node control thread.
             */
            void execute();
    };

}

#endif // NODE_NODE_CONTROL_HPP
