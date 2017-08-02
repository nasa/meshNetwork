#include "comm/fpgaRadio.hpp"
#include "crc.hpp"
#include "SLIPMsg.hpp"
#include "utilities.hpp"

using std::vector;
namespace comm {

    FPGARadio::FPGARadio(serial::Serial * serialIn, RadioConfig & configIn) :
        SerialRadio(serialIn, configIn)
    {
    };

    unsigned int FPGARadio::sendMsg(vector<uint8_t> & msgBytes) {
        // Create message crc    
        crc_t crc = crc_create(msgBytes);

        // Add FPGA message header and crc to outgoing message
        vector<uint8_t> outMsg;
        outMsg.push_back(SLIP_END);
        outMsg.push_back(FPGA_MSG_START);
        uint16_t msgLength = msgBytes.size();
        std::vector<uint8_t> lengthBytes = util::packBytes(&msgLength, 2);
        outMsg.insert(outMsg.end(), lengthBytes.begin(), lengthBytes.end());
        outMsg.insert(outMsg.end(), msgBytes.begin(), msgBytes.end());
        crcToBytes(outMsg, crc);

        return SerialRadio::sendMsg(outMsg);

    }

}
