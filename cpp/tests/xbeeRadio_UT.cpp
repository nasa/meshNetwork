#include "tests/xbeeRadio_UT.hpp"
#include "GPIOWrapper/GPIOWrapper.hpp"
#include <gtest/gtest.h>
#include <serial/serial.h>
#include <unistd.h>
#include <iostream>

namespace comm
{
    serial::Serial xbeeSer("/dev/ttyV2", 9600, serial::Timeout::simpleTimeout(10));
    comm::RadioConfig xbeeConfig;
    static int testPin;

    XbeeRadio_UT::XbeeRadio_UT()
        : m_xbeeRadio(&xbeeSer, xbeeConfig, GPIOWrapper::getPin("P8_26"))
    {
    }

    void XbeeRadio_UT::SetUpTestCase(void) {
        testPin = GPIOWrapper::getPin("P8_19");
        GPIOWrapper::setupPin(testPin, GPIOWrapper::INPUT);
    }
    
    void XbeeRadio_UT::SetUp(void)
    {
    }

    TEST_F(XbeeRadio_UT, wake_gpio) {
        m_xbeeRadio.wake();
        std::cout << "Wake pin value: " << GPIOWrapper::getValue(testPin) << std::endl;
    }

}
