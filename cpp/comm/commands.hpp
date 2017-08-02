#ifndef COMM_COMMANDS_HPP
#define COMM_COMMANDS_HPP

#include "comm/commandSupport.hpp"
#include <unordered_map>
#include <string>
#include <vector>
#include <cstdint>

namespace comm {

    class Cmds {
        public:

            /*
             * Command ID to header type mapping.
             */
            static std::unordered_map<uint8_t, HeaderType> cmdDict;

            /*
             * Utility function to load command ID dictionaries.
             */
            static void updateCmdDict(std::unordered_map<uint8_t, HeaderType> & newDict);

            /*
             * Returns vector of all values in a command ID map.
             */
            //static std::vector<uint8_t> getCmds(std::map<std::string, uint8_t> & cmds);

            static std::vector<uint8_t> cmdsToRelay;
    };

//    struct CmdMessage {
//    };

}

#endif // COMM_COMMANDS_HPP
