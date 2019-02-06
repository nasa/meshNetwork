#include "comm/li1Radio.hpp"
#include "comm/checksum.hpp"
#include "comm/utilities.hpp"
#include <math.h>

using std::vector;



namespace comm {
    
    // Static members
    vector<uint8_t> Li1Radio::syncBytes = {72, 101}; // 'He'
    unsigned int Li1Radio::lenSyncBytes = Li1Radio::syncBytes.size();
    unsigned int Li1Radio::headerLength = 8;
    unsigned int Li1Radio::checksumLen = 2;
    unsigned int Li1Radio::maxPayload = 255;

    Li1Radio::Li1Radio() : 
        Radio(),
        cmdBuffer(CommBuffer<Li1Cmd>(5)),
        bigendian(util::isbigendian())
    {
        cmdRxBuffer.reserve(config.cmdRxBufferSize);
    }

    Li1Radio::Li1Radio(serial::Serial * serialIn, RadioConfig & configIn) :
        Radio(serialIn, configIn),
        cmdBuffer(CommBuffer<Li1Cmd>(5)),
        bigendian(util::isbigendian())
    {
        cmdRxBuffer.reserve(config.cmdRxBufferSize);
    }

    void Li1Radio::createHeader(Li1Cmd & cmd) {
        // Start with sync bytes
        vector<uint8_t> headerBytes = Li1Radio::syncBytes;
        if (bigendian == true) {
            // Add command type (big-endian)
            headerBytes.push_back((uint8_t)(cmd.type & 0x00FF));
            headerBytes.push_back((uint8_t)((cmd.type & 0xFF00) >> 8));
            // Add payload size (big-endian)
            headerBytes.push_back((uint8_t)(cmd.payload.size() & 0x00FF));
            headerBytes.push_back((uint8_t)((cmd.payload.size() & 0xFF00) >> 8));
        }
        else {
            // Add command type (big-endian)
            headerBytes.push_back((uint8_t)((cmd.type & 0xFF00) >> 8));
            headerBytes.push_back((uint8_t)(cmd.type & 0x00FF));
            // Add payload size (big-endian)
            headerBytes.push_back((uint8_t)((cmd.payload.size() & 0xFF00) >> 8));
            headerBytes.push_back((uint8_t)(cmd.payload.size() & 0x00FF));
        }   
        // Append checksum
        vector<uint8_t> checksum = calculate8bitFletcherChecksum(vector<uint8_t>(headerBytes.begin()+Li1Radio::lenSyncBytes, headerBytes.end()));
        headerBytes.insert(headerBytes.end(), checksum.begin(), checksum.end());
        // Add to message bytes
        cmd.msgBytes.insert(cmd.msgBytes.end(), headerBytes.begin(), headerBytes.end());
    }
    
    void Li1Radio::createPayload(Li1Cmd & cmd) {
        if (cmd.payload.size() > 0) {
            // Append payload bytes
            cmd.msgBytes.insert(cmd.msgBytes.end(), cmd.payload.begin(), cmd.payload.end());
            // Append checksum
            vector<uint8_t> checksum = calculate8bitFletcherChecksum(vector<uint8_t>(cmd.msgBytes.begin()+Li1Radio::lenSyncBytes, cmd.msgBytes.end()));
            cmd.msgBytes.insert(cmd.msgBytes.end(), checksum.begin(), checksum.end());
        }
    }
    
    void Li1Radio::createCommand(Li1Cmd & cmd) {
        // Create command elements
        createHeader(cmd);
        createPayload(cmd);
    }
    
    vector<uint8_t> Li1Radio::createMsg(vector<uint8_t> msgBytes) {
        // Create command
        Li1Cmd cmd(LI1_TRANSMIT, msgBytes);
        createCommand(cmd);

        // Return raw command bytes
        return cmd.msgBytes;
    }
    
    bool Li1Radio::parseCmdHeader(Li1Cmd & cmd, const vector<uint8_t> serBytes) {
        // Header components
        vector<uint8_t> headerBytes = vector<uint8_t>(serBytes.begin(), serBytes.begin() + Li1Radio::headerLength);    
        vector<uint8_t> cmdInfo = vector<uint8_t>(headerBytes.begin() + Li1Radio::lenSyncBytes, headerBytes.end() - Li1Radio::checksumLen);
        vector<uint8_t> checksumBytes = vector<uint8_t>(headerBytes.end() - Li1Radio::checksumLen, headerBytes.end());       
        // Check header checksum
        if (compareChecksum(cmdInfo, checksumBytes) == true) { // valid checksum
            cmd.header = cmdInfo;
            cmd.rawHeader = vector<uint8_t>(headerBytes.begin() + Li1Radio::lenSyncBytes, headerBytes.end());
            cmd.type = ((uint16_t)cmd.header[0] << 8) | cmd.header[1]; // parse command type value
            return true;
        }
        return false;
    }
            
