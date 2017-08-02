#include "tests/formationClock_UT.hpp"
#include "GPIOWrapper/GPIOWrapper.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>
#include "comm/utilities.hpp"

using std::vector;

namespace {
    
}

namespace comm
{
    FormationClock_UT::FormationClock_UT()
        : m_clock()
    {
    }

    void FormationClock_UT::SetUpTestCase(void) {
    }
    
    void FormationClock_UT::SetUp(void)
    {
    }

    TEST_F(FormationClock_UT, getTime) {
        // Test non-referenced clock
        EXPECT_TRUE((int)(util::getTime() - m_clock.getTime()) == 0); // just compare whole number

        // Test referenced clock
        int sleepTime = 2*1e6;
        m_clock = FormationClock(true, util::getTime());
        EXPECT_TRUE(m_clock.getTime() < sleepTime); // should be a small value
        usleep(sleepTime);
        EXPECT_TRUE(m_clock.getTime() >= sleepTime/1.0e6); // should be greater than sleep time
        
    }

    TEST_F(FormationClock_UT, resetAndGetTDMATimer) {
        m_clock.resetTDMATimer();
        double timerValue = m_clock.getTDMATimer();
        EXPECT_TRUE(timerValue >= 0.0 && timerValue <= 0.1); // should be a small value
    
        // Delay some time and test again
        usleep(0.5*1e6);
        timerValue = m_clock.getTDMATimer();
        EXPECT_TRUE(timerValue >= 0.5 && timerValue <= 0.6); // should be a small value
    
        // Check for valid reset
        m_clock.resetTDMATimer();
        timerValue = m_clock.getTDMATimer();
        EXPECT_TRUE(timerValue >= 0.0 && timerValue <= 0.1); // should be a small value

    }
    
    // Requires NTP to test
    TEST_F(FormationClock_UT, getOffset_ntp) {
        double offset = m_clock.getOffset();
        std::cout << "Retrieved offset: " << offset << std::endl;
    }

    // Requires GPIO to test
    TEST_F(FormationClock_UT, monitorSyncPulse_gpio) {
        // Check that tdma timer is reset at ~1Hz
        int delayTime = 0.1*1e6; // 100 ms delay
        unsigned int loopMax = 2.0 / 0.1; // test for two seconds
        double timerValue = -1.0;
        for (unsigned int i = 0; i < loopMax; i++) {
            timerValue = m_clock.getTDMATimer();
            EXPECT_TRUE(timerValue >= 0.0 && timerValue <= 1.1);
            usleep(delayTime);
        }
    }

}
