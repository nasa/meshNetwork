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
    comm::CommBuffer<uint16_t> NodeParams::cmdHistory(50);
    std::vector<NodeState> NodeParams::nodeStatus;
    std::vector< std::vector<uint8_t> > NodeParams::linkStatus;
    std::default_random_engine NodeParams::generator(time(0));
    std::uniform_int_distribution<int> NodeParams::distribution(0, 65536);
    FormationClock NodeParams::clock;
    bool NodeParams::nodeParamsLoaded(false);
    bool NodeParams::configConfirmed(false);

    void NodeParams::loadParams(std::string configFile) 
    {
        config = NodeConfig(configFile);

        NodeParams::init();
    }

    void NodeParams::loadParams(NodeConfig & configIn) 
    {
        config = configIn;

        // Populate node parameters
        //config = configIn;

        // Command counter parameters
        //generator = std::default_random_engine(time(0));
        //distribution = std::uniform_int_distribution<int>(0, 65536);

        
        //clock = FormationClock();

        NodeParams::init();
    }

    void NodeParams::init() 
    {
        nodeStatus.resize(config.maxNumNodes);
        for (unsigned int i = 0; i < config.maxNumNodes; i++) {
            nodeStatus[i] = NodeState(i+1);
        }

        linkStatus.resize(config.maxNumNodes); // a row for each node
        for (unsigned int row = 0; row < config.maxNumNodes; row++) { // populate entries
            linkStatus[row].resize(config.maxNumNodes); // entry for each node
            for (unsigned int col = 0; col < config.maxNumNodes; col++) {
                linkStatus[row][col] = NoLink;
            }
        }

        // TDMA parameters
        if (config.commType == TDMA) { // load TDMA command dictionary
            std::unordered_map<uint8_t, comm::HeaderType> tdmaCmdDict = comm::TDMACmds::getCmdDict();
            Cmds::updateCmdDict(tdmaCmdDict);
            
            if (config.commConfig.fpga == true) {
                // Setup FPGA failsafe status pin
                if (config.commConfig.fpgaFailsafePin.size() > 0) {
                    GPIOWrapper::setupPin(config.commConfig.fpgaFailsafePin, GPIOWrapper::INPUT);
                }
            }
        }

        nodeParamsLoaded = true;

        return;
    }
 
    /*void NodeParams::loadCmdDict() {
        if (config.commType == TDMA) {
            std::unordered_map<uint8_t, comm::HeaderType> tdmaCmdDict = comm::TDMACmds::getCmdDict();
            Cmds::updateCmdDict(tdmaCmdDict);
        }
    }*/

    uint16_t NodeParams::getCmdCounter() {
        //if (commStartTime > 0.0) { // comm start time has been initialized
        //    // Time-based counter
        //    double currentTime = util::getTime();
        //    return (unsigned int)((currentTime - commStartTime)*1000);
        //}
        //else { // random counter
            return (uint16_t)distribution(generator);
        //}
    }

}
