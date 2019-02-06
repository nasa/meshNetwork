#include "node/nodeConfig.hpp"
#include "GPIOWrapper.hpp"
#include <cstring>
#include "comm/utilities.hpp"
#include "comm/defines.hpp"
#include "rapidjson/JSON_Wrapper.hpp"

namespace node {
   
    NodeConfig::NodeConfig() {}

    NodeConfig::NodeConfig(std::string configFile) :
        loadSuccess(false),
        nodeId(-1),
        maxNumNodes(-1),
        hashSize(20),
        numMeshNetworks(1),
        uartNumBytesToRead(100),
        gcsPresent(false),
        gcsNodeId(0)
    {
        // Attempt load from configuration file
        loadConfigFile(configFile);

    }

    void NodeConfig::loadConfigFile(std::string configFile) {
        
        // Load configuration from file
        rapidjson::Document config;
        if (loadJSONDocument(config, configFile.c_str())) {
            loadSuccess = true; // default to success
            
            // Load general node parameters
            loadSuccess &= loadNodeConfig(config);
        
            // Load software interface config
            loadSuccess &= loadInterfaceConfig(config);       
        
            // Load communication network config
            loadSuccess &= loadCommConfig(config);
        }            
    
    }
    
    bool NodeConfig::loadNodeConfig(rapidjson::Document & config) {
        std::string tempString;
        std::string temp[3];
        int numRet = 0;
        bool loadStatus = true;        

        if (config.HasMember("node") == false) {
            return false;
        }

        const rapidjson::Value & node = config["node"];
       
        // General node configuration 
        loadStatus &= get_int(node, "maxNumNodes", maxNumNodes);
        loadStatus &= get_bool(node, "gcsPresent", gcsPresent);
        if (gcsPresent) {
            gcsNodeId = maxNumNodes;
        }
        if (node.HasMember("nodeId") == true) {
            // Get node ID from config file
            loadStatus &= get_int(node, "nodeId", nodeId);
        }
        else {
            readNodeId();
        }
        loadStatus &= get_double(node, "nodeUpdateTimeout", nodeUpdateTimeout);
        loadStatus &= get_double(node, "FCCommWriteInterval", FCCommWriteInterval);
        loadStatus &= get_string(node, "FCCommDevice", FCCommDevice);
        loadStatus &= get_int(node, "FCBaudrate", FCBaudrate);
        loadStatus &= get_double(node, "cmdInterval", cmdInterval);
        loadStatus &= get_double(node, "logInterval", logInterval);
       
        // Network config
        loadStatus &= get_string(node, "commType", tempString);
        if (tempString.compare("TDMA") == 0) {
            commType = TDMA;
        }
        else if (tempString.compare("standard") == 0) {
            commType = STANDARD;
        }
        loadStatus &= get_int(node, "meshBaudrate", meshBaudrate);
        if (node.HasMember("uartNumBytesToRead") == true) {
            loadStatus &= get_int(node, "uartNumBytesToRead", uartNumBytesToRead);
        }
        else { // Calculate based on serial baudrates
            uartNumBytesToRead = std::max(FCBaudrate, meshBaudrate) / 8;
        }
        loadStatus &= get_int(node, "parseMsgMax", parseMsgMax);
        loadStatus &= get_int(node, "rxBufferSize", rxBufferSize);
        loadStatus &= get_int(node, "numMeshNetworks", numMeshNetworks);
        numRet = get_strings(node, "meshDevices", temp, 3);
        if (numRet > 0) {
            meshDevices.assign(temp, temp + numRet);
        }
        else {
            loadStatus = false;
        }

        // Radios
        numRet = get_strings(node, "radios", temp, 3);
        if (numRet > 0 ) {
            for (int i = 0; i < numRet; i++) {
                if (temp[i].compare("Xbee") == 0) {
                    radios.push_back(XBEE);
                }
                else if (temp[i].compare("Li-1") == 0) {
                    radios.push_back(LI1);
                }
            }
        }    
        else {
            loadStatus = false;
        }    

        // Message parsers 
        numRet = get_strings(node, "msgParsers", temp, 3);
        if (numRet > 0 ) {
            for (int i = 0; i < numRet; i++) {
                if (temp[i].compare("SLIP") == 0) {
                    msgParsers.push_back(SLIP_PARSER);
                }
                else if (temp[i].compare("Standard") == 0) {
                    msgParsers.push_back(STANDARD_PARSER);
                }
            }
        }
        else {
            loadStatus = false;
        }         

        // Load platform specific parameters 
        //loadSuccess &= get_string(node, "platform", tempString);
        //if (tempString.compare("generic") == 0) {
        //    platform = GENERIC;
        //}
        //else if (tempString.compare("Pixhawk") == 0) {
        //    platform = PIXHAWK;
        //}
        //else if (tempString.compare("SatFC") == 0) {
        //    platform = SATFC;
        //}
        
        loadStatus &= loadPlatformConfig(config);

        return loadStatus;
    }

