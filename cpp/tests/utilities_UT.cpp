#include "tests/utilities_UT.hpp"
#include <gtest/gtest.h>
#include <iostream>
#include <unistd.h>
#include <string>

namespace util
{
    Utilities_UT::Utilities_UT()
    {
    }

    void Utilities_UT::SetUpTestCase(void) {
    }
    
    void Utilities_UT::SetUp(void)
    {
    }

    TEST_F(Utilities_UT, hashElement) {
        SHA_CTX context;
        SHA1_Init(&context);

        // Test hashing of int
        unsigned int intVal = 120;
        unsigned char hashVal[20] = {119, 91, 197, 195, 14, 39, 240, 229, 98, 17, 93, 19, 110, 127, 126, 219, 211, 206, 173, 137};
        hashElement(&context, intVal);
        unsigned char outHash[20];
        SHA1_Final(outHash, &context);
        for (unsigned int i = 0; i < 20; i++) {
            EXPECT_TRUE(outHash[i] == hashVal[i]);
        }

        // Test proper truncation of floats
        double doubleVal = 123456789.987654321;
        unsigned char doubleHashVal[20] = {57, 184, 2, 193, 35, 225, 250, 6, 9, 174, 32, 17, 151, 2, 189, 243, 98, 4, 114, 56};
        SHA1_Init(&context);
        hashElement(&context, doubleVal);
        SHA1_Final(outHash, &context);
        for (unsigned int i = 0; i < 20; i++) {
            EXPECT_TRUE(outHash[i] == doubleHashVal[i]);
        }
            
        // Test equality of floats
        SHA1_Init(&context);
        hashElement(&context, 123456789.9876543);
        SHA1_Final(outHash, &context);
        for (unsigned int i = 0; i < 20; i++) {
            EXPECT_TRUE(outHash[i] == doubleHashVal[i]);
        }
        
        // Test hashing of string
        unsigned char strHashVal[20] = {32, 7, 193, 121, 130, 25, 101, 249, 148, 120, 27, 125, 133, 199, 187, 217, 166, 183, 81, 227};
        std::string strVal = "thisIsAString";
        SHA1_Init(&context);
        hashElement(&context, strVal);
        SHA1_Final(outHash, &context);
        for (unsigned int i = 0; i < 20; i++) {
            EXPECT_TRUE(outHash[i] == strHashVal[i]);
        }
         
    }

}
