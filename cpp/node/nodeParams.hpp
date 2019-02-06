#ifndef NODE_NODE_PARAMS_HPP
#define NODE_NODE_PARAMS_HPP

#include <vector>
#include <random>
#include "node/nodeConfig.hpp"
#include "comm/commBuffer.hpp"
#include "node/nodeState.hpp"
#include "comm/formationClock.hpp"

namespace node {

    class NodeParams {

        public:

            /**
             * Load parameters from node configuration.
             * @param config Node configuration.
             */
            static void loadParams(NodeConfig & config);
            static void loadParams(std::string configFile);
            
            static void init();

            /**
             * Populates command dictionary.
             */
            //static void loadCmdDict();

            /**
             * Get new command counter value.
             @return Returns command counter value.
             */
            static uint16_t getCmdCounter();

            /**
             * Node configuration instance.
             */
            static NodeConfig config;

            /**
             * Command counter history FIFO buffer.
             */
            static comm::CommBuffer<uint16_t> cmdHistory;

            /**
             * Node status structure.
             */
            static std::vector<NodeState> nodeStatus;

            /**
             * Random number generator.
             */
            static std::default_random_engine generator;

            /**
             * Random number distribution.
             */
            static std::uniform_int_distribution<int> distribution;

            /**
             * Formation clock.
             */
            static comm::FormationClock clock;

            /**
             * Node parameters loaded flag.
             */
            static bool nodeParamsLoaded;

            /**
             * Configuration check confirmation flag.
             */
            static bool configConfirmed;

            /**
             * Network links status.
             */
            static std::vector< std::vector<uint8_t> > linkStatus;

    };
}

#endif // NODE_NODE_PARAMS_HPP
