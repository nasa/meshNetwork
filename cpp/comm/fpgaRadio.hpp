#ifndef COMM_FPGA_RADIO_HPP
#define COMM_FPGA_RADIO_HPP

#include <string>
#include <vector>
#include <cstdint>

#include "comm/radio.hpp"
#include "comm/defines.hpp"
#include <serial/serial.h>

namespace comm {
    static const uint8_t FPGA_MSG_START = 250;

    class FPGARadio : public Radio {

        public:
            /**
             * Default constructor.
             */
            FPGARadio() {};

            /**
             * Constructor.
             * @param serialIn Serial instance to be used by radio.
             * @param configIn Radio configuration.
             */
            FPGARadio(serial::Serial * serialIn, RadioConfig & configIn);

            /**
             * This function sends bytes over the serial connetion.
             * @param msgBytes Bytes to send.
             * @return Returns number of messages sent.
             */
            virtual unsigned int sendMsg(std::vector<uint8_t> & msgBytes);

    };
}
#endif // COMM_FPGA_RADIO_HPP
