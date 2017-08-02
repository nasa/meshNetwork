#include "comm/serialRadio.hpp"

using std::vector;
namespace comm {

    SerialRadio::SerialRadio(serial::Serial * serialIn, RadioConfig & configIn) :
        Radio(configIn),
        serial(serialIn)
    {
    };

    int SerialRadio::readBytes(bool bufferFlag, int bytesToRead) {
        // Attempt to read serial bytes
        vector<uint8_t> newBytes;
        serial->read(newBytes, bytesToRead);
        
        // Process received bytes
        if (newBytes.size() > 0) {
            return processRxBytes(newBytes, bufferFlag);
        }

        return 0;
    }

    unsigned int SerialRadio::sendMsg(vector<uint8_t> & msgBytes) {
        if (msgBytes.size() > 0) {
            serial->write(createMsg(msgBytes));
        }

        return 1; // number of messages sent
    }

}
