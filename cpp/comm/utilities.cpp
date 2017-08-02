#include "utilities.hpp"
    
namespace util {
    void setupSerial(serial::Serial & ser, std::string port, unsigned int baudrate, unsigned int timeout) {
        serial::Timeout sTimeout = serial::Timeout::simpleTimeout(timeout);
        ser.setPort(port);
        ser.setBaudrate(baudrate);
        ser.setTimeout(sTimeout);
        ser.open();

    }

    std::vector<uint8_t> packBytes(void * data, unsigned int dataSize) {
        uint8_t buf[dataSize];
        memcpy(buf, data, dataSize);
        return std::vector<uint8_t>(buf, buf + sizeof(buf));
    }
    
}
