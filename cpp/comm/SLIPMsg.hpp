#ifndef COMM_SLIP_MSG_HPP
#define COMM_SLIP_MSG_HPP

#include <string>
#include <vector>
#include <cstdint>

#include "comm/defines.hpp"
#include <serial/serial.h>

namespace comm {

    // SLIP pre-defined byte definitions.
    static const uint8_t SLIP_END = 192;
    static const uint8_t SLIP_ESC = 219;
    static const uint8_t SLIP_END_TDMA = 193;
    static const uint8_t SLIP_ESC_END = 220;
    static const uint8_t SLIP_ESC_ESC = 221;
    static const uint8_t SLIP_ESC_END_TDMA = 222;

    class SLIPMsg {

        public:

            /**
             * Maximum decoded message length.
             */
            unsigned int maxLength;

            /**
             * Message found flag.
             */
            bool msgFound;

            /**
             * Message end index.
             */
            unsigned int msgEnd;

            /**
             * Message length.
             */
            unsigned int msgLength;

            /**
             * SLIP message.
             */
            std::vector<uint8_t> msg;

            /**
             * Pending message bytes buffer.
             */
            std::vector<uint8_t> buffer;
            
            /**
             * Default constructor.
             */
            SLIPMsg();

            /**
             * Constructor.
             * @param maxLength Maximum message length to decode.
             */
            SLIPMsg(unsigned int maxLength);

            /**
             * Searches input for a SLIP message.
             * @param bytes Vector of raw bytes.
             * @param msgStart Location to begin search.
             * @return True if message decoded.
             */
            bool decodeSLIPMsg(const std::vector<uint8_t> & bytes, unsigned int msgStart = 0);

            /**
             * Parses SLIP message to remove control bytes.
             * @param bytes Vector of raw bytes.
             * @param pos Search location index.
             * @return True if message decoded.
             */
            bool decodeSLIPMsgContents(const std::vector<uint8_t> & bytes, unsigned int pos);

            /**
             * Encodes a SLIP message.
             * @param bytes Vector of raw bytes.
             * @return Returns encoded message.
             */
            std::vector<uint8_t> encodeSLIPMsg(const std::vector<uint8_t> & bytes);

    };
}
#endif // COMM_SLIP_MSG_HPP
