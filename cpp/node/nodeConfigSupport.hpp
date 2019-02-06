#ifndef NODE_NODE_CONFIG_SUPPORT_HPP
#define NODE_NODE_CONFIG_SUPPORT_HPP

#include "rapidjson/JSON_Wrapper.hpp"
#include <cmath>
#include <algorithm>

namespace node {

    enum ParamId {
        PARAMID_PARSE_MSG_MAX = 1
    };
    
    enum ParamName {
            
    };

    // Communication type.
    enum CommType {
        STANDARD = 0,
        TDMA = 1
    };

    // Radio type.
    enum RadioType {
        XBEE = 0,
        LI1 = 1
    };

    // Message parser type.
    enum MsgParserType {
        SLIP_PARSER = 0,
        STANDARD_PARSER = 1
    };

    // Node platform type.
    enum PlatformType {
        PIXHAWK = 0,
        SATFC = 1,
        GENERIC = 2
    };

    struct SoftwareInterface {
        /**
         * IP address to interface with platform.
         */
        std::string nodeCommIntIP;

        /**
         * Input UDP port from platform.
         */
        unsigned int commRdPort;
        
        /**
         * Output UDP port to platform.
         */
        unsigned int commWrPort;
        
        /**
         * Load success flag.
         */
        bool loadSuccess;
    
        /**
         * Default constructor.
         */
        SoftwareInterface() {};

        /**
         * Constructor for loading config from a JSON file.
         * @param value JSON configuration data.
         */
        SoftwareInterface(const rapidjson::Value & intConfig) : 
            loadSuccess(true)
        {
            // Load values from JSON
            loadSuccess &= get_string(intConfig, "nodeCommIntIP", nodeCommIntIP);
            loadSuccess &= get_int(intConfig, "commRdPort", commRdPort);
            loadSuccess &= get_int(intConfig, "commWrPort", commWrPort);
        }
    };

    struct CommConfig {
        /**
         * Radio sleep pin
         */
        std::string sleepPin;        

        /**
         * Pre-transmit guard length.
         */
        double preTxGuardLength;

        /**
         * Post-transmit guard length.
         */
        double postTxGuardLength;

        /**
         * Transmit length.
         */
        double txLength;

        /**
         * TDMA enable length.
         */
        double enableLength;

        /**
         * TDMA delay before attempting read.
         */
        double rxDelay;

        /**
         * Maximum number of TDMA slots.
         */
        unsigned int maxNumSlots;

        /**
         * TDMA slot guard length.
         */
        double slotGuardLength;

        /**
         * Desired data throughput baudrate.
         */
        double desiredDataRate;

        /**
         * Time to wait for mesh messages before initializing a new mesh.
         */
        double initTimeToWait;

        /**
         * Time offset error bound for initialization.
         */
        double initSyncBound;

        /**
         * Time offset error bound during TDMA operation.
         */
        double operateSyncBound;

        /**
         * Time allowed between offset value checks before initiating failsafe.
         */
        double offsetTimeout;

        /**
         * Time between successive transmissions of offset status.
         */
        double offsetTxInterval;

        /**
         * Time between successive transmissions of node status.
         */
        double statusTxInterval;

        /**
         * Time between successive transmissions of links status.
         */
        double linksTxInterval;

        /**
         * Maximum block transmit block data block size.
         */
        unsigned int maxTxBlockSize;

        /**
         * Time to wait for response from other nodes before timing out a block transmit request.
         */
        unsigned int blockTxRequestTimeout;

        /**
         * Minimum number of frames to wait before starting block transmit.
         */
        unsigned int minBlockTxDelay;

        /**
         * TDMA receive period length.
         */
        double rxLength;

        /**
         * TDMA slot length.
         */
        double slotLength;

        /**
         * TDMA frame length.
         */
        double frameLength;

        /**
         * TDMA cycle length.
         */
        double cycleLength;

        /**
         * Maximum size of data to transmit in a single message.
         */
        unsigned int maxTransferSize;

        /**
         * Receive buffer size.
         */
        unsigned int rxBufferSize;

        /**
         * Maximum size of data to transmit in a single message during a block transfer.
         */
        unsigned int maxBlockTransferSize;

        /**
         * Transmit slot number.
         */
        unsigned int transmitSlot;

        /**
         * FPGA presence flag
         */
        bool fpga;

        /**
         * FPGA failsafe pin
         */
        std::string fpgaFailsafePin;
        
