#include "node/nodeExecutive.hpp"

using std::vector;
using std::unique_ptr;

namespace node {

    NodeExecutive::NodeExecutive() :
        nodeController(NULL),
        FCComm(NULL),
        fcLogFile(NULL)
    {}

    NodeExecutive::NodeExecutive(NodeController * controllerIn, vector<unique_ptr<comm::Comm>> & nodeCommIn, comm::Comm * FCCommIn, std::ofstream * fcLogFileIn) :
        nodeController(controllerIn),
        FCComm(FCCommIn),
        fcLogFile(fcLogFileIn)
    {
        for (unsigned int i = 0; i < nodeCommIn.size(); i++) {
            nodeComm.push_back(nodeCommIn[i].get());
        }
    }

    void NodeExecutive::executeNodeSoftware() {
        // Process data from flight computer
        processFCMsg();

        // Check mesh connections for new messages
        for (unsigned int i = 0; i < nodeComm.size(); i++) {
            processNodeMsg(nodeComm[i]);
        }

        // Run node control algorithms
        if (nodeController != NULL) {
            nodeController->controlNode();
        }

        // Send commands to flight computer
        sendFCCmds();

        // Send outgoing node messages to other formation nodeParams
        sendNodeCmds();
    }

    void NodeExecutive::processFCMsg() {
        if (FCComm != NULL) {
            FCComm->readMsgs();
        }
    }

    void NodeExecutive::processNodeMsg(comm::Comm * comm) {
        if (comm != NULL) {
            comm->readMsgs();
        }
    }

    void NodeExecutive::sendFCCmds() {

    }

    void NodeExecutive::sendNodeCmds() {

    }

}
