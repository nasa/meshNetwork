#ifndef __COMM_FORMATION_CLOCK_UT_HPP__
#define __COMM_FORMATION_CLOCK_UT_HPP__

#include <gtest/gtest.h>
#include "comm/formationClock.hpp"

namespace comm
{
    class FormationClock_UT : public ::testing::Test
    {
      public:  
      
      protected:
        FormationClock_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

        /* The class under test.
         */
        FormationClock m_clock;

    };
}

#endif // __COMM_FORMATION_CLOCK_UT_HPP__
