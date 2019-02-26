#include "comm/fpgaRadio.hpp"
#include "crc_16.hpp"
#include "SLIPMsg.hpp"
#include "utilities.hpp"

using std::vector;
namespace comm {

    FPGARadio::FPGARadio(serial::Serial * serialIn, RadioConfig & configIn) :
        Radio(serialIn, configIn)
    {
    };

    unsigned int FPGARadio::sendMsg(vector<uint8_t> & msgBytes) {
        // Create message crc    
        crc16_t crc = crc16_create(msgBytes);

        // Add FPGA message header and crc to outgoing message
        vector<uint8_t> outMsg;
        outMsg.push_back(SLIP_END);
        outMsg.push_back(FPGA_MSG_START);
        uint16_t msgLength = msgBytes.size();
        std::vector<uint8_t> lengthBytes = util::packBytes(&msgLength, 2);
        outMsg.insert(outMsg.end(), lengthBytes.begin(), lengthBytes.end());
        outMsg.insert(outMsg.end(), msgBytes.begin(), msgBytes.end());
        util::variableToSerialBytes(outMsg, crc);

        return Radio::sendMsg(outMsg);

    }

}
