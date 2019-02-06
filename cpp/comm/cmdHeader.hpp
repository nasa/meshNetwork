#ifndef COMM_CMD_HEADER_HPP
#define COMM_CMD_HEADER_HPP

#include <cstdint>
#include <vector>
#include "comm/commandSupport.hpp"

namespace comm {

    // Defined header types
/*    enum HeaderType {
        NODE_HEADER = 0,
        MINIMAL_HEADER = 1,
        SOURCE_HEADER = 2,
        NO_HEADER = 3,
        HEADER_UNKNOWN = 4
    };*/

    // Node Header
    struct NodeHeader {
        uint8_t cmdId;
        uint8_t sourceId;
        uint16_t cmdCounter;
    };

    union NodeHeaderU {
        NodeHeader header;
        char c[sizeof(NodeHeader)];
    };

    // Source Header
    struct SourceHeader {
        uint8_t cmdId;
        uint8_t sourceId;
    };

    union SourceHeaderU {
        SourceHeader header;
        char c[sizeof(SourceHeader)];
    };

    // Minimal Header
    struct MinimalHeader {
        uint8_t cmdId;
    };

    union MinimalHeaderU {
        MinimalHeader header;
        char c[sizeof(MinimalHeader)];
    };

    class CmdHeader {
        public:
            /**
             * Type of header stored in this instance.
             */
            HeaderType type;

            /**
             * Command ID.
             */
            uint8_t cmdId;

            /**
             * Source ID number.
             */
            uint8_t sourceId;

            /**
             * Command counter.
             */
            uint16_t cmdCounter;

            /**
             * Default constructor
             */
            CmdHeader();

            /**
             * Minimal header constructor.
             * @param cmdId Command ID for this instance.
             */
            CmdHeader(uint8_t cmdId);

            /**
             * Source header constructor.
             * @param cmdId Command ID for this instance.
             * @param sourceId Source ID.
             */
            CmdHeader(uint8_t cmdId, unsigned int sourceId);

            /**
             * Node header constructor.
             * @param cmdId Command ID for this instance.
             * @param sourceId Source ID.
             * @param cmdCounter Command counter.
             */
            CmdHeader(uint8_t cmdId, unsigned int sourceId, uint16_t cmdCounter);

            /**
             * Convert header elements to vector of bytes.
             */
            std::vector<uint8_t> packHeader();
    };

    /**
     * Unpack a header from vector of bytes.
     */
    unsigned int unpackHeader(std::vector<uint8_t> & bytes, HeaderType type, CmdHeader & retHeader);

    /**
     * Return size of requested header type.
     */
    unsigned int headerSize(HeaderType type);

    /**
     * Create command header.
     */
    CmdHeader createHeader(uint8_t cmdId, std::vector<uint8_t> & headerInputs);
    CmdHeader createHeader(uint8_t cmdId, uint8_t sourceId = 0, uint16_t cmdCounter = 0);
    CmdHeader createHeader(HeaderType headerType, std::vector<uint8_t> & headerInputs);
}

#endif // COMM_CMD_HEADER_HPP
