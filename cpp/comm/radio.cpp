#include "comm/radio.hpp"
#include <iostream>
using std::vector;
namespace comm {
    Radio::Radio(serial::Serial * serialIn, RadioConfig & configIn) :
        mode(RADIO_OFF),
        config(configIn),
        serial(serialIn)
    {
        rxBuffer.reserve(config.rxBufferSize);
    };

    bool Radio::setMode(RadioMode modeIn) {
        bool retValue = false;
        switch (modeIn) {
            case RADIO_OFF:
                retValue = setOff();
                break;
            case RADIO_SLEEP:
                retValue = setSleep();
                break;
            case RADIO_RECEIVE:
                retValue = setReceive();
                break;
            case RADIO_TRANSMIT:
                retValue = setTransmit();
                break;
        }

        return retValue;
    }

    bool Radio::setOff() {
        if (mode == RADIO_OFF) {
            return false;
        }
        else {
            mode = RADIO_OFF;
            return true;
        }
    }
    
    bool Radio::setSleep() {
        if (mode == RADIO_SLEEP) {
            return false;
        }
        else {
            mode = RADIO_SLEEP;
            return true;
        }
    }
    
    bool Radio::setReceive() {
        if (mode == RADIO_RECEIVE) {
            return false;
        }
        else {
            mode = RADIO_RECEIVE;
            return true;
        }
    }

    bool Radio::setTransmit() {
        if (mode == RADIO_TRANSMIT) {
            return false;
        }
        else {
            mode = RADIO_TRANSMIT;
            return true;
        }
    }
    
    void Radio::clearRxBuffer() {
        rxBuffer.clear();
    }
           
    int Radio::readBytes(bool bufferFlag) {
        // Attempt to read serial bytes
        vector<uint8_t> newBytes;
        serial->read(newBytes, config.numBytesToRead);
       
        // Process received bytes
        if (newBytes.size() > 0) {
            processRxBytes(newBytes, bufferFlag);
        }

        return newBytes.size();
    }
            
    void Radio::sendBytes(std::vector<uint8_t> msgBytes) {
        serial->write(msgBytes);
    }


    int Radio::processRxBytes(vector<uint8_t> & newBytes, bool bufferFlag) {
        // Base class just adds received bytes to the buffer.
        return bufferRxMsg(newBytes, bufferFlag);
    }

    int Radio::bufferRxMsg(vector<uint8_t> & newBytes, bool bufferFlag) {
        if (newBytes.size() == 0) {
            return 0;
        }
        
        if (bufferFlag == true) { // Buffer new bytes
            if ((rxBuffer.size() + newBytes.size()) <= config.rxBufferSize) {
                rxBuffer.insert(rxBuffer.end(), newBytes.begin(), newBytes.end());
                return newBytes.size();
            }
            else { // Buffer full so discard bytes
                return -1;
            }
        }
        else { // Replace any existing bytes
            rxBuffer = newBytes;
            return newBytes.size();
        }   

    }

    vector<uint8_t> Radio::getRxBytes(void) {
        return rxBuffer;
    }

    unsigned int Radio::sendMsg(vector<uint8_t> & msgBytes) {
        if (msgBytes.size() > 0) {
            return serial->write(createMsg(msgBytes));
        }

        return 0; // no data sent
    }
    
    void Radio::bufferTxMsg(vector<uint8_t> & msgBytes) {
        txBuffer.insert(txBuffer.end(), msgBytes.begin(), msgBytes.end());
    }

    unsigned int Radio::sendMsg(Message & msg) {
        return 0;
    }

    vector<uint8_t> Radio::createMsg(vector<uint8_t> msgBytes) {
        // Base class just passes through raw bytes
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

    void Radio::sendCommand(std::vector<uint8_t> cmd) {
        
    }
}
