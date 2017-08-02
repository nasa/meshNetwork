Library dependencies:
    -Serial (https://github.com/wjwwood/serial)
        -Requires catkin to build (Install from source option: http://wiki.ros.org/catkin)
    -JSON (https://github.com/miloyip/rapidjson) with additional wrapper functions
    -Google test (https://github.com/google/googletest)
    -GPIO
        -Beaglebone Black (https://github.com/mkaczanowski/BeagleBoneBlack-GPIO)
        -Raspberry Pi (wiringpi.com)
    -OpenSSL library - for SHA1 hash calculations (https://www.openssl.org/docs/manmaster/crypto/crypto.html, 'sudo apt-get install libssl-dev')
    -Google Protocol Buffers (requires version 3 beta for Python3 support) - Download latest release from Github and build following readme directions. Build for both c++ and python. https://github.com/google/protobuf/releases

Test dependencies:
-Since some tests will exercise GPIO functions, they must be run on a platform with GPIO pins (i.e. BBB or Raspberry Pi).  These tests are named with a "gpio" tag.  To exclude these tests, run the test executable using the gtest filter flag (i.e. ./run_test --gtest_filter=-*gpio*).   
-Likewise for ntp required tests, use filter "ntp".
-Filters can be chained with a ":", i.e. --gtest_filter=-*gpio*:-*ntp*

Python test run script:
-Unit tests can be run using the runTest.py script.  This script will set up required testing dependencies like virtual serial ports.
-To pass test filters, use the '-f' option, i.e. sudo python3 runTest.py -f=-*gpio*.  If the filter has "-" in it, you must use the equal sign or the arguments will not be parsed correctly.
