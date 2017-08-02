#ifndef COMM_UDPRADIO_HPP
#define COMM_UDPRADIO_HPP

#include <string>
#include <vector>
#include <cstdint>

#include "comm/radio.hpp"

namespace comm {
    
    class UDPRadio : public Radio {

        public:
            
            /**
             * Constructor.
             * @param udpInterfaceIn UDP network interface.
             * @param udpPortIn UDP port.
             * @param configIn Radio configuration.
             */
            UDPRadio(std::string udpInterfaceIn, std::string udpPortIn, RadioConfig & configIn);

    };
}
#endif // COMM_UDPRADIO_HPP
