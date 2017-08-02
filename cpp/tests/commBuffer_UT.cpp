#include "tests/commBuffer_UT.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <vector>

using std::vector;

namespace {
    
}

namespace comm
{
    CommBuffer_UT::CommBuffer_UT() :
        m_commBuffer(CommBuffer< vector<uint8_t> >(5))
    {
    }

    void CommBuffer_UT::SetUpTestCase(void) {
    }
    
    void CommBuffer_UT::SetUp(void)
    {
    }

    TEST_F(CommBuffer_UT, pushAndPop) {
        vector<uint8_t> testVec = {0,1,2,3,4,5};
        
        // Push into buffer and track size (update first element to track entries)
        EXPECT_TRUE(m_commBuffer.size() == 0);
        for (unsigned int i = 0; i < m_commBuffer.maxSize; i++) {
            m_commBuffer.push(testVec);
            EXPECT_TRUE(m_commBuffer.size() == i+1);
            testVec[0] = testVec[0] + 1;
        }
        EXPECT_TRUE(m_commBuffer.size() == m_commBuffer.maxSize);

        // Overrun buffer size and then check that first element popped out
        m_commBuffer.push(testVec);
        ASSERT_TRUE(m_commBuffer.size() == m_commBuffer.maxSize);

        // Check if old data removed correctly when max size reached
        unsigned int initialSize = m_commBuffer.size();
        for (unsigned int i = 0; i < m_commBuffer.maxSize; i++) {
            vector<uint8_t> entry = m_commBuffer.pop();
            EXPECT_TRUE(entry[0] == i + 1);
            EXPECT_TRUE(m_commBuffer.size() == --initialSize);
        }
        

    }

}
