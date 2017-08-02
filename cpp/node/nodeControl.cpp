#include "node/nodeControl.hpp"
#include "node/nodeParams.hpp"
#include "comm/comm.hpp"
#include "comm/SLIPMsgParser.hpp"
#include "comm/serialRadio.hpp"
//#include "node/nodeConfigSupport.hpp"
//#include "node/pixhawk/pixhawkComm.hpp"
//#include "node/pixhawk/pixhawkNodeController.hpp"
//#include "node/pixhawk/pixhawkNodeExecutive.hpp"
#include <unistd.h>
#include <thread>

using std::unique_ptr;

namespace node {

    NodeControl::NodeControl(unsigned int meshNum, comm::Radio * radioIn, NodeInterface * commInterfaceIn, std::ofstream * nodeLogFile, std::ofstream * fcLogFile, std::ofstream * cmdLogFile) :
        FCSer(NodeParams::config.FCCommDevice, NodeParams::config.FCBaudrate, serial::Timeout::simpleTimeout(10)),
        commInterface(commInterfaceIn)
    {

        // Create FC radio
        comm::RadioConfig config;
        config.numBytesToRead = NodeParams::config.uartNumBytesToRead;
        config.rxBufferSize = NodeParams::config.rxBufferSize;
        FCRadio = unique_ptr<comm::Radio>(new comm::SerialRadio(&FCSer, config)); // FC radio

        // Create message parsers
        switch (NodeParams::config.msgParsers[meshNum]) {
            case SLIP_PARSER:
                msgParsers.push_back(unique_ptr<comm::MsgParser>(new comm::SLIPMsgParser(NodeParams::config.parseMsgMax, 256)));
                break;
            case STANDARD_PARSER:
                msgParsers.push_back(unique_ptr<comm::MsgParser>(new comm::MsgParser(NodeParams::config.parseMsgMax)));
                break;
        }
        FCMsgParser = unique_ptr<comm::MsgParser>(new comm::SLIPMsgParser(NodeParams::config.parseMsgMax, 256)); // FC comm message parser

        // Instantiate specific node software
        switch (NodeParams::config.platform) { // Platform specific initializations
            case GENERIC:
                comms.push_back(unique_ptr<comm::Comm>(new comm::Comm(NULL, radioIn, msgParsers.front().get())));
                FCComm = unique_ptr<comm::Comm>(new comm::Comm(NULL, FCRadio.get(), FCMsgParser.get()));
                nodeController = unique_ptr<NodeController>(new NodeController(nodeLogFile));
                nodeExecutive = unique_ptr<NodeExecutive>(new NodeExecutive(nodeController.get(), comms, NULL, fcLogFile));
                break;
//            case PIXHAWK:
//                comms.push_back(unique_ptr<comm::Comm>(new PixhawkComm(radioIn, msgParsers.front().get())));
//                FCComm = unique_ptr<comm::Comm>(new PixhawkComm(FCRadio.get(), msgParsers.back().get()));
//                nodeController = unique_ptr<NodeController>(new PixhawkNodeController(nodeLogFile, cmdLogFile));
//                nodeExecutive = unique_ptr<NodeExecutive>(new PixhawkNodeExecutive(nodeController.get(), comms, NULL, fcLogFile));
//                break;
            default:
                break;
        }    

    }

    void NodeControl::run() {
        while (true) {
           if (NodeParams::config.commConfig.fpga == true || commInterface->nodeControlRunFlag == true) {
                // Run node executive
                nodeExecutive->executeNodeSoftware();
                commInterface->nodeControlRunFlag = false; // reset run flag

                // Sleep for minimum delay between executions
                usleep(0.5*1e6);
            }
            else {
                // Sleep before checking run flag again
                usleep(0.1*1e6);
            }
        }
    }
    
    void NodeControl::execute() {
        std::thread runThread([this] { this->run(); });
        runThread.detach();
    }

}
