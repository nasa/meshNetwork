#ifndef COMM_NODE_COMMANDS_HPP
#define COMM_NODE_COMMANDS_HPP

#include <vector>
#include <cstdint>
#include <unordered_map>
#include "comm/command.hpp"
#include "comm/cmdHeader.hpp"
#include "node/nodeState.hpp"
#include "node/nodeParams.hpp"
#include "node/nodeConfigSupport.hpp"

namespace comm {
    
    namespace NodeCmds {
        //public:
            /*
             * Allowed Node command IDs.
             */
            enum {
                NoOp = 0,
                GCSCmd = 10,
                ParamUpdate = 30,
                ConfigRequest = 40
            };

            /*
             * Container of all Node command IDs.
             */
            extern std::vector<uint8_t> cmds;

            /*
             * Command ID to header type mapping.
             */
            extern std::unordered_map<uint8_t, comm::HeaderType> cmdDict;

            std::unordered_map<uint8_t, comm::HeaderType> getCmdDict();
            std::vector<uint8_t> getCmds();
    };


    class Node_NoOp : public Command {
        public:
            Node_NoOp() {};
            /**
             * Primary constructor.
             */
            Node_NoOp(CmdHeader header, double txInterval = 0.0);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            Node_NoOp(std::vector<uint8_t> & msg);

            /**
             * Command body serialization method.
             * @return Returns serialized command body bytes.
             */
            virtual std::vector<uint8_t> packBody();
            
            /**
             * Checks if raw bytes are valid command.
             * @param msgBytes Raw message bytes.
             */ 
            static bool isValid(std::vector<uint8_t> & msgBytes);
    };
    
    class Node_GCSCmd : public Command {
        public:

            /**
             * Destination node id.
             */
            uint8_t destId;

            /**
             * Mode command.
             */
            uint8_t mode;

            /**
             * Primary constructor.
             * @param destIdIn Destination node id.
             * @param modeIn Mode command.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            Node_GCSCmd(uint8_t destId, uint8_t mode, CmdHeader header, double txInterval = 0.0);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            Node_GCSCmd(std::vector<uint8_t> & msg);

            /**
             * Command body serialization method.
             * @return Returns serialized command body bytes.
             */
            virtual std::vector<uint8_t> packBody();
           
            /**
             * Checks if raw bytes are valid command.
             * @param msgBytes Raw message bytes.
             */ 
            static bool isValid(std::vector<uint8_t> & msgBytes);
    };

    class Node_ConfigRequest : public Command {
        public:

            /**
             * Configuration hash.
             */
            std::vector<uint8_t> configHash;

            /**
             * Primary constructor.
             * @param configHashIn Configuration hash.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            Node_ConfigRequest(std::vector<uint8_t> & configHashIn, CmdHeader header, double txInterval = 0.0);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            Node_ConfigRequest(std::vector<uint8_t> & msg);

            /**
             * Command body serialization method.
             * @return Returns serialized command body bytes.
             */
            virtual std::vector<uint8_t> packBody();
            
            /**
             * Checks if raw bytes are valid command.
             * @param msgBytes Raw message bytes.
             */ 
            static bool isValid(std::vector<uint8_t> & msgBytes);
    };

    class Node_ParamUpdate : public Command {
        public:

            /**
             * Destination node id.
             */
            uint8_t destId;

            /**
             * Parameter id.
             */
            uint8_t paramId;

            /**
             * Length of parameter value data.
             */
            uint8_t dataLength;
            
            /**
             * Parameter value raw data bytes.
             */
            std::vector<uint8_t> paramValue;

            /**
             * Primary constructor.
             * @param destIdIn Destination node id.
             * @param paramIdIn Parameter id.
             * @param dataLengthIn Length of parameter value data.
             * @param paramValue Raw parameter bytes.
             * @param header Command header.
             * @param txInterval Command re-transmit interval.
             */
            Node_ParamUpdate(uint8_t destIdIn, uint8_t paramIdIn, uint8_t dataLengthIn, std::vector<uint8_t> & paramValueIn, CmdHeader header, double txInterval = 0.0);

            /**
             * Parsing constructor for creating command from message bytes.
             * @param msg Raw message bytes.
             */
            Node_ParamUpdate(std::vector<uint8_t> & msg); // Parsing constructor

            /**
             * Command body serialization method.
             * @return Returns serialized command body bytes.
             */
            virtual std::vector<uint8_t> packBody();

            /**
             * Checks if raw bytes are valid command.
             * @param msgBytes Raw message bytes.
             */ 
            static bool isValid(std::vector<uint8_t> & msgBytes);
    };

}

#endif // COMM_NODE_COMMANDS_HPP
