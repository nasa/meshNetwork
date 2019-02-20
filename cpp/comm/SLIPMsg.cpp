#include "comm/SLIPMsg.hpp"
#include <iostream>

using std::vector;

namespace comm {
            
    SLIPMsg::SLIPMsg() : 
        maxLength(SLIP_MAX_LENGTH),
        msgFound(false),
        msgEnd(0),
        msgLength(0)
    {}

    SLIPMsg::SLIPMsg(unsigned int maxLengthIn) :
        maxLength(maxLengthIn),
        msgFound(false),
        msgEnd(0),
        msgLength(0)
    {}

    bool SLIPMsg::decodeSLIPMsg(const vector<uint8_t> & bytes, unsigned int msgStart) {
        if (bytes.size() == 0) {
            return false;
        }
        
        if (msgFound == true) {
            if (msgEnd != 0) { // Clear previous message results
                msg.clear();
                msgLength = 0;
                msgFound = false;
                msgEnd = 0;
                buffer.clear();
            }
            else { // partial message found
                if (buffer.size() > 0) { // bytes in waiting in buffer
                    std::vector<uint8_t> msgBytes;
                    msgBytes.insert(msgBytes.end(), buffer.begin(), buffer.end());
                    msgBytes.insert(msgBytes.end(), bytes.begin() + msgStart, bytes.end());
                    buffer.clear();
                    return decodeSLIPMsgContents(msgBytes, 0);
                }
                else {
                    return decodeSLIPMsgContents(bytes, 0);
                }
            }
        }

        for (unsigned int i = msgStart; i < bytes.size(); i++) {
            if (bytes[i] == SLIP_END) { // message start found
                msgFound = true;
                return decodeSLIPMsgContents(bytes, i + 1);
            }
        }

        return false;
    }
        
    bool SLIPMsg::decodeSLIPMsgContents(const vector<uint8_t> & bytes, unsigned int pos) {
        while (pos < bytes.size() && msg.size() < maxLength) {
            // Parse message contents
            if (bytes[pos] != SLIP_END) {
                //if ((bytes[pos] == SLIP_ESC) && (pos + 1) < bytes.size()) { // ESC character found
                if (bytes[pos] == SLIP_ESC) { // ESC character found
                    if ((pos + 1) < bytes.size()) { // remainder of ESC sequence available
                        if (bytes[pos+1] == SLIP_ESC_END) { // replace ESC sequence with END character
                            msg.push_back(SLIP_END);
                        }
                        else if (bytes[pos+1] == SLIP_ESC_END_TDMA) { // replace with TDMA END character
                            msg.push_back(SLIP_END_TDMA);
                        }
                        else { // replace with ESC character
                            msg.push_back(SLIP_ESC);
                        }

                        pos++;
                    }
                    else { // Add partial sequence to buffer and return
                        buffer.push_back(bytes[pos]);
                        return false;
                    }
                }  
                else { // insert raw byte
                    msg.push_back(bytes[pos]);
                }

                msgLength++;
            }
            else { // message end found
                msgEnd = pos + 1;
                return true;
            }

            pos++; 
        }

        return false;
    }
        
    vector<uint8_t> SLIPMsg::encodeSLIPMsg(const vector<uint8_t> & bytes) {
        vector<uint8_t> encodedMsg;
    
        // Check for empty message
        if (bytes.size() == 0) {
            return encodedMsg;
        }

        encodedMsg.push_back(SLIP_END);
        for (unsigned int i = 0; i < bytes.size(); i++) {
            // Look for control characters
            if (bytes[i] == SLIP_END) {
                encodedMsg.push_back(SLIP_ESC);        
                encodedMsg.push_back(SLIP_ESC_END);        
            }
            else if (bytes[i] == SLIP_ESC) {
                encodedMsg.push_back(SLIP_ESC);        
                encodedMsg.push_back(SLIP_ESC_ESC);        
            }
            else if (bytes[i] == SLIP_END_TDMA) {
                encodedMsg.push_back(SLIP_ESC);        
                encodedMsg.push_back(SLIP_ESC_END_TDMA);
            } 
            else { // insert raw byte
                encodedMsg.push_back(bytes[i]);
            }       
        }
        encodedMsg.push_back(SLIP_END);
         
        return encodedMsg;
    }
}
