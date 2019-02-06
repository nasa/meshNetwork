#include "comm/msgParser.hpp"
#include <iostream>

using std::vector;

namespace comm {

    MsgParser::MsgParser(unsigned int parseMsgMaxIn) :
        parseMsgMax(parseMsgMaxIn)
    {};

    unsigned int MsgParser::parseSerialMsg(const vector<uint8_t> & msgBytes, unsigned int msgStart) {
        if (msgBytes.size() > 0) {
            parsedMsgs.push_back(std::vector<uint8_t>(msgBytes.begin() + msgStart, msgBytes.end()));
            return msgBytes.size();
        }

        return 0;
    }

    void MsgParser::parseMsgs(const vector<uint8_t> & msgBytes) {
        unsigned int msgEnd = 0;
        for (unsigned int i = 0; i < parseMsgMax; i++) {
            if (msgEnd < msgBytes.size()) {
                msgEnd = parseSerialMsg(msgBytes, msgEnd);
            }
            else {
                break;
            }
        } 
    }

    vector<uint8_t> MsgParser::encodeMsg(vector<uint8_t> msgBytes) {
        // Base class just returns inputted bytes
        return vector<uint8_t>(msgBytes.begin(), msgBytes.end());
    }

    bool MsgParser::getMsg(std::vector<uint8_t> & msg, unsigned int pos) {
        if (pos >= parsedMsgs.size()) { // position greater than number of parsed messages
            return false;
        }
        
        // Return and delete requested element
        msg = parsedMsgs[pos];
        parsedMsgs.erase(parsedMsgs.begin() + pos);
        return true;
    }
 
}