    unsigned int Li1Radio::parseCmdPayload(Li1Cmd & cmd, unsigned int payloadSize, const vector<uint8_t> & serBytes) {
        if (serBytes.size() >= (payloadSize + Li1Radio::checksumLen)) {
            // Check payload checksum
            vector<uint8_t> payloadBytes = vector<uint8_t>(serBytes.begin(), serBytes.begin() + payloadSize);
            vector<uint8_t> headerAndPayload = cmd.rawHeader;
            headerAndPayload.insert(headerAndPayload.end(), payloadBytes.begin(), payloadBytes.end());
            vector<uint8_t> payloadChecksum = vector<uint8_t>(serBytes.begin() + payloadSize, serBytes.begin() + (payloadSize + Li1Radio::checksumLen));    
            
            if (compareChecksum(headerAndPayload, payloadChecksum) == true) {
                cmd.payload = parseAX25Msg(payloadBytes);
            }
            return payloadSize + Li1Radio::checksumLen;
        }
        else { // incomplete command - too short
            return serBytes.size();
        }
    }
            
    vector<uint8_t> Li1Radio::parseAX25Msg(vector<uint8_t> & msgBytes) {
        return vector<uint8_t>(msgBytes.begin()+16, msgBytes.end()-2);
    }
            
    unsigned int Li1Radio::parseCommand(Li1Cmd & cmd, vector<uint8_t> & serBytes) {
        cmd.valid = false; 

        for (unsigned int i = 0; i < (serBytes.size() - (Li1Radio::lenSyncBytes-1)); i++) {
            // Search for sync characters
            if (serBytes[i] == Li1Radio::syncBytes[0] && serBytes[i+1] == Li1Radio::syncBytes[1]) {
                unsigned int msgStart = i;
            
                bool headerFound = false;
                if ((serBytes.size() - msgStart) >= Li1Radio::headerLength) { // entire header received
                    headerFound = parseCmdHeader(cmd, vector<uint8_t>(serBytes.begin() + msgStart, serBytes.end()));
                }
                else { // incomplete command
                    return serBytes.size();
                }

                unsigned int msgEnd = msgStart + Li1Radio::headerLength; // update buffer position
                if (headerFound == true) {
                    // Check for payload
                    if (cmd.type == LI1_RECEIVED_DATA) {
                        unsigned int payloadSize = ((uint16_t)cmd.header[2] << 8) | cmd.header[3]; // reverse payload size bytes 
                        if (payloadSize == 0) { // no payload
                            cmd.valid = true;
                            return msgEnd;
                        }
                        else if (payloadSize == 65535) { // receive error status
                            cmd.valid = true;
                            return msgEnd;
                        }
                        else { // parse payload
                            if (serBytes.size() >= (Li1Radio::headerLength + payloadSize + Li1Radio::checksumLen)) { // entire message received
                                unsigned int payloadEnd = parseCmdPayload(cmd, payloadSize, vector<uint8_t>(serBytes.begin() + msgStart + Li1Radio::headerLength, serBytes.end()));
                                msgEnd += payloadEnd;
                                if (cmd.payload.size() > 0) { // payload found
                                    cmd.valid = true;
                                    return msgEnd;
                                }
                                else {
                                    return msgEnd; // return with invalid cmd flag
                                }
                            }
                            else {
                                return serBytes.size();
                            }
                        }
                    }
                    else { // header only valid command
                        cmd.valid = true;
                        return msgEnd;  
                    }
                }
                else { // invalid header
                    return msgEnd;
                }
            }
        }
                    
        return serBytes.size();
    }
            
    unsigned int Li1Radio::sendMsg(vector<uint8_t> & msgBytes) {
        if (msgBytes.size() > 0) {
            unsigned int numMsgs = ceil(msgBytes.size() / (double)Li1Radio::maxPayload);
            for (unsigned int i = 0; i < numMsgs; i++) {
                // End of message location
                unsigned int msgEnd = 0;
                if (msgBytes.size() > ((i+1)*Li1Radio::maxPayload)) {    
                    msgEnd = (i+1)*Li1Radio::maxPayload;
                }
                else {
                    msgEnd = msgBytes.size();
                }
                
                // Send message
                vector<uint8_t> payload = vector<uint8_t>(msgBytes.begin() + i*Li1Radio::maxPayload, msgBytes.begin() + msgEnd);
                Radio::sendMsg(payload);
                
            }
            return numMsgs;
        }

        return 0;
    }
    
    int Li1Radio::processRxBytes(vector<uint8_t> & newBytes, bool bufferFlag) {
        Li1Cmd cmd;
        
        // Search received bytes for commands
        cmdRxBuffer.insert(cmdRxBuffer.end(), newBytes.begin(), newBytes.end());
        unsigned int msgEnd = 0;
        unsigned int loopCtr = 0;
        while (msgEnd < cmdRxBuffer.size() && loopCtr < 5) {
            msgEnd = parseCommand(cmd, cmdRxBuffer);
        
            if (cmd.valid == true) { // command found
                cmdRxBuffer = vector<uint8_t>(cmdRxBuffer.begin() + msgEnd, cmdRxBuffer.end()); // clear out parsed bytes
                cmdBuffer.push(cmd); // add to parsed command buffer
                
                // Check for received data
                if (cmd.type == LI1_RECEIVED_DATA && cmd.payload.size() > 0) {
                    bufferRxMsg(cmd.payload, bufferFlag);
                }
            }
        }

        if (cmdRxBuffer.size() > config.cmdRxBufferSize) { // buffer too large, clear buffer
            cmdRxBuffer.clear();
        } 
        return 0;
    }
}
