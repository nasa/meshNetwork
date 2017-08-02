#ifndef UTIL_UTILITIES_HPP
#define UTIL_UTILITIES_HPP

#include <string>
#include <sstream>
#include <iostream>
#include <stdio.h>
#include <vector>
#include <cstdint>
#include <ctime>
#include <openssl/sha.h>
#include "comm/defines.hpp"
#include <serial/serial.h>

namespace util {

    enum TIME_OFFSET_TYPE {
	    PPS = 0,
	    STANDARD = 1
    };

    /**
     * Check if system is big endian.
     * @return Returns true if system is big endian.
     */
    inline bool isbigendian()
    {
        union endian_test_u
        {
            unsigned char bytes[2];
            uint16_t value;
        };
        static endian_test_u endian_test;
        endian_test.bytes[0] = 1;
        endian_test.bytes[1] = 0;

        return 1 != endian_test.value;
    }

    /**
     * Get current system time.
     * @return Returns current system time.
     */
    inline double getTime() {
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        return (double)(ts.tv_sec + ts.tv_nsec/1.0e9);
    }

    /**
     * Split a string using provided delimiter.
     * @param s String to split.
     * @param delim Delimiter.
     * @return Returns vector of split string components.
     */
    inline std::vector<std::string> split(const std::string &s, char delim) {
        std::vector<std::string> elems;
        std::stringstream ss(s);
        std::string item;
        if (delim == ' ') { // whitespace delimiter
            while (ss >> item) {
                elems.push_back(item);
            }
        }
        else { // other delimiter
            while (std::getline(ss, item, delim)) {
                elems.push_back(item);
            }
        }

        return elems;
    }

    /*
     * Get clock time offset.
     * @param offsetType Type of offset to retrieve.
     * @param offset Offset to return.
     * @return Returns offset retrieval result flag.
     */
    inline int getTimeOffset(TIME_OFFSET_TYPE offsetType, double & offset) {
        if (NTP_ENABLED == 0) {
            return -1;
        }

        if (offsetType == PPS) {
            FILE * pipe = popen("ntpq -p", "r");
            if (!pipe) {
                return -1;
            }

            // Read result line by line
            char buffer[256];
            std::string line;
            while (!feof(pipe)) {
                if (fgets(buffer, sizeof(buffer), pipe) != NULL) {
                    line = buffer;
                    if (line.find("PPS") != std::string::npos) { // PPS line
                        std::vector<std::string> elems = split(line, ' ');

                        // Do quick check for valid output
                        if (elems.size() == 10) {
                            offset = std::stod(elems[8]);
                        }
                        pclose(pipe);
                        return 0;
                    }
                }
            }
            pclose(pipe);
        }
        else if (offsetType == STANDARD) {
            int retValue = -1;
            FILE * pipe = popen("ntpq -crv", "r");
            if (!pipe) {
                return -1;
            }

            // Read result line by line
            char buffer[256];
            std::string line;
            while (!feof(pipe)) {
                if (fgets(buffer, sizeof(buffer), pipe) != NULL) {
                    line = buffer;
                    if (line.find("sync_pps") != std::string::npos) { // sync status found
                        retValue = 0;
                    }
                    else if (line.find("offset") != std::string::npos) { // offset found
                        std::vector<std::string> elems = split(line, ',');
                        for (unsigned int i = 0; i < elems.size(); i++) {
                            if (elems[i].find("offset") != std::string::npos) { // offset value
                                offset = std::stod(elems[i].substr(8, elems[i].size()));
                                break;
                            }
                        }
                    }
                }
            }
            pclose(pipe);
            return retValue;
        }

        return -1;
    }

    /**
     * Updates SHA1 hash value based on provided string.
     * @param context SHA1 hash structure.
     * @param elem String element to hash.
     */
    inline void hashElement(SHA_CTX * context, std::string elem) {
        SHA1_Update(context, elem.c_str(), elem.size());
    }

    /**
     * Updates SHA1 hash value based on provided unsigned int.
     * @param context SHA1 hash structure.
     * @param elem String element to hash.
     */
    inline void hashElement(SHA_CTX * context, unsigned int elem) {
        std::string out = std::to_string(elem);
        SHA1_Update(context, out.c_str(), out.size());
    }

    /**
     * Updates SHA1 hash value based on provided double.
     * @param context SHA1 hash structure.
     * @param elem String element to hash.
     */
    inline void hashElement(SHA_CTX * context, double elem) {
        // Set precision of float before hashing
        std::ostringstream outSS;
        outSS.precision(7);
        outSS << std::fixed << elem;
        std::string out = outSS.str();
        SHA1_Update(context, out.c_str(), out.size());
    }
        

    void setupSerial(serial::Serial & ser, std::string port, unsigned int baudrate, unsigned int timeout);
    
    std::vector<uint8_t> packBytes(void * data, unsigned int dataSize);

}
#endif // UTIL_UTILITIES_HPP
