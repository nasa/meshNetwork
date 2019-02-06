#include "comm/testMsgProcessor.hpp"

#include <vector>
#include <iostream>
#include "comm/tdmaCmds.hpp"
#include <map>
#include <string>
using std::vector;    


namespace comm {
    

    TestMsgProcessor::TestMsgProcessor() 
    {
        cmdIds = vector<uint8_t>({TDMACmds::MeshStatus, TDMACmds::TimeOffset});
    }
    
    bool TestMsgProcessor::processMsg(uint8_t cmdId, vector<uint8_t> & msg, MsgProcessorArgs args) {
        std::cout << "In processor 1" << std::endl;        
        return True;
    };
}    
