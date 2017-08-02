#include "comm/radio.hpp"

using std::vector;
namespace comm {
    Radio::Radio(RadioConfig & configIn) :
        mode(OFF),
        config(configIn)
    {
        rxBuffer.reserve(config.rxBufferSize);
    };

    bool Radio::setMode(RadioMode modeIn) {
        bool retValue = false;
        switch (modeIn) {
            case OFF:
                retValue = setOff();
                break;
            case SLEEP:
                retValue = setSleep();
                break;
            case RECEIVE:
                retValue = setReceive();
                break;
            case TRANSMIT:
                retValue = setTransmit();
                break;
        }

        return retValue;
    }

    bool Radio::setOff() {
        if (mode == OFF) {
            return false;
        }
        else {
            mode = OFF;
            return true;
        }
    }
    
    bool Radio::setSleep() {
        if (mode == SLEEP) {
            return false;
        }
        else {
            mode = SLEEP;
            return true;
        }
    }
    
    bool Radio::setReceive() {
        if (mode == RECEIVE) {
            return false;
        }
        else {
            mode = RECEIVE;
            return true;
        }
    }

    bool Radio::setTransmit() {
        if (mode == TRANSMIT) {
            return false;
        }
        else {
            mode = TRANSMIT;
            return true;
        }
    }
    
    void Radio::clearRxBuffer() {
        rxBuffer.clear();
    }
           
    int Radio::readBytes(bool bufferFlag, int bytesToRead) {
        return -1;
    }

    int Radio::processRxBytes(vector<uint8_t> & newBytes, bool bufferFlag) {
        return bufferRxMsg(newBytes, bufferFlag);
    }

    int Radio::bufferRxMsg(vector<uint8_t> & newBytes, bool bufferFlag) {
        if (newBytes.size() == 0) {
            return 0;
        }
        
        if (bufferFlag == true) { // Buffer new bytes
            if ((rxBuffer.size() + newBytes.size()) <= config.rxBufferSize) {
                rxBuffer.insert(rxBuffer.end(), newBytes.begin(), newBytes.end());
            }
            else { // Buffer full so discard bytes
                return -1;
            }
        }
        else { // Replace any existing bytes
            rxBuffer = newBytes;
        }   

        return newBytes.size(); // return size of newly stored bytes
    }

    vector<uint8_t> Radio::getRxBytes(void) {
        return rxBuffer;
    }

    void Radio::bufferTxMsg(vector<uint8_t> & msgBytes) {
        txBuffer.insert(txBuffer.end(), msgBytes.begin(), msgBytes.end());
    }

    unsigned int Radio::sendMsg(std::vector<uint8_t> & msgBytes) {
        return 0;
    }
            
    unsigned int Radio::sendMsg(Message & msg) {
        return 0;
    }

    vector<uint8_t> Radio::createMsg(vector<uint8_t> msgBytes) {
        return msgBytes;
    }

    unsigned int Radio::sendBuffer(unsigned int maxBytesToSend) {
        if (txBuffer.size() > 0) {
            if (maxBytesToSend > 0 && txBuffer.size() > maxBytesToSend) { // Too much data to send
                vector<uint8_t> msgBytes = vector<uint8_t>(txBuffer.begin(), txBuffer.begin() + maxBytesToSend);
                sendMsg(msgBytes);
                txBuffer.erase(txBuffer.begin(), txBuffer.begin() + maxBytesToSend); // clear sent bytes
                return 1; // partial buffer sent
            }
            else { // send entire tx buffer
                sendMsg(txBuffer);
                txBuffer.clear();
            }
        }

        return 0;
    }
}
