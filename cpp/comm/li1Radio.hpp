#ifndef COMM_LI1_RADIO_HPP
#define COMM_LI1_RADIO_HPP

#include "comm/radio.hpp"
#include "comm/commBuffer.hpp"
#include <serial/serial.h>
#include <vector>
#include <cstdint>

namespace comm {
    // Li-1 radio command types.
    enum Li1RadioCmdType {
        LI1_TRANSMIT = 0x1003,
        LI1_NO_OP = 0x1001,
        LI1_RECEIVED_DATA = 0x2004
    };

    // Li-1 radio command structure.
    struct Li1Cmd {
        /**
         * Validity flag.
         */
        bool valid;

        /**
         * Command type.
         */
        uint16_t type;

        /**
         * Parsed command header bytes.
         */
        std::vector<uint8_t> header;

        /**
         * Raw command header bytes.
         */
        std::vector<uint8_t> rawHeader;

        /**
         * Parsed command payload data bytes.
         */
        std::vector<uint8_t> payload;

        /**
         * Full command raw bytes.
         */
        std::vector<uint8_t> msgBytes;

        /**
         * Default constructor.
         */
        Li1Cmd() {};

        /**
         * Constructor with inputs.
         * @param typeIn Command type.
         * @param payloadIn Command payload data bytes.
         */
        Li1Cmd(Li1RadioCmdType typeIn, std::vector<uint8_t> payloadIn) :
            valid(false),
            type(typeIn),
            payload(payloadIn)
        {};
    };

    class Li1Radio : public Radio {

        public:
            /**
             * Length of sync bytes at beginning of Li-1 commands.
             */
            static unsigned int lenSyncBytes;

            /**
             * Li-1 sync bytes.
             */
            static std::vector<uint8_t> syncBytes;

            /**
             * Li-1 header length.
             */
            static unsigned int headerLength;

            /**
             * Li-1 checksum length.
             */
            static unsigned int checksumLen;

            /**
             * Li-1 maximum payload size.
             */
            static unsigned int maxPayload;

            /**
             * Received command bytes buffer.
             */
            std::vector<uint8_t> cmdRxBuffer;

            /**
             * Processed commands buffer.
             */
            CommBuffer<Li1Cmd> cmdBuffer;
            //CommBuffer cmdBuffer;

            /**
             * Big endianness flag
             */
            bool bigendian;

            /**
             * Creates Li-1 command for transmission to radio.
             * @param cmd Li-1 command structure.
             */
            void createCommand(Li1Cmd & cmd);

            /**
             * Creates Li-1 command header.
             * @param cmd Li-1 command structure.
             */
            void createHeader(Li1Cmd & cmd);

            /**
             * Creates Li-1 command payload.
             * @param cmd Li-1 command structure.
             */
            void createPayload(Li1Cmd & cmd);

            /**
             * Parses command header information from message bytes.
             * @param cmd Li-1 command structure.
             * @param serBytes Raw serial bytes.
             * @return Returns true if header data found.
             */
            bool parseCmdHeader(Li1Cmd & cmd, const std::vector<uint8_t> serBytes);

            /**
             * Parses command payload from message bytes.
             * @param cmd Li-1 command structure.
             * @param payloadSize Expected length of payload data.
             * @param serBytes Raw serial bytes.
             * @return Returns end of parsed bytes.
             */
            unsigned int parseCmdPayload(Li1Cmd & cmd, unsigned int payloadSize, const std::vector<uint8_t> & serBytes);

            /**
             * Parses raw AX25 formatted message.
             * @param msgBytes Raw serial bytes
             * @return Returns parsed bytes.
             */
            std::vector<uint8_t> parseAX25Msg(std::vector<uint8_t> & msgBytes);

            /**
             * Parses command data structure from raw serial bytes.
             * @param cmd Li-1 command structure to populate.
             * @param serBytes Raw serial bytes.
             * @return Returns position of last parsed byte.
             */
            unsigned int parseCommand(Li1Cmd & cmd, std::vector<uint8_t> & serBytes);

            /**
             * This function sends bytes over the serial connetion.
             * @param msgBytes Bytes to send.
             * @return Returns number of messages sent.
             */
            virtual unsigned int sendMsg(std::vector<uint8_t> & msgBytes);

            /**
             * This function creates a message for serial transmission.
             * @param msgBytes Bytes to create message from.
             * @return Returns message.
             */
            virtual std::vector<uint8_t> createMsg(std::vector<uint8_t> msgBytes);

            /**
             * This function processes newly received bytes.
             * @param newBytes Bytes to process.
             * @param bufferFlag Whether or not to buffer new bytes or replace existing.
             * @return Returns number of new bytes buffered.
             */
            virtual int processRxBytes(std::vector<uint8_t> & newBytes, bool bufferFlag);

            /**
             * Default constructor.
             */
            Li1Radio();

            /**
             * Constructor.
             * @param serialIn Serial instance to be used by radio.
             * @param configIn Radio configuration.
             */
            Li1Radio(serial::Serial * serialIn, RadioConfig & configIn);

    };
}
#endif // COMM_LI1_RADIO_HPP
