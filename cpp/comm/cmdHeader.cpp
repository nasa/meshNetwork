#include "comm/cmdHeader.hpp"
#include "comm/commands.hpp"
#include <cstring>

using std::vector;

namespace comm {

    CmdHeader::CmdHeader() :
        type(NO_HEADER)
    {}

    CmdHeader::CmdHeader(uint8_t cmdIdIn) :
        type(MINIMAL_HEADER),
        cmdId(cmdIdIn)
    {}
    
    CmdHeader::CmdHeader(uint8_t cmdIdIn, unsigned int sourceIdIn) :
        type(SOURCE_HEADER),
        cmdId(cmdIdIn),
        sourceId(sourceIdIn)
    {}
    
    CmdHeader::CmdHeader(uint8_t cmdIdIn, unsigned int sourceIdIn, unsigned int cmdCounterIn) :
        type(NODE_HEADER),
        cmdId(cmdIdIn),
        sourceId(sourceIdIn),
        cmdCounter(cmdCounterIn)
    {}
    
    vector<uint8_t> CmdHeader::packHeader() {
        vector<uint8_t> header;
        switch(type) {
            case MINIMAL_HEADER:
                header.push_back(cmdId);
                break;
            case SOURCE_HEADER:
                header.push_back(cmdId);
                header.push_back(sourceId);
                break;
            case NODE_HEADER:
                header.push_back(cmdId);
                header.push_back(sourceId);
                header.push_back(cmdCounter);
                break;
            default:
                break;
        }

        return header;
    }

    unsigned int unpackHeader(vector<uint8_t> & bytes, HeaderType type, CmdHeader & retHeader) {
        unsigned int retValue = 0;        

        // Check for non-zero length header
        if (bytes.size() == 0) {
            return retValue;
        }

        // Unpack header
        if (type == HEADER_UNKNOWN) { // attempt to determine header type
            uint8_t cmdId = bytes[0];
            if (Cmds::cmdDict.find(cmdId) != Cmds::cmdDict.end()) { // command ID found
                type = Cmds::cmdDict[cmdId];
            }
            else { // can't determine header
                return retValue;
            }
        }            

        // Parse header
        switch (type) {
            case NODE_HEADER:
                if (bytes.size() >= sizeof(NodeHeader)) { // make sure enough bytes
                    NodeHeaderU headerU;
                    memcpy(&headerU, bytes.data(), sizeof(NodeHeader));
                    retHeader = CmdHeader(headerU.header.cmdId, headerU.header.sourceId, headerU.header.cmdCounter);
                    retValue = sizeof(NodeHeader);
                }
                break;
            
            case SOURCE_HEADER:
                if (bytes.size() >= sizeof(SourceHeader)) { // make sure enough bytes
                    SourceHeaderU headerU;
                    memcpy(&headerU, bytes.data(), sizeof(SourceHeader));
                    retHeader = CmdHeader(headerU.header.cmdId, headerU.header.sourceId);
                    retValue = sizeof(SourceHeader);
                }
                break;

            case MINIMAL_HEADER:
                if (bytes.size() >= sizeof(MinimalHeader)) { // make sure enough bytes
                    MinimalHeaderU headerU;
                    memcpy(&headerU, bytes.data(), sizeof(MinimalHeader));
                    retHeader = CmdHeader(headerU.header.cmdId);
                    retValue = sizeof(MinimalHeader);
                }
                break;
            
            default:
                break;
        }
        
        return retValue;
    }
    
}
