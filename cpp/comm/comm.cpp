#include "comm/comm.hpp"
#include "comm/exceptions.hpp"
#include "comm/utilities.hpp"

using std::vector;

namespace comm {

    Comm::Comm(CommProcessor * commProcessorIn, Radio * radioIn, MsgParser * msgParserIn) :
        radio(radioIn),
        msgParser(msgParserIn),
        commProcessor(commProcessorIn),
        lastMsgSentTime(0.0),
        msgCounter(0)
    {
        // Check if radio provided
        if (radio == NULL) {
            // Radio must be provided - throw exception
            throw InvalidInputsException();
        }
    }

    void Comm::execute() {};

    void Comm::sendMsg(vector<uint8_t> & msgBytes) {
        if (msgBytes.size() > 0) {
            // Update stored message stats
            lastMsgSentTime = util::getTime();
            msgCounter = (msgCounter + 1) % 256;
         
            // Encode and send message
            vector<uint8_t> msgOut = msgParser->encodeMsg(msgBytes);
            
            if (radio != NULL) {
                radio->sendMsg(msgOut);
            }
        }
    }

    void Comm::sendBuffer() {
        if (radio != NULL) {
            radio->sendBuffer();
        }
    }
    
    void Comm::readBytes(bool bufferFlag) {
        if (radio != NULL) {
            radio->readBytes(bufferFlag);
        }
    }

    void Comm::sendBytes(std::vector<uint8_t> & msgBytes) {
        if (radio != NULL) {
            radio->sendMsg(msgBytes);
        }
    }

    void Comm::readMsgs() {
        // Read from radio
        readBytes(false);

        // Parse messages
        parseMsgs();
    }

    void Comm::parseMsgs() {
        // Parse messages
        if (msgParser != NULL) {
            msgParser->parseMsgs(radio->getRxBytes());
        }

        // Clear radio rx buffer
        if (radio != NULL) {
            radio->clearRxBuffer();
        }
        
    }

    void Comm::bufferTxMsg(vector<uint8_t> & msgBytes) {
        if (msgBytes.size() > 0) {
            vector<uint8_t> msgOut = msgParser->encodeMsg(msgBytes);
            
            if (radio != NULL) {
                radio->bufferTxMsg(msgOut);
            }
        }
    }

    int Comm::processMsg(vector<uint8_t> & msg, MsgProcessorArgs & args) {
        if (commProcessor != NULL) {
            return commProcessor->processMsg(msg, args);
        }
            
        return -1;

    }

    void Comm::processMsgs(MsgProcessorArgs & args) {
        readMsgs();
        
        if (msgParser != NULL) {
            std::vector<uint8_t> msg;
            for (unsigned int i = 0; i < msgParser->parsedMsgs.size(); i++) {
                msgParser->getMsg(msg);
                processMsg(msg, args);
            }
        }
    }   
}
