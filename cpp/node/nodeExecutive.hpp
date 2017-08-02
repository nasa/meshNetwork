#ifndef NODE_NODE_EXECUTIVE_HPP
#define NODE_NODE_EXECUTIVE_HPP

#include <fstream>
#include <vector>
#include <memory>
#include "comm/comm.hpp"
#include "node/nodeController.hpp"

namespace node {

    class NodeExecutive {

        public:
            
            /**
             * Node controller instance for this node.
             */
            NodeController * nodeController;

            /**
             * Container of node communication instances.
             */
            std::vector<comm::Comm *> nodeComm;

            /**
             * Flight computer comm instance.
             */
            comm::Comm * FCComm;

            /**
             * Flight computer logging file stream.
             */
            std::ofstream * fcLogFile;

            /**
             * Default constructor.
             */
            NodeExecutive();

            /**
             * Constructor.
             * @param controller NodeController instance pointer.
             * @param nodeComm Container of node communication instances.
             * @param FCComm Flight computer comm instance.
             * @param fcLogFile Flight computer logging file stream.
             */
            NodeExecutive(NodeController * controller, std::vector<std::unique_ptr<comm::Comm>> & nodeComm, comm::Comm * FCComm, std::ofstream * fcLogFile);

            /**
             * Controls execution of all node software in the proper sequence.
             */
            virtual void executeNodeSoftware();

            /**
             * Processes messages from flight computer.
             */
            virtual void processFCMsg();
    
            /**
             * Processes messages from other nodes.
             * @param comm Comm instance to processes messages from.
             */
            virtual void processNodeMsg(comm::Comm * comm);

            /**
             * Sends outgoing flight computer messages.
             */
            virtual void sendFCCmds();

            /**
             * Sends outgoing node communications.
             */
            virtual void sendNodeCmds();
    };

}

#endif // NODE_NODE_EXECUTIVE_HPP
