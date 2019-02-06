#include "comm/serialComm.hpp"
#include "comm/exceptions.hpp"
#include "comm/utilities.hpp"
#include "comm/msgParser.hpp"
#include "node/nodeParams.hpp"
#include <algorithm>

using std::vector;

namespace comm {

    SerialComm::SerialComm(std::vector<MsgProcessor *> msgProcessorsIn, Radio * radioIn, MsgParser * msgParserIn) :
        radio(radioIn),
        msgParser(msgParserIn),
        msgProcessors(msgProcessorsIn),
        lastMsgSentTime(0.0),
        msgCounter(0)
    {
        // Check if radio provided
        if (radio == NULL) {
            // Radio must be provided - throw exception
            throw InvalidInputsException();
        }

        // Check if msg parser provided
        //if (msgParserIn == NULL) { 
        //    msgParser = std::unique_ptr<MsgParser>(new MsgParser(node::NodeParams::config.parseMsgMax)); // use default parser
        //}
        //else {
        //    msgParser = std::unique_ptr<MsgParser>(msgParserIn);
        //}
    }

    void SerialComm::execute() {};

    void SerialComm::sendMsg(vector<uint8_t> & msgBytes) {
        if (msgBytes.size() > 0 && msgParser != NULL) {
            // Update stored message stats
            lastMsgSentTime = util::getTime();
            msgCounter = (msgCounter + 1) % 256;
         
            // Encode and send message
            vector<uint8_t> msgOut = msgParser->encodeMsg(msgBytes);
            sendBytes(msgOut);
        }
    }

    void SerialComm::sendBuffer() {
        if (radio != NULL) {
            radio->sendBuffer();
        }
    }
    
    void SerialComm::readBytes(bool bufferFlag) {
        if (radio != NULL) {
            radio->readBytes(bufferFlag);
        }
    }

    unsigned int SerialComm::sendBytes(std::vector<uint8_t> & msgBytes) {
        if (radio != NULL) {
            return radio->sendMsg(msgBytes);
        }

        return 0; 

    }

    bool SerialComm::readMsgs() {
        // Read from radio
        readBytes(false);

        // Parse messages
        parseMsgs();

        return true;
    }

    void SerialComm::parseMsgs() {
        // Parse messages
        if (radio != NULL && msgParser != NULL) {
            msgParser->parseMsgs(radio->getRxBytes());
            
            // Clear radio rx buffer
            radio->clearRxBuffer();
        }
    }

    void SerialComm::bufferTxMsg(vector<uint8_t> & msgBytes) {
        if (msgBytes.size() > 0 && msgParser != NULL) {
            
            vector<uint8_t> msgOut = msgParser->encodeMsg(msgBytes);
            if (radio != NULL) {
                radio->bufferTxMsg(msgOut);
            }
        }
    }

    void SerialComm::processMsgs(MsgProcessorArgs & args) {
        readMsgs();
        
        if (msgParser != NULL) {
            std::vector<uint8_t> msg;
            
            unsigned int numMsgs = msgParser->parsedMsgs.size();
            for (unsigned int i = 0; i < numMsgs; i++) {
                msgParser->getMsg(msg);
                processMsg(msg, args);
            }
        }
    }   
    
    bool SerialComm::processMsg(vector<uint8_t> & msg, MsgProcessorArgs args) {

        if (msg.size() > 0) {
            // Check command id and pass to appropriate message processor
            uint8_t cmdId = msg[0]; // the command ID will be the first element in the message
            std::vector<uint8_t>::iterator it;
            for (unsigned int i = 0; i < msgProcessors.size(); i++) { // look for proper processor
                it = std::find(msgProcessors[i]->cmdIds.begin(), msgProcessors[i]->cmdIds.end(), cmdId);
                //for (unsigned int j = 0; j < msgProcessors[i]->cmdIds.size(); j++) {
                //}
                if (it != msgProcessors[i]->cmdIds.end()) { // cmd Id found
                    return msgProcessors[i]->processMsg(cmdId, msg, args); // processor command
                }
                    


                //std::vector<uint8_t>::iterator it;
                //it = std::find(MsgProcessors::cmdIdMappings[msgProcessors[i]].begin(), MsgProcessors::cmdIdMappings[msgProcessors[i]].end(), cmdId);
                //if (it != MsgProcessors::cmdIdMappings[msgProcessors[i]].end()) { // cmd Id found
                //    MsgProcessors::msgProcessorMap[msgProcessors[i]](5); // processor command
                //    return 1;
                //}
                
            }
        }
        
        return false; // no processor found
    }

    void SerialComm::processBuffers() {
        
        // Send command buffer
        for (auto i : cmdBuffer) {
            bufferTxMsg(i.second);
        } 
        //for (unsigned int i = 0; i < cmdBuffer.size(); i++) { 
        //    bufferTxMsg(cmdBuffer[i]);
        //}
        cmdBuffer.clear();

        // Send command relay buffer
        if (cmdRelayBuffer.size() > 0) {
            radio->bufferTxMsg(cmdRelayBuffer);
            cmdRelayBuffer.clear();
        }         
    }

}
