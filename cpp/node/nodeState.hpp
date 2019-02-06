#ifndef NODE_NODE_STATE_HPP
#define NODE_NODE_STATE_HPP

#include <cstdint>
#include <vector>

namespace node {

    enum LinkStatus {
        NoLink = 0,
        IndirectLink = 2,
        GoodLink = 1,
        BadLink = 3
    };

    class NodeState {

        public:

            /**
             * Constructor.
             * @param id Node id number.
             */
            NodeState(uint8_t id = 0);

            /**
             * Node id number.
             */
            uint8_t id;

            /**
             * Presence flag.
             */
            bool present;

            /**
             * Status updating flag.
             */
            bool updating;

            /**
             * Current flight mode.
             */
            uint8_t flightMode;

            /**
             * Current formation mode.
             */
            uint8_t formationMode;

            /**
             * Current failsafe type if applicable.
             */
            uint8_t failsafeType;

            /**
             * State vector
             */
            std::vector<double> state;

            /**
             * Timestamp corresponding to last received state update.
             */
            double timestamp;

            /**
             * Current clock time offset.
             */
            double timeOffset;

            /**
             * Number of messages received from this node.
             */
            uint16_t numMsgsReceived;

            /**
             * Time that last state update was received.
             */
            double lastStateUpdateTime;

            /**
             * Time that last message was received.
             */
            double lastMsgRcvdTime;

            /**
             * Status byte to indicate various status conditions.
             */
            uint8_t status;

    };
}

#endif // NODE_NODE_STATE_HPP
