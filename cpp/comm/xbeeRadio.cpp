#include "comm/xbeeRadio.hpp"
#include "GPIOWrapper/GPIOWrapper.hpp"

namespace comm {
    XbeeRadio::XbeeRadio(serial::Serial * serialIn, RadioConfig & configIn, int sleepPinIn) :
        SerialRadio(serialIn, configIn),
        sleepPin(sleepPinIn)
    {
        if (sleepPinIn > -1) { // sleep pin available
            GPIOWrapper::setupPin((unsigned int)sleepPinIn, GPIOWrapper::OUTPUT);
        }
    }
    
    bool XbeeRadio::setOff(void) {
        setSleep();
        mode = OFF;
        return true;
    }

    bool XbeeRadio::setSleep(void) {
        if (sleepPin > -1) {
            GPIOWrapper::setValue((unsigned int)sleepPin, GPIOWrapper::HIGH);
        }

        mode = SLEEP;

        return true;
    }

    bool XbeeRadio::setReceive(void) {
        wake();
        mode = RECEIVE;
        return true;
    }

    bool XbeeRadio::setTransmit(void) {
        wake();
        mode = TRANSMIT;
        return true;
    }

    void XbeeRadio::wake(void) {
        if (sleepPin > -1) {
            GPIOWrapper::setValue((unsigned int)sleepPin, GPIOWrapper::LOW);
        }
    }
}
