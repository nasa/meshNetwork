#include "comm/commProcessor.hpp"
#include <algorithm>
//#include "comm/msgProcessors.hpp"
//#include "comm/commands.hpp"

using std::vector;
//using std::map;

namespace comm {
    
    CommProcessor::CommProcessor(std::vector<MsgProcessor *> msgProcessorsIn) :
        msgProcessors(msgProcessorsIn)        
    {};
    
    int CommProcessor::processMsg(vector<uint8_t> & msg, MsgProcessorArgs args) {

        if (msg.size() > 0) {
            // Check command id and pass to appropriate message processor
            uint8_t cmdId = msg[0]; // the command ID will be the first element in the message
            std::vector<uint8_t>::iterator it;
            for (unsigned int i = 0; i < msgProcessors.size(); i++) { // look for proper processor
                it = std::find(msgProcessors[i]->cmdIds.begin(), msgProcessors[i]->cmdIds.end(), cmdId);
                for (unsigned int j = 0; j < msgProcessors[i]->cmdIds.size(); j++) {
                }
                if (it != msgProcessors[i]->cmdIds.end()) { // cmd Id found
                    msgProcessors[i]->processMsg(cmdId, msg, args); // processor command
                    return i;
                }
                    


                //std::vector<uint8_t>::iterator it;
                //it = std::find(MsgProcessors::cmdIdMappings[msgProcessors[i]].begin(), MsgProcessors::cmdIdMappings[msgProcessors[i]].end(), cmdId);
                //if (it != MsgProcessors::cmdIdMappings[msgProcessors[i]].end()) { // cmd Id found
                //    MsgProcessors::msgProcessorMap[msgProcessors[i]](5); // processor command
                //    return 1;
                //}
                
            }
        }
        
        return -1; // no processor found
    }
}
