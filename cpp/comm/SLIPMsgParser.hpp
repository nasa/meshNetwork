#ifndef COMM_SLIP_MSG_PARSER_HPP
#define COMM_SLIP_MSG_PARSER_HPP

#include "comm/defines.hpp"
#include "msgParser.hpp"
#include "SLIPMsg.hpp"
#include <serial/serial.h>

namespace comm {

    class SLIPMsgParser : public MsgParser {

        public:
            /**
             * SLIPMsg instance.
             */
            SLIPMsg slipMsg;

            /**
             * Default constructor.
             */
            SLIPMsgParser() : slipMsg(SLIPMsg(256)) {};

            /**
             * Constructor.
             * @param parseMsgMaxIn Message parsing limit
             * @param SLIPMaxLength Maximum length of SLIP message
             */
            SLIPMsgParser(unsigned int parseMsgMaxIn, unsigned int SLIPMaxLength);

            /**
             * This function searches raw byte for a message.
             * @param msgBytes The raw bytes of a message.
             * @param msgStart Index to begin search.
             * @return Length of parsed message.
             */
            virtual unsigned int parseSerialMsg(const std::vector<uint8_t> & msgBytes, unsigned int msgStart);

            /**
             * This function encodes raw input bytes into a message for serial transmission.
             * @param msgBytes Bytes to be encoded.
             */
            virtual std::vector<uint8_t> encodeMsg(std::vector<uint8_t> msgBytes);

    };
}
#endif // COMM_SLIP_MSG_PARSER_HPP
