#ifndef NODE_NODE_CONTROLLER_HPP
#define NODE_NODE_CONTROLLER_HPP

#include <fstream>
#include <map>
#include <memory>
#include "comm/comm.hpp"
#include "comm/command.hpp"

namespace node {

    class NodeController {

        public:

            /**
             * Node logging file stream.
             */            
            std::ofstream * logFile;

            /**
             * Last log entry time.
             */
            double logTime;

            /**
             * Container of outgoing flight computer commands.
             */
            std::map<uint8_t, std::unique_ptr<comm::Command>> fcOutputCmds; 

            /**
             * Container of outgoing node commands.
             */
            std::map<uint8_t, std::unique_ptr<comm::Command>> nodeOutputCmds; 

            /**
             * Default constructor.
             */
            NodeController();

            /**
             * Constructor.
             * @param logFile Node logging file stream.
             */
            NodeController(std::ofstream * logFile);

            /**
             * Controls node logic execution.
             */
            virtual void controlNode();

            /**
             * Executes primary formation node processing logic and position commanding.
             */
            virtual void executeNode();
            
            /**
             * Performs initial processing of incoming flight computer commands and messages.
             * @param FCComm Flight computer communication instance pointer.
             */   
            virtual void processFCCommands(comm::Comm * FCComm);

            /**
             * Performs initial processing of incoming node commands and messages."
             */
            virtual void processNodeCommands(comm::Comm * comm);

            /**
             * Performs lower level processing and implementation of received commands."
             */
            virtual void processCommands();

            /**
             * Logs pertinent operational and state data.
             */
            virtual void logData();

            /**
             * Monitors and determines status of other formation nodes.
             */
            virtual void monitorFormationStatus();
            
            /**
             * Checks status of links to each node in the network.
             */
            virtual void checkNodeLinks();
    };

}

#endif // NODE_NODE_CONTROLLER_HPP
