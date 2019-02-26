#include "comm/SLIPMsgParser.hpp"
#include "crc.hpp"
#include "utilities.hpp"
#include <iostream> 

using std::vector;

namespace comm {

    SLIPMsgParser::SLIPMsgParser(unsigned int parseMsgMaxIn, unsigned int SLIPMaxLength) :
        MsgParser(parseMsgMaxIn),
        slipMsg(SLIPMsg(SLIPMaxLength))
    {
    };

    unsigned int SLIPMsgParser::parseSerialMsg(const vector<uint8_t> & msgBytes, unsigned int msgStart) {
        if (msgBytes.size() < 0) { // no message bytes
            return 0;
        }

        if (slipMsg.decodeSLIPMsg(msgBytes, msgStart) == true && slipMsg.msg.size() >= sizeof(crc8_t)) { // minimum size should be crc length
            // Compare CRC
            vector<uint8_t> msgOnly = vector<uint8_t>(slipMsg.msg.begin(), slipMsg.msg.end()-sizeof(crc8_t));
            crc8_t crc = crc8_create(msgOnly);
            crc8_t msgCrc;
            util::serialBytesToVariable(slipMsg.msg, slipMsg.msg.size()-sizeof(msgCrc), &msgCrc);
            if (crc == msgCrc) {
                // Add message to parsed messages
                parsedMsgs.push_back(msgOnly);
            }
            return slipMsg.msgEnd;
        } 
        return msgBytes.size(); // no message found - return length of parsed bytes
    }

    vector<uint8_t> SLIPMsgParser::encodeMsg(vector<uint8_t> msgBytes) {
        if (msgBytes.size() > 0) {
            // Add CRC    
            crc8_t crc = crc8_create(msgBytes);
            util::variableToSerialBytes(msgBytes, crc);
            //msgBytes.push_back((uint8_t)((crc & 0xFF00) >> 8));
            //msgBytes.push_back((uint8_t)((crc & 0x00FF)));
            return slipMsg.encodeSLIPMsg(msgBytes);

        }

        return vector<uint8_t>(); // no message

    }

}
