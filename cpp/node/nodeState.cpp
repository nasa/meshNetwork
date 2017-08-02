#include "node/nodeState.hpp"
#include "comm/formationClock.hpp"

namespace node {
    
    NodeState::NodeState(uint8_t idIn) :
        id(idIn),
        present(false),
        updating(false),
        flightMode(0),
        formationMode(0),
        failsafeType(0),
        timestamp(-1.0),
        timeOffset(comm::FormationClock::invalidOffset),
        numMsgsReceived(0),
        lastStateUpdateTime(0.0),
        lastMsgRcvdTime(0.0),
        status(0)
    {}
}
