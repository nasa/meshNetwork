#include "tests/checksum_UT.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <vector>
#include "comm/checksum.hpp"

using std::vector;

namespace {
    vector<uint8_t> testMsg = {1, 2, 3, 4, 5, 100, 90, 80, 70, 60};
    vector<uint8_t> validChecksum = {159, 130}; 
}
namespace comm
{

    checksum_UT::checksum_UT()
    {
    }

    void checksum_UT::SetUpTestCase(void) {
 
    }
    
    void checksum_UT::SetUp(void)
    {
    }

    TEST_F(checksum_UT, calculate8bitFletcher) {
        vector<uint8_t> checksum = calculate8bitFletcherChecksum(testMsg);
        ASSERT_TRUE(checksum.size() == 2);
        EXPECT_TRUE(checksum[0] == validChecksum[0]);
        EXPECT_TRUE(checksum[1] == validChecksum[1]);
    }    

    TEST_F(checksum_UT, compareChecksum) {
        EXPECT_TRUE(compareChecksum(testMsg, validChecksum)); 

        // Alter valid checksum and recompare
        validChecksum[0] += 1;
        EXPECT_TRUE(compareChecksum(testMsg, validChecksum) == false); 
    }
}
