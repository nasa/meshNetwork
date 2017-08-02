#include "node/nodeParams.hpp"
#include "comm/utilities.hpp"
#include "comm/commands.hpp"
#include "comm/tdmaCmds.hpp"
#include "GPIOWrapper.hpp"
#include <cmath>

using comm::FormationClock;
using comm::Cmds;

namespace node {
 
    // Create static variables
    NodeConfig NodeParams::config;
    double NodeParams::commStartTime;
    std::vector<uint8_t> NodeParams::cmdRelayBuffer;
    comm::CommBuffer<uint8_t> NodeParams::cmdHistory(10);
    std::vector<NodeState> NodeParams::nodeStatus;
    std::vector< std::vector<uint8_t> > NodeParams::linkStatus;
    TDMAStatus NodeParams::tdmaStatus;
    bool NodeParams::tdmaFailsafe;
    double NodeParams::timeOffsetTimer; 
    std::default_random_engine NodeParams::generator;
    std::uniform_int_distribution<int> NodeParams::distribution;
    FormationClock NodeParams::clock;
    bool NodeParams::nodeParamsLoaded(false);

    void NodeParams::loadParams(NodeConfig & configIn) {
        // Populate node parameters
        config = configIn;
        generator = std::default_random_engine(time(0));
        distribution = std::uniform_int_distribution<int>(0, 65536);
        clock = FormationClock();
        commStartTime = -1.0;
        for (unsigned int i = 0; i < config.maxNumNodes; i++) {
            nodeStatus.push_back(NodeState(i+1));
        }

        linkStatus.resize(config.maxNumNodes); // a row for each node
        for (unsigned int row = 0; row < config.maxNumNodes; row++) { // populate entries
            linkStatus[row].resize(config.maxNumNodes); // entry for each node
            for (unsigned int col = 0; col < config.maxNumNodes; col++) {
                linkStatus[row][col] = NoLink;
            }
        }

        // TDMA parameters
        tdmaStatus = NOMINAL; 
        tdmaFailsafe = false;
        timeOffsetTimer = -1.0;
        if (config.commConfig.fpga == true) {
            // Setup FPGA failsafe status pin
            if (config.commConfig.fpgaFailsafePin.size() > 0) {
                GPIOWrapper::setupPin(config.commConfig.fpgaFailsafePin, GPIOWrapper::INPUT);
            }
        }

        // Load command dictionary
        loadCmdDict();

        nodeParamsLoaded = true;

        return;
    }
 
    void NodeParams::loadCmdDict() {
        if (config.commType == TDMA) {
            std::unordered_map<uint8_t, comm::HeaderType> tdmaCmdDict = comm::TDMACmds::getCmdDict();
            Cmds::updateCmdDict(tdmaCmdDict);
        }
    }

    int NodeParams::getCmdCounter() {
        if (commStartTime > 0.0) { // comm start time has been initialized
            // Time-based counter
            double currentTime = util::getTime();
            return (unsigned int)((currentTime - commStartTime)*1000);
        }
        else { // random counter
            return (unsigned int)distribution(generator);
        }
    }

    int NodeParams::checkTimeOffset(double offset) {
        if (config.commType == TDMA) {
            if (config.commConfig.fpga == true && config.commConfig.fpgaFailsafePin.size() > 0) { // TDMA time controlled by FPGA
                if (GPIOWrapper::getValue(config.commConfig.fpgaFailsafePin) == 0) { //failsafe not set
                    timeOffsetTimer = -1; // reset timer
                }
                else { // failsafe condition set
                    if (timeOffsetTimer >= 0) { // timer started
                        if (clock.getTime() - timeOffsetTimer > config.commConfig.offsetTimeout) { // no time offset reading for longer than allowed
                            tdmaFailsafe = true; // set TDMA failsafe flag
                            return 3;    
                        }
                    }
                    else { // start timer
                        timeOffsetTimer = clock.getTime();
                    }
                }
            }
            else { // check offset 
                if (offset == FormationClock::invalidOffset) { // no offset provided so get from clock
                    offset = clock.getOffset();
                }
                if (offset != FormationClock::invalidOffset) { // time offset available
                    timeOffsetTimer = -1.0;
                    nodeStatus[config.nodeId-1].timeOffset = offset;
                    if (std::abs(offset) > config.commConfig.operateSyncBound) { // time offset out of bounds
                        return 1;
                    }
                }
                else { // no offset available
                    return checkOffsetFailsafe();
                }

                return 0;
            }
        }

        return -1;
    } 

    int NodeParams::checkOffsetFailsafe() {
        nodeStatus[config.nodeId-1].timeOffset = FormationClock::invalidOffset; // set to invalid value
                
        // Check time offset timer
        if (timeOffsetTimer > 0) { // timer started
            if (clock.getTime() - timeOffsetTimer >= config.commConfig.offsetTimeout) { // offset unavailablity timeout
                tdmaFailsafe = true;
                return 2;
            }
        }
        else { // start timer
            timeOffsetTimer = clock.getTime();
        }
        
        return 0;
    }
}
