#include "comm/commands.hpp"
#include "comm/tdmaCmds.hpp"

using std::unordered_map;
using std::string;
using std::vector;

namespace comm {

        std::unordered_map<uint8_t, HeaderType> Cmds::cmdDict;

            
        void Cmds::updateCmdDict(std::unordered_map<uint8_t, HeaderType> & newDict) {
            Cmds::cmdDict.insert(newDict.begin(), newDict.end());
        }
            

        // Commands to relay
        std::vector<uint8_t> Cmds::cmdsToRelay = {TDMACmds::BlockTxRequest, TDMACmds::BlockTxRequestResponse, TDMACmds::BlockTxConfirmed, TDMACmds::BlockTxStatus}; 

        /*vector<uint8_t> Cmds::getCmds(map<string, uint8_t> & cmds) {
            vector<uint8_t> out;

            for (map<string, uint8_t>::iterator it = cmds.begin(); it != cmds.end(); it++) {
                out.push_back(it->second);
            }

            return out;
        }*/
}