        /**
         * FPGA fifo size.
         */
        unsigned int fpgaFifoSize;

        /**
         * FPGA enable pin
         */
        std::string enablePin;
        
        /**
         * FPGA status pin
         */
        std::string statusPin;

        /**
         * Load success flag.
         */
        bool loadSuccess;
    
        /**
         * Default constructor.
         */
        CommConfig() {};

        /**
         * Constructor for loading config from a JSON file.
         * @param nodeId Node ID number for this node.
         * @param type Communication protocol type.
         * @param value JSON configuration data.
         */
        CommConfig(unsigned int nodeId, unsigned int meshBaudrate, CommType type, const rapidjson::Value & value) :
            fpga(false),
            loadSuccess(true)
        {
            // Load values from JSON
            loadSuccess &= get_string(value, "sleepPin", sleepPin);
            loadSuccess &= get_double(value, "enableLength", enableLength);
            loadSuccess &= get_double(value, "slotGuardLength", slotGuardLength);
            loadSuccess &= get_double(value, "preTxGuardLength", preTxGuardLength);
            loadSuccess &= get_double(value, "postTxGuardLength", postTxGuardLength);
            loadSuccess &= get_double(value, "txLength", txLength);
            loadSuccess &= get_double(value, "rxDelay", rxDelay);
            loadSuccess &= get_double(value, "initTimeToWait", initTimeToWait);
            loadSuccess &= get_int(value, "maxNumSlots", maxNumSlots);
            loadSuccess &= get_double(value, "desiredDataRate", desiredDataRate);
            loadSuccess &= get_double(value, "initSyncBound", initSyncBound);
            loadSuccess &= get_double(value, "operateSyncBound", operateSyncBound);
            loadSuccess &= get_double(value, "offsetTimeout", offsetTimeout);
            loadSuccess &= get_double(value, "offsetTxInterval", offsetTxInterval);
            loadSuccess &= get_double(value, "statusTxInterval", statusTxInterval);
            loadSuccess &= get_double(value, "linksTxInterval", linksTxInterval);
            loadSuccess &= get_int(value, "maxTxBlockSize", maxTxBlockSize);
            loadSuccess &= get_int(value, "blockTxRequestTimeout", blockTxRequestTimeout);
            loadSuccess &= get_int(value, "minBlockTxDelay", minBlockTxDelay);
         
            if (value.HasMember("fpga")) {
                loadSuccess &= get_bool(value, "fpga", fpga);
                if (fpga == true) {
                    loadSuccess &= get_string(value, "fpgaFailsafePin", fpgaFailsafePin);
                    loadSuccess &= get_int(value, "fpgaFifoSize", fpgaFifoSize);
                    loadSuccess &= get_string(value, "enablePin", enablePin);
                    loadSuccess &= get_string(value, "statusPin", statusPin);
                }
            }

            // Process comm inputs
            rxLength = preTxGuardLength + txLength + postTxGuardLength;
            slotLength = enableLength + rxLength + slotGuardLength;
            if (desiredDataRate > 0) {
                frameLength = 1.0 / desiredDataRate;
            }
            else {
                loadSuccess = false;
            }
            cycleLength = slotLength * maxNumSlots;
            maxTransferSize = (unsigned int)(0.8 * txLength * meshBaudrate / 8.0);
            if (fpga == true) {
                maxTransferSize = std::min(maxTransferSize, fpgaFifoSize);
            }
            maxTransferSize = (unsigned int)(0.8 * maxTransferSize); // apply margin

            rxBufferSize = maxNumSlots * maxTransferSize;

            maxBlockTransferSize = (unsigned int)(0.8 * cycleLength * meshBaudrate/8.0);

            if (rxDelay > 1.0 || rxDelay < 0.0) {
                std::cout << "ERROR: Invalid TDMA Rx Delay percentage!" << std::endl;
            }
            else { // convert percentage
                rxDelay = rxDelay * txLength;
            }

            double sleepLength = frameLength - cycleLength;
            if (sleepLength < 0.0) { // Config infeasible
                std::cout << "ERROR: TDMA Frame length is less than Cycle length!" << std::endl;
            }

            if (get_int(value, "transmitSlot", transmitSlot) == false) { // transmit slot not provided
                transmitSlot = nodeId;
            }

        }
    };

}

#endif // NODE_NODE_CONFIG_SUPPORT_HPP