    bool NodeConfig::loadInterfaceConfig(rapidjson::Document & config) {
        if (config.HasMember("interface") == false) {
            return false;
        }
            
        const rapidjson::Value & intConfig = config["interface"];
        interface = SoftwareInterface(intConfig);

        return interface.loadSuccess;
    }

    bool NodeConfig::loadCommConfig(rapidjson::Document & config) {
        // Specific comm config
	    if (commType == TDMA) {
            if (config.HasMember("tdmaConfig") == false) {
                return false;
            }
            const rapidjson::Value & tdmaConfig = config["tdmaConfig"];
            commConfig = CommConfig(nodeId, meshBaudrate, TDMA, tdmaConfig);
        }

        return commConfig.loadSuccess;
    }
           
    bool NodeConfig::loadPlatformConfig(rapidjson::Document & json) {
        platform = GENERIC;

        return true;
    }

    bool NodeConfig::readNodeId() {
        nodeId = 1; // default to 1
        return true;
    }

    std::vector<uint8_t> NodeConfig::calculateHash() {
        SHA_CTX context;
        SHA1_Init(&context);

        // Hash global non-unique parameters
        util::hashElement(&context, maxNumNodes);
        util::hashElement(&context, (unsigned int)gcsPresent);
        util::hashElement(&context, gcsNodeId);
        util::hashElement(&context, nodeUpdateTimeout);
        util::hashElement(&context, FCCommWriteInterval);
        util::hashElement(&context, FCCommDevice);
        util::hashElement(&context, FCBaudrate);
        util::hashElement(&context, cmdInterval);
        util::hashElement(&context, logInterval);
        util::hashElement(&context, (unsigned int)commType);
        util::hashElement(&context, parseMsgMax);
        util::hashElement(&context, rxBufferSize);
        util::hashElement(&context, meshBaudrate);
        util::hashElement(&context, uartNumBytesToRead);
        util::hashElement(&context, numMeshNetworks);
        for (unsigned int i = 0; i < meshDevices.size(); i++) {
            util::hashElement(&context, meshDevices[i]);
        }
        for (unsigned int i = 0; i < radios.size(); i++) {
            util::hashElement(&context, (unsigned int)radios[i]);
        }
        for (unsigned int i = 0; i < msgParsers.size(); i++) {
            util::hashElement(&context, (unsigned int)msgParsers[i]);
        }
      
        // Interface params (order is alphabetical)
        util::hashElement(&context, interface.commRdPort);
        util::hashElement(&context, interface.commWrPort);
        util::hashElement(&context, interface.nodeCommIntIP);
        
        
 
        // Comm params (order is alphabetical)
        util::hashElement(&context, commConfig.frameLength);
        util::hashElement(&context, commConfig.blockTxRequestTimeout);
        util::hashElement(&context, commConfig.cycleLength);
        util::hashElement(&context, commConfig.desiredDataRate);
        util::hashElement(&context, commConfig.enableLength);
        util::hashElement(&context, commConfig.enablePin);
        util::hashElement(&context, (unsigned int)commConfig.fpga);
        util::hashElement(&context, commConfig.fpgaFailsafePin);
        util::hashElement(&context, commConfig.fpgaFifoSize);
        util::hashElement(&context, commConfig.frameLength);
        util::hashElement(&context, commConfig.initSyncBound);
        util::hashElement(&context, commConfig.initTimeToWait);
        util::hashElement(&context, commConfig.linksTxInterval);
        util::hashElement(&context, commConfig.maxBlockTransferSize);
        util::hashElement(&context, commConfig.maxNumSlots);
        util::hashElement(&context, commConfig.maxTransferSize);
        util::hashElement(&context, commConfig.maxTxBlockSize);
        util::hashElement(&context, commConfig.minBlockTxDelay);
        util::hashElement(&context, commConfig.offsetTimeout);
        util::hashElement(&context, commConfig.offsetTxInterval);
        util::hashElement(&context, commConfig.operateSyncBound);
        util::hashElement(&context, commConfig.postTxGuardLength);
        util::hashElement(&context, commConfig.preTxGuardLength);
        util::hashElement(&context, commConfig.rxDelay);
        util::hashElement(&context, commConfig.rxLength);
        util::hashElement(&context, commConfig.sleepPin);
        util::hashElement(&context, commConfig.slotGuardLength);
        util::hashElement(&context, commConfig.slotLength);
        util::hashElement(&context, commConfig.statusPin);
        util::hashElement(&context, commConfig.statusTxInterval);
        util::hashElement(&context, commConfig.txLength);

        // Platform specific params
        hashPlatformConfig(context);

        /*if (platform == PIXHAWK) {
            // Command fence
            util::hashElement(&context, pixhawk.cmdFence.minLat);
            util::hashElement(&context, pixhawk.cmdFence.maxLat);
            util::hashElement(&context, pixhawk.cmdFence.minLon);
            util::hashElement(&context, pixhawk.cmdFence.maxLon);
            util::hashElement(&context, pixhawk.cmdFence.minAlt);
            util::hashElement(&context, pixhawk.cmdFence.maxAlt);
       
            // Formation Cmd     
            util::hashElement(&context, pixhawk.formationCmd.lat);
            util::hashElement(&context, pixhawk.formationCmd.lon);
            util::hashElement(&context, pixhawk.formationCmd.alt);
            util::hashElement(&context, (unsigned int)pixhawk.formationCmd.shape);
            
            util::hashElement(&context, pixhawk.altSpacing);
            util::hashElement(&context, pixhawk.lateralDrift);
            util::hashElement(&context, pixhawk.altitudeDrift);
            util::hashElement(&context, pixhawk.radius);
            util::hashElement(&context, pixhawk.lineAngle);
            util::hashElement(&context, pixhawk.vehSpacing);
            
        }
        else if (platform == SATFC) {
            util::hashElement(&context, (unsigned int)satFC.satFormationType);
            
            if (satFC.satFormationType == EI_VEC_SEP) {
                util::hashElement(&context, satFC.formSpecs.chiefId);
                for (unsigned int i = 0; i < satFC.formSpecs.nomOrbElems.size(); i++) {
                    util::hashElement(&context, satFC.formSpecs.nomOrbElems[i]);
                }
                util::hashElement(&context, satFC.formSpecs.deltaA);
                util::hashElement(&context, satFC.formSpecs.deltaU);
                for (unsigned int i = 0; i < 2; i++) {
                    util::hashElement(&context, satFC.formSpecs.eccDelta[i]);
                    util::hashElement(&context, satFC.formSpecs.inclDelta[i]);
                    util::hashElement(&context, satFC.formSpecs.deltaE[i]);
                    util::hashElement(&context, satFC.formSpecs.deltaI[i]);
                }
                util::hashElement(&context, satFC.formSpecs.maxEIAngle);
                util::hashElement(&context, satFC.formSpecs.burnSpacing);
            }
        }*/
 
 
        // Get hash value
        unsigned char hash[20];
        SHA1_Final(hash, &context);
        std::vector<uint8_t> output(20);
        std::memcpy(output.data(), hash, 20);
        
        return output;
            
    }
            
    bool NodeConfig::updateParameter(unsigned int paramId, std::vector<uint8_t> & paramValue) { 
        bool updateSuccess = true;

        // Update selected parameter
        switch (paramId) {
            case PARAMID_PARSE_MSG_MAX:
                if (paramValue.size() == 2) {
                    std::memcpy(&parseMsgMax, &paramValue[0], 2);
                }
                else {
                    updateSuccess = false;
                }
                break;
            default: // undefined parameter
                updateSuccess = false;
                break;
            }

        return updateSuccess;
    }
}       
