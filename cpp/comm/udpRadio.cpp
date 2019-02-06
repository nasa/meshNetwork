#include "comm/udpRadio.hpp"

using std::vector;
namespace comm {
    UDPRadio::UDPRadio(std::string udpInterfaceIn, std::string udpPortIn, RadioConfig & configIn) :
        Radio(NULL, configIn)
    {
    };

}
