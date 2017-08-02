#ifndef COMM_CHECKSUM_HPP
#define COMM_CHECKSUM_HPP

#include <vector>
#include <cstdint>

namespace comm {

    std::vector<uint8_t> calculate8bitFletcherChecksum(std::vector<uint8_t> msgBytes);
    bool compareChecksum(std::vector<uint8_t> msgBytes, std::vector<uint8_t> & checksumBytes);
}
#endif // COMM_CHECKSUM_HPP

