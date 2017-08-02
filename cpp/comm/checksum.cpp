#include "comm/checksum.hpp"

namespace comm {

    // Calculate 8-bit Fletcher checksum for message bytes
    std::vector<uint8_t> calculate8bitFletcherChecksum(std::vector<uint8_t> msgBytes) {

        std::vector<uint8_t> checksum;
        uint8_t ck_A = 0;
        uint8_t ck_B = 0;

        for (unsigned int i = 0; i < msgBytes.size(); i++) {
            ck_A += msgBytes[i];
            ck_B += ck_A;
        }

        // Output checksum
        checksum.push_back(ck_A);
        checksum.push_back(ck_B);
        return checksum;
    }

    // Compare two checksum values
    bool compareChecksum(std::vector<uint8_t> msgBytes, std::vector<uint8_t> & checksumBytes) {
        std::vector<uint8_t> checksum = calculate8bitFletcherChecksum(msgBytes);

        if (checksum[0] == checksumBytes[0] && checksum[1] == checksumBytes[1]) {
            return true; // checksum matches
        }
        else { // checksums don't match
            return false;
        }
    }

}
