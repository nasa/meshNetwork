#ifndef COMM_MSG_PARSER_HPP
#define COMM_MSG_PARSER_HPP

#include <string>
#include <vector>
#include <deque>
#include <cstdint>

#include "comm/defines.hpp"
#include <serial/serial.h>

namespace comm {

    class MsgParser {

        public:
            /**
             * Container for parsed messages.
             */
            std::deque< std::vector<uint8_t> > parsedMsgs;

            /**
             * Maximum number of messages to attempt to parse.
             */
            unsigned int parseMsgMax;

            /**
             * Default constructor.
             */
            MsgParser() : parseMsgMax(1) {};

            /**
             * Constructor.
             * @param parseMsgMaxIn Message parsing limit
             */
            MsgParser(unsigned int parseMsgMaxIn);

            /**
             * This function searches raw byte for a message.
             * @param msgBytes The raw bytes of a message.
             * @param msgStart Index to begin search.
             * @return Length of parsed message.
             */
            virtual unsigned int parseSerialMsg(const std::vector<uint8_t> & msgBytes, unsigned int msgStart);

            /**
             * This function searches inputted bytes and attempts to find messages.
             * @param msgBytes Raw received bytes.
             */
            void parseMsgs(const std::vector<uint8_t> & msgBytes);

            /**
             * This function encodes raw input bytes into a message for serial transmission.
             * @param msgBytes Bytes to be encoded.
             */
            virtual std::vector<uint8_t> encodeMsg(std::vector<uint8_t> msgBytes);

            /**
             * This function returns and removes a message from the parsedMsgs vector.
             * @param msg Vector to store message to be returned.
             * @param pos Index of message to return.
             * @return Returns true if message was successfully retrieved.
             */
            bool getMsg(std::vector<uint8_t> & msg, unsigned int pos = 0);

    };
}
#endif // COMM_MSG_PARSER_HPP
