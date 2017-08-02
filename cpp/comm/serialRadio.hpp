#ifndef COMM_SERIAL_RADIO_HPP
#define COMM_SERIAL_RADIO_HPP

#include <string>
#include <vector>
#include <cstdint>

#include "comm/radio.hpp"
#include "comm/defines.hpp"
#include <serial/serial.h>

namespace comm {

    class SerialRadio : public Radio {

        public:
            /**
             * Serial instance.
             */
            serial::Serial * serial;

            /**
             * Default constructor.
             */
            SerialRadio() {};

            /**
             * Constructor.
             * @param serialIn Serial instance to be used by radio.
             * @param configIn Radio configuration.
             */
            SerialRadio(serial::Serial * serialIn, RadioConfig & configIn);

            /**
             * This function clears the receive buffer.
             * @param bufferFlag Whether or not to buffer new bytes or replace existing.
             * @param bytesToRead Number of bytes to attempt to read.
             * @return Returns number of new bytes buffered.
             */
            virtual int readBytes(bool bufferFlag, int bytesToRead = 65536);

            /**
             * This function sends bytes over the serial connetion.
             * @param msgBytes Bytes to send.
             * @return Returns number of messages sent.
             */
            virtual unsigned int sendMsg(std::vector<uint8_t> & msgBytes);

    };
}
#endif // COMM_SERIAL_RADIO_HPP
