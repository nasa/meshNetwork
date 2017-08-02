#include "node/nodeController.hpp"
#include "node/nodeParams.hpp"

namespace node {

    NodeController::NodeController() :
        logFile(NULL)
    {}

    NodeController::NodeController(std::ofstream * logFileIn) :
        logFile(logFileIn),
        logTime(0.0)
    {
        // Set logging precision
        if (logFile != NULL) {
            logFile->setf(std::ios::fixed);
            logFile->precision(6);
        }
    }

    void NodeController::controlNode() {
        // Process commands
        processCommands();

        // Check status of other formation nodes
        monitorFormationStatus();

        // Run unique node behavior
        executeNode();

        // Log data
        logData();

    }

    void NodeController::executeNode() {
        monitorFormationStatus();
    }

    void NodeController::processFCCommands(comm::Comm * FCComm) {
    }

    void NodeController::processNodeCommands(comm::Comm * comm) {
    }

    void NodeController::processCommands() {
    }

    void NodeController::logData() {
    }

    void NodeController::monitorFormationStatus() {
        // Check that other nodes' status are updating
        for (unsigned int i = 0; i < NodeParams::nodeStatus.size(); i++) {
            if ((NodeParams::nodeStatus[i].lastStateUpdateTime + NodeParams::config.nodeUpdateTimeout) < NodeParams::clock.getTime()) {
                NodeParams::nodeStatus[i].updating = true;
            }
            else {
                NodeParams::nodeStatus[i].updating = false;
            }
        }
    }

    void NodeController::checkNodeLinks() {
        // TODO   
    }
}
