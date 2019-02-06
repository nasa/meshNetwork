#include "comm/xbeeRadio.hpp"
#include "GPIOWrapper/GPIOWrapper.hpp"

namespace comm {
    XbeeRadio::XbeeRadio(serial::Serial * serialIn, RadioConfig & configIn, int sleepPinIn) :
        Radio(serialIn, configIn),
        sleepPin(sleepPinIn)
    {
        if (sleepPinIn > -1) { // sleep pin available
            GPIOWrapper::setupPin((unsigned int)sleepPinIn, GPIOWrapper::OUTPUT);
        }
    }
    
    bool XbeeRadio::setOff(void) {
        setSleep();
        mode = RADIO_OFF;
        return true;
    }

    bool XbeeRadio::setSleep(void) {
        if (sleepPin > -1) {
            GPIOWrapper::setValue((unsigned int)sleepPin, GPIOWrapper::HIGH);
        }

        mode = RADIO_SLEEP;

        return true;
    }

    bool XbeeRadio::setReceive(void) {
        wake();
        mode = RADIO_RECEIVE;
        return true;
    }

    bool XbeeRadio::setTransmit(void) {
        wake();
        mode = RADIO_TRANSMIT;
        return true;
    }

    void XbeeRadio::wake(void) {
        if (sleepPin > -1) {
            GPIOWrapper::setValue((unsigned int)sleepPin, GPIOWrapper::LOW);
        }
    }
}
