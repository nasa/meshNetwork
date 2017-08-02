#ifndef COMM_COMMAND_HPP
#define COMM_COMMAND_HPP

#include <vector>
#include <cstdint>
#include "comm/utilities.hpp"
#include "comm/cmdHeader.hpp"

namespace comm {

    enum CmdStatus {
        CMD_ACCEPTED = 0,
        CMD_INVALID = 1,
        CMD_NOT_ALLOWED = 2,
        CMD_STALE = 3,
        CMD_REJECTED = 5
    }; 

    class Command {
        public:
            /**
             * Command ID.
             */
            uint8_t cmdId;

            /**
             * Command header.
             */
            CmdHeader header;

            /**
             * Last time this command was sent.
             */
            double lastTxTime;

            /**
             * Command transmit repeat interval.
             */
            double txInterval;

            /**
             * Command timestamp.
             */
            double timestamp;

            std::vector<uint8_t> packed;

            /**
             * Default constructor.
             */
            Command();

            /**
             * Command ID only constructor.
             * @param cmdId Command ID.
             */
            Command(uint8_t cmdId);

            /**
             * Full command properties constructor.
             * @param cmdId Command ID.
             * @param header Command header.
             * @param txInterval Command repeat transmit interval. Defaults to non-repeating.
             */
            Command(uint8_t cmdId, CmdHeader header, double txInterval = 0.0);

            /**
             * Pre-packed constructor.
             * @param packedIn Packed command bytes.
             * @param txIntervalIn Command repeat transmit interval. Defaults to non-repeating.
             */
            Command(std::vector<uint8_t> packedIn, double txIntervalIn = 0.0);
            
            /**
             * Unknown command type constructor.
             * @param msg Command message bytes.
             */
            //Command(std::vector<uint8_t> & msg);

            /**
             * Pack all command data.
             * @param timestamp Transmit timestamp.
             * @return Returns vector of packed command data.
             */
            std::vector<uint8_t> pack(double timestamp = util::getTime());

            /**
             * Pack provided data.
             * @param data Data to be packed.
             * @param dataSize Size of data.
             * @return Returns vector of packed data.
             */
            std::vector<uint8_t> packData(void * data, unsigned int dataSize);

            /**
             * Pack provided data.
             * @param data Data to be packed.
             * @param dataSize Size of data.
             * @param packed Vector to pack data into.
             */
            void packData(void * data, unsigned int dataSize, std::vector<uint8_t> & packed);

            /**
             * Serialize command data for transmission.
             */
            virtual std::vector<uint8_t> serialize();
    };

}

#endif // COMM_COMMAND_HPP
