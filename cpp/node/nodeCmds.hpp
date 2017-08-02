#ifndef COMM_NODE_COMMANDS_HPP
#define COMM_NODE_COMMANDS_HPP

#include <vector>
#include <string>
#include <cstdint>
#include <unordered_map>
#include "comm/cmdHeader.hpp"
#include "comm/command.hpp"
#include "node/nodeParams.hpp"
#include "node/nodeConfigSupport.hpp"

namespace node {

    class NodeCmds {
        public:
            /*
             * Allowed Node command IDs.
             */
            enum {
                GCSCmd = 10,
                FormationCmd = 20,
                ParamUpdate = 30,
                ConfigRequest = 40,
                ConfigHash = 50
            };

            /*
             * Container of all Node command IDs.
             */
            static std::vector<uint8_t> cmds;

            /*
             * Command ID to header type mapping.
             */
            static std::unordered_map<uint8_t, comm::HeaderType> cmdDict;
    };
    
    class Node_GCSCmd : public comm::Command {
        public: 
        
            /**
             * Commanded mode.
             */
            FormationMode mode;

            /**
             * Primary constructor.
             * @param modeIn Mode command.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            Node_GCSCmd(FormationMode modeIn, comm::CmdHeader header, double txInterval = NodeParams::config.cmdInterval);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            Node_GCSCmd(std::vector<uint8_t> & msg);

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();
    };

    class Node_ParamUpdate : public comm::Command {
        public: 
        
            /**
             * Parameter name
            */
            ParamName name;
    
            /**
             * Parameter value.
            */
            std::vector<uint8_t> value;

            /**
             * Primary constructor.
             * @param nameIn Parameter name.
             * @param valueIn Parameter value.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            Node_ParamUpdate(ParamName nameIn, std::vector<uint8_t> valueIn, comm::CmdHeader header, double txInterval = NodeParams::config.cmdInterval);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            Node_ParamUpdate(std::vector<uint8_t> & msg);

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();
    };
        
    class Node_ConfigRequest : public comm::Command {
        public: 
        
            /**
             * Configuration hash
            */
            std::string hash;

            /**
             * Primary constructor.
             * @param hashIn Configuration hash.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            Node_ConfigRequest(std::string hash, comm::CmdHeader header, double txInterval = NodeParams::config.cmdInterval);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            Node_ConfigRequest(std::vector<uint8_t> & msg);

            /**
             * Command serialization method.
             * @return Returns serialized command for transmission.
             */
            virtual std::vector<uint8_t> serialize();
    };
        
}
#endif // COMM_NODE_COMMANDS_HPP
