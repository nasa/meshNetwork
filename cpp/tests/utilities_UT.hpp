#ifndef __UTIL_UTILITIES_UT_HPP__
#define __UTIL_UTILITIES_UT_HPP__

#include <gtest/gtest.h>
#include "comm/utilities.hpp"

namespace util
{
    class Utilities_UT : public ::testing::Test
    {
      public:  
      
      protected:
        Utilities_UT();

        virtual void SetUp(void);
        static void SetUpTestCase(void);

    };
}

#endif // __UTIL_UTILITIES_UT_HPP__
