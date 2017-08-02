#ifndef NODE_NODE_CONFIG_HPP
#define NODE_NODE_CONFIG_HPP

#include <string>
#include <vector>
#include <iostream>
#include <cstdint>
#include "rapidjson/document.h"
#include "rapidjson/JSON_Wrapper.hpp"
#include "node/nodeConfigSupport.hpp"

namespace node {

    class NodeConfig {

        public:
            /**
             * Default constructor.
             */
            NodeConfig();

            /**
             * Constructor.
             * @param configFile File path to configuration file.
             */
            NodeConfig(std::string configFile);

            /**
             * Load general node configuration.
             * @param json Configuration JSON structure.
             */
            void loadNodeConfig(rapidjson::Document & json);
            
            /**
             * Load software interface configuration.
             * @param json Configuration JSON structure.
             */
            void loadSoftwareInterface(rapidjson::Document & json);
            
            /**
             * Loads platform specific configuration parameters.
             * @param json Configuration JSON structure.
             */
            virtual void loadPlatformConfig(rapidjson::Document & json) {};

            /**
             * Load communication configuration parameters.
             * @param json Configuration JSON structure.
             */
            void loadCommConfig(rapidjson::Document & json);

            /**
             * Reads DIP switch states to determine node ID.
             * @return Returns true if node ID successfully read.
             */
            bool readNodeId();

            /**
             * Update parameter.
             * @param name Name of parameter to update.
             * @param value New parameter value.
             */
            bool updateParam(ParamName param, std::vector<uint8_t> value); 

            /**
             * Calculates a hash of configuration parameters for comparison.
             */
            std::string calculateHash();

            // *** Basic node parameters ***

            /**
             * Type of node platform.
             */
            PlatformType platform;

            /**
             * Node ID number.
             */
            unsigned int nodeId;

            /**
             * Maximum number of nodes in network.
             */
            unsigned int maxNumNodes;

            /**
             * Allowable time in seconds between updates from a node.
             */
            double nodeUpdateTimeout;

            /**
             * Size of configuration hash.
             */
            int hashSize;

            // *** Communication parameters ***

            /**
             * Number of mesh networks.
             */
            unsigned int numMeshNetworks;

            /**
             * Maximum number of bytes to attempt to read from uart.
             */
            unsigned int uartNumBytesToRead;

            /**
             * Maximum number of messages to attempt to parse from one comm packet.
             */
            unsigned int parseMsgMax;

            /**
             * Size of receive buffer.
             */
            unsigned int rxBufferSize;

            /**
             * Time in seconds between consecutive flight computer comm attempts.
             */
            double FCCommWriteInterval;

            /**
             * Mesh network communication baudrate.
             */
            unsigned int meshBaudrate;

            /**
             * Flight computer communication baudrate.
             */
            unsigned int FCBaudrate;

            /**
             * Mesh device names.
             */
            std::vector<std::string> meshDevices;

            /**
             * Mesh network radio types.
             */
            std::vector<RadioType> radios;

            /**
             * Mesh network message parser types.
             */
            std::vector<MsgParserType> msgParsers;

            /**
             * Name of flight computer comm device.
             */
            std::string FCCommDevice;

            /**
             * Interval in seconds between consecutive repeating commands.
             */
            double cmdInterval;

            /**
             * Data logging interval.
             */
            double logInterval;

            /**
             * Software interface configuration.
             */
            SoftwareInterface interface;

            /**
             * Mesh network communication type.
             */
            CommType commType;

            /**
             * Communication configuration structure.
             */
            CommConfig commConfig;

    };
}

#endif // NODE_NODE_CONFIG_HPP
