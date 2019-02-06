#ifndef COMM_XBEE_RADIO_HPP
#define COMM_XBEE_RADIO_HPP

#include "comm/radio.hpp"
#include <serial/serial.h>

namespace comm {

    class XbeeRadio : public Radio {
    
        public:
            /**
             * Sleep GPIO pin.
             */
            int sleepPin;

            /**
             * Default constructor.
             */
            XbeeRadio() : Radio(), sleepPin(-1) {};
            
            /**
             * Constructor.
             * @param serialIn Serial instance to be used by radio.
             * @param configIn Radio configuration.
             * @param sleepPin GPIO pin to toggle sleep.
             */
            XbeeRadio(serial::Serial * serialIn, RadioConfig & configIn, int sleepPin = -1);

            /**
             * This function sets the radio mode to OFF.
             * @return True on successful mode change.
             */
            virtual bool setOff(void);
            
            /**
             * This function sets the radio mode to SLEEP.
             * @return True on successful mode change.
             */
            virtual bool setSleep(void);
            
            /**
             * This function sets the radio mode to RECEIVE.
             * @return True on successful mode change.
             */
            virtual bool setReceive(void);
            
            /**
             * This function sets the radio mode to TRANSMIT.
             * @return True on successful mode change.
             */
            virtual bool setTransmit(void);
            
            /**
             * This function wakes the radio.
             */
            void wake(void);
            
    };
}
#endif // COMM_XBEE_RADIO_HPP
