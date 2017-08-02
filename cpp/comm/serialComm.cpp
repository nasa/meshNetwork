#include "comm/serialComm.hpp"
#include "comm/utilities.hpp"
#include "comm/exceptions.hpp"

using std::vector;

namespace comm {            
    
    SerialComm::SerialComm(CommProcessor * commProcessorIn, Radio * radioIn, MsgParser * msgParserIn) :
        Comm(commProcessorIn, radioIn, msgParserIn)
    {}

}
