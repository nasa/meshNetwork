#include "tests/crc_UT.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <vector>
#include "comm/crc.hpp"

using std::vector;

vector<uint8_t> testMsg = {1, 2, 3, 4, 5, 100, 90, 80, 70, 60};
comm::crc_t validCRC = 21788; 
vector<uint8_t> crcBytes = {0x55, 0x1C};

namespace comm
{

    crc_UT::crc_UT()
    {
    }

    void crc_UT::SetUpTestCase(void) {
 
    }
    
    void crc_UT::SetUp(void)
    {
    }

    TEST_F(crc_UT, create) {
        crc_t crc = crc_create(testMsg);
        EXPECT_TRUE(crc == validCRC);
    }    

    TEST_F(crc_UT, bytesToCrc) {
        EXPECT_TRUE(bytesToCrc(crcBytes) == validCRC);
    }
    
    TEST_F(crc_UT, crcToBytes) {
        vector<uint8_t> bytes = crcToBytes(validCRC);
        EXPECT_TRUE(bytes[0] == crcBytes[0]);
        EXPECT_TRUE(bytes[1] == crcBytes[1]);
    }

}
