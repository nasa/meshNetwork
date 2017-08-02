#include "tests/commProcessor_UT.hpp"
#include "comm/testMsgProcessor.hpp"
#include "comm/tdmaCmds.hpp"
#include "comm/msgProcessor.hpp"
#include <gtest/gtest.h>
#include <unistd.h>

using std::vector;

namespace {
    comm::TestMsgProcessor testProcessor;    
    vector<comm::MsgProcessor *> msgProcessors = {&testProcessor};
}

namespace comm
{
    CommProcessor_UT::CommProcessor_UT() :
        m_commProcessor(CommProcessor(vector<comm::MsgProcessor *>()))
    {
    }

    void CommProcessor_UT::SetUpTestCase(void) {
    }
    
    void CommProcessor_UT::SetUp(void)
    {
    }

    TEST_F(CommProcessor_UT, processMsg) {
        // Test with no message processors
        vector<uint8_t> msg = {TDMACmds::MeshStatus,2,3,4,5};
        MsgProcessorArgs args;
        EXPECT_TRUE(m_commProcessor.processMsg(msg, args) == -1);

        // Test with proper processor
        m_commProcessor.msgProcessors = msgProcessors;
        EXPECT_TRUE(m_commProcessor.processMsg(msg, args) == 0);

        // Test with multiple processors
        comm::TestMsgProcessor badProcessor;
        badProcessor.cmdIds = vector<uint8_t>({255});    
        m_commProcessor.msgProcessors = vector<comm::MsgProcessor *>({&badProcessor, &testProcessor});
        EXPECT_TRUE(m_commProcessor.processMsg(msg, args) == 1);


    }


}
