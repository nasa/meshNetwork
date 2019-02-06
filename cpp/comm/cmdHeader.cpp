#include "comm/cmdHeader.hpp"
#include "comm/commands.hpp"
#include <cstring>
#include <iostream>

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
    
    CmdHeader::CmdHeader(uint8_t cmdIdIn, unsigned int sourceIdIn, uint16_t cmdCounterIn) :
        type(NODE_HEADER),
        cmdId(cmdIdIn),
        sourceId(sourceIdIn),
        cmdCounter(cmdCounterIn)
    {
    }

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
                header.resize(4);
                header[0] = cmdId;
                header[1] = sourceId;
                memcpy(header.data() + 2, &cmdCounter, 2);
                //header.push_back(cmdCounter);
                break;
            default:
                break;
        }

        return header;
    }

    CmdHeader createHeader(uint8_t cmdId, uint8_t sourceId, uint16_t cmdCounter) {
        CmdHeader header;
        std::vector<uint8_t> headerInputs(3);
        headerInputs[0] = cmdId;
        headerInputs[1] = sourceId;
        memcpy(headerInputs.data() + 2, &cmdCounter, 2);
        return createHeader(cmdId, headerInputs);

    }
        
    CmdHeader createHeader(uint8_t cmdId, std::vector<uint8_t> & headerInputs) {
        CmdHeader header;
        
        // Attempt to determine header type
        if(Cmds::cmdDict.size() > 0 && Cmds::cmdDict.find(cmdId) != Cmds::cmdDict.end()) {
            return createHeader(Cmds::cmdDict[cmdId], headerInputs);
        }

        return header;
    }
    
    CmdHeader createHeader(HeaderType headerType, std::vector<uint8_t> & headerInputs) {
        CmdHeader header;
        
        switch(headerType) {
                case NO_HEADER:
                    break;
                case MINIMAL_HEADER:
                    if (headerInputs.size() >= 1) { 
                        header = CmdHeader(headerInputs[0]);
                    }
                    break;
                case SOURCE_HEADER:
                    if (headerInputs.size() >= 2) { 
                        header = CmdHeader(headerInputs[0], headerInputs[1]);
                    }
                    break;
                case NODE_HEADER:     
                    if (headerInputs.size() >= 3) { 
                        uint16_t counter;
                        memcpy(&counter, &headerInputs[2], 2);
                        header = CmdHeader(headerInputs[0], headerInputs[1], counter);
                    }
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

    unsigned int headerSize(HeaderType type) {
        // Return size of header type
        switch (type) {
            case HEADER_UNKNOWN:
                return 0;
                break;
            case NODE_HEADER:
                return sizeof(NodeHeader);
                break;
            case SOURCE_HEADER:
                return sizeof(SourceHeader);
                break;
            case MINIMAL_HEADER:
                return sizeof(MinimalHeader);
                break;
            default:
                return 0;
        }
    }

    
}
