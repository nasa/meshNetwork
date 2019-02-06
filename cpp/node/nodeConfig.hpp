#ifndef NODE_NODE_CONFIG_HPP
#define NODE_NODE_CONFIG_HPP

#include <string>
#include <vector>
#include <iostream>
#include <cstdint>
#include <openssl/sha.h>
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
             * Load node configuration file.
             * @param configFile Configuration file path.
             */
            void loadConfigFile(std::string configFile);
            
            /**
             * Load general node configuration.
             * @param json Configuration JSON structure.
             */
            bool loadNodeConfig(rapidjson::Document & json);
            
            /**
             * Load software interface configuration.
             * @param json Configuration JSON structure.
             */
            bool loadInterfaceConfig(rapidjson::Document & json);
            
            /**
             * Loads platform specific configuration parameters.
             * @param json Configuration JSON structure.
             */
            virtual bool loadPlatformConfig(rapidjson::Document & json);

            /**
             * Load communication configuration parameters.
             * @param json Configuration JSON structure.
             */
            bool loadCommConfig(rapidjson::Document & json);

            /**
             * Reads DIP switch states to determine node ID.
             * @return Returns true if node ID successfully read.
             */
            virtual bool readNodeId();

            /**
             * Update parameter.
             * @param paramId Parameter id number.
             * @param paramValue New parameter value.
             * @return Returns true if parameter updated successfully.
             */
            bool updateParameter(unsigned int paramId, std::vector<uint8_t> & paramValue);

            /**
             * Calculates a hash of configuration parameters for comparison.
             * @return Returns vector of hash.
             */
            std::vector<uint8_t> calculateHash();
            
            /**
             * Hash platform specific configuration parameters
             */
            virtual void hashPlatformConfig(SHA_CTX & context) {};

            // *** Basic node parameters ***

            /**
             * Load success flag.
             */
            bool loadSuccess;

            /**
             * Type of node platform.
             */
            PlatformType platform;

            /**
             * Node ID number.
             */
            int nodeId;

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
            unsigned int hashSize;

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

            /**
             * Ground control system presence flag.
             */
            bool gcsPresent;

            /**
             * GCS node ID.
             */
            unsigned int gcsNodeId;

    };
}

#endif // NODE_NODE_CONFIG_HPP
