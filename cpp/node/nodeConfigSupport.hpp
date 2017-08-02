#ifndef NODE_NODE_CONFIG_SUPPORT_HPP
#define NODE_NODE_CONFIG_SUPPORT_HPP

#include "rapidjson/JSON_Wrapper.hpp"
#include <cmath>

namespace node {

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
        std::string nodeCommIntIP;
        unsigned int commRdPort;
        unsigned int commWrPort;
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
         * Transmission baudrate.
         */
        unsigned int txBaudrate;

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
         * Default constructor.
         */
        CommConfig() {};

        /**
         * Constructor for loading config from a JSON file.
         * @param nodeId Node ID number for this node.
         * @param type Communication protocol type.
         * @param value JSON configuration data.
         */
        CommConfig(unsigned int nodeId, CommType type, const rapidjson::Value & value) {
            // Load values from JSON
            get_string(value, "sleepPin", sleepPin);
            get_int(value, "txBaudrate", txBaudrate);
            get_double(value, "enableLength", enableLength);
            get_double(value, "slotGuardLength", slotGuardLength);
            get_double(value, "preTxGuardLength", preTxGuardLength);
            get_double(value, "postTxGuardLength", postTxGuardLength);
            get_double(value, "txLength", txLength);
            get_double(value, "rxDelay", rxDelay);
            get_double(value, "initTimeToWait", initTimeToWait);
            get_int(value, "maxNumSlots", maxNumSlots);
            get_double(value, "desiredDataRate", desiredDataRate);
            get_double(value, "initSyncBound", initSyncBound);
            get_double(value, "operateSyncBound", operateSyncBound);
            get_double(value, "offsetTimeout", offsetTimeout);
            get_double(value, "offsetTxInterval", offsetTxInterval);
            get_double(value, "statusTxInterval", statusTxInterval);
            get_double(value, "linksTxInterval", linksTxInterval);
            get_int(value, "maxTxBlockSize", maxTxBlockSize);
            get_int(value, "blockTxRequestTimeout", blockTxRequestTimeout);
            get_int(value, "minBlockTxDelay", minBlockTxDelay);
            get_bool(value, "fpga", fpga);
            get_string(value, "fpgaFailsafePin", fpgaFailsafePin);

            // Process comm inputs
            rxLength = preTxGuardLength + txLength + postTxGuardLength;
            slotLength = enableLength + rxLength + slotGuardLength;
            frameLength = 1.0 / desiredDataRate;
            cycleLength = slotLength * maxNumSlots;
            maxTransferSize = (unsigned int)(0.8 * txLength * txBaudrate / 8.0);
            maxBlockTransferSize = (unsigned int)(0.8 * cycleLength * txBaudrate / 8.0);

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
                // Determine transmit slot
                if (nodeId == 0) { // ground node
                    transmitSlot = maxNumSlots;
                }
                else { // standard node
                    transmitSlot = nodeId;
                }
            }

        }
    };

}

#endif // NODE_NODE_CONFIG_SUPPORT_HPP
