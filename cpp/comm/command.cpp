#include "comm/command.hpp"
#include "comm/commands.hpp"
#include "comm/utilities.hpp"
#include <iostream>      
#include <cstring>
#include <vector>

using std::vector;

namespace comm {      
    Command::Command() : // empty command
        cmdId(0)
    {}
    
    Command::Command(uint8_t cmdIdIn) :
        cmdId(cmdIdIn),
        timestamp(util::getTime())
    {
        // Attempt to determine header type
        if (Cmds::cmdDict.find(cmdId) != Cmds::cmdDict.end()) { // command ID found
            header.type = Cmds::cmdDict[cmdId];
        }
    }

    Command::Command(uint8_t cmdIdIn, CmdHeader headerIn, double txIntervalIn) :
        cmdId(cmdIdIn),
        header(headerIn),
        lastTxTime(0.0),
        txInterval(txIntervalIn),
        timestamp(util::getTime())
    {}
            
    Command::Command(vector<uint8_t> packedIn, double txIntervalIn) :
        txInterval(txIntervalIn),
        packed(packedIn)
    {
        // Attempt to parse header
        unpackHeader(packedIn, HEADER_UNKNOWN, header);
    }

    vector<uint8_t> Command::serialize() {
        return vector<uint8_t>();
    }
        
    vector<uint8_t> Command::pack(double timestamp) {
        lastTxTime = timestamp;

        // Insert header
        vector<uint8_t> cmd = header.packHeader();

        // Insert command data
        vector<uint8_t> cmdData = serialize();
        cmd.insert(cmd.end(), cmdData.begin(), cmdData.end());

        packed = cmd; // stored packed data
        return cmd;        
    }
        
    vector<uint8_t> Command::packData(void * data, unsigned int dataSize) {
        uint8_t buf[dataSize];
        memcpy(buf, data, dataSize);
        return vector<uint8_t>(buf, buf + sizeof(buf));
    }
    
    void Command::packData(void * data, unsigned int dataSize, vector<uint8_t> & packed) {
        uint8_t buf[dataSize];
        memcpy(buf, data, dataSize);
        vector<uint8_t> newData(buf, buf + sizeof(buf));
        packed.insert(packed.end(), newData.begin(), newData.end());
    }
    
}
