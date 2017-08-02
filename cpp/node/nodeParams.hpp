#ifndef NODE_NODE_PARAMS_HPP
#define NODE_NODE_PARAMS_HPP

#include <vector>
#include <random>
#include "node/nodeConfig.hpp"
#include "comm/commBuffer.hpp"
#include "node/nodeState.hpp"
#include "comm/formationClock.hpp"

namespace node {

    enum TDMAStatus {
        NOMINAL = 0,
        BLOCK_TX = 1
    };

    class NodeParams {

        public:

            /**
             * Load parameters from node configuration.
             * @param config Node configuration.
             */
            static void loadParams(NodeConfig & config);

            /**
             * Populates command dictionary.
             */
            static void loadCmdDict();

            /**
             * Get new command counter value.
             @return Returns command counter value.
             */
            static int getCmdCounter();

            /**
             * Check time offset bounds.
             * @param offset Current time offset value.
             * @return Returns status of time offset.
             */
            static int checkTimeOffset(double offset = comm::FormationClock::invalidOffset);

            /**
             * Checks for time offset failsafe.
             */
            static int checkOffsetFailsafe();

            /**
             * Node configuration instance.
             */
            static NodeConfig config;

            /**
             * Mesh communication start time
             */
            static double commStartTime;

            /**
             * Buffer of commands to relay.
             */
            static std::vector<uint8_t> cmdRelayBuffer;

            /**
             * Command counter history FIFO buffer.
             */
            static comm::CommBuffer<uint8_t> cmdHistory;

            /**
             * Node status structure.
             */
            static std::vector<NodeState> nodeStatus;

            /**
             * Status of TDMA mesh network.
             */
            static TDMAStatus tdmaStatus;

            /**
             * TDMA in failsafe status flag.
             */
            static bool tdmaFailsafe;

            /**
             * Time that time offset was found unavailable.
             */
            static double timeOffsetTimer;

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
             * Network links status.
             */
            static std::vector< std::vector<uint8_t> > linkStatus;

    };
}

#endif // NODE_NODE_PARAMS_HPP
