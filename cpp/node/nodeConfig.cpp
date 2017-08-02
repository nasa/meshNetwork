#include "node/nodeConfig.hpp"
#include "GPIOWrapper.hpp"
#include <openssl/sha.h>
#include "comm/utilities.hpp"
#include "comm/defines.hpp"
#include "rapidjson/JSON_Wrapper.hpp"

namespace node {
   
    NodeConfig::NodeConfig() {}

    NodeConfig::NodeConfig(std::string configFile) {
        // Load configuration from file
        rapidjson::Document config;
        loadJSONDocument(config, configFile.c_str());
 
        // Load general node parameters
        loadNodeConfig(config);
        
        // Load software interface config
        loadSoftwareInterface(config);       
        
        // Load communication network config
        loadCommConfig(config);
        
        // Calculate hash
        hashSize = calculateHash().size();
    }

    void NodeConfig::loadNodeConfig(rapidjson::Document & config) {
        std::string tempString;
        std::string temp[3];
        int numRet = 0;
        
        if (config.HasMember("node") == false) {
            return;
        }

        const rapidjson::Value & node = config["node"];
        
        get_int(node, "maxNumNodes", maxNumNodes);
        if (readNodeId() == false) {
            // Get node ID from config file
            get_int(node, "nodeId", nodeId);
        }
        get_string(node, "platform", tempString);
        if (tempString.compare("Pixhawk") == 0) {
            platform = PIXHAWK;
        }
        else if (tempString.compare("SatFC") == 0) {
            platform = SATFC;
        }
        else if (tempString.compare("generic") == 0) {
            platform = GENERIC;
        }
        get_double(node, "nodeUpdateTimeout", nodeUpdateTimeout);
        get_double(node, "FCCommWriteInterval", FCCommWriteInterval);
        get_string(node, "FCCommDevice", FCCommDevice);
        get_int(node, "FCBaudrate", FCBaudrate);
        get_double(node, "cmdInterval", cmdInterval);
        get_double(node, "logInterval", logInterval);
       
        // Network config
        get_string(node, "commType", tempString);
        if (tempString.compare("TDMA") == 0) {
            commType = TDMA;
        }
        else if (tempString.compare("Standard") == 0) {
            commType = STANDARD;
        }
        get_int(node, "uartNumBytesToRead", uartNumBytesToRead);
        get_int(node, "parseMsgMax", parseMsgMax);
        get_int(node, "rxBufferSize", rxBufferSize);
        get_int(node, "meshBaudrate", meshBaudrate);
        get_int(node, "numMeshNetworks", numMeshNetworks);
        numRet = get_strings(node, "meshDevices", temp, 3);
        if (numRet > 0) {
            meshDevices.assign(temp, temp + numRet);
        }

        // Radios

        numRet = get_strings(node, "radios", temp, 3);
        for (unsigned int i = 0; i < numRet; i++) {
            if (temp[i].compare("Xbee") == 0) {
                radios.push_back(XBEE);
            }
            else if (temp[i].compare("Li-1") == 0) {
                radios.push_back(LI1);
            }
        }        

        // Message parsers 
        numRet = get_strings(node, "msgParsers", temp, 3);
        for (unsigned int i = 0; i < numRet; i++) {
            if (temp[i].compare("SLIP") == 0) {
                msgParsers.push_back(SLIP_PARSER);
            }
            else if (temp[i].compare("Standard") == 0) {
                msgParsers.push_back(STANDARD_PARSER);
            }
        }         

        // Load platform specific parameters 
        loadPlatformConfig(config);
    }

    void NodeConfig::loadSoftwareInterface(rapidjson::Document & config) {
        if (config.HasMember("interface") == false) {
            return;
        }
        const rapidjson::Value & intConfig = config["interface"];
        get_string(intConfig, "nodeCommIntIP", interface.nodeCommIntIP);
        get_int(intConfig, "commRdPort", interface.commRdPort);
        get_int(intConfig, "commWrPort", interface.commWrPort);
    }

    void NodeConfig::loadCommConfig(rapidjson::Document & config) {
        // Specific comm config
	    if (commType == TDMA) {
            if (config.HasMember("tdmaConfig") == false) {
                return;
            }
            const rapidjson::Value & tdmaConfig = config["tdmaConfig"];
            commConfig = CommConfig(nodeId, TDMA, tdmaConfig);
        }
    }

    bool NodeConfig::readNodeId() {
        if (HAS_GPIO == 0) { // not on a platform with GPIO
            return false;
        }

        // Enable switches
        GPIOWrapper::setupPin("P8_7", GPIOWrapper::INPUT);
        GPIOWrapper::setupPin("P8_8", GPIOWrapper::INPUT);
        GPIOWrapper::setupPin("P8_9", GPIOWrapper::INPUT);
        GPIOWrapper::setupPin("P8_10", GPIOWrapper::INPUT);
         
        // Check switch positions
        if(GPIOWrapper::getValue("P8_7") == 0 && GPIOWrapper::getValue("P8_10") == 0 && GPIOWrapper::getValue("P8_9") == 0) {
            nodeId = 0;
        }
        else if(GPIOWrapper::getValue("P8_7") == 0 && GPIOWrapper::getValue("P8_10") == 0 && GPIOWrapper::getValue("P8_9") == 1) {
            nodeId = 1;
        }
        else if(GPIOWrapper::getValue("P8_7") == 0 && GPIOWrapper::getValue("P8_10") == 1 && GPIOWrapper::getValue("P8_9") == 0) {
            nodeId = 2;
        }
        else if(GPIOWrapper::getValue("P8_7") == 0 && GPIOWrapper::getValue("P8_10") == 1 && GPIOWrapper::getValue("P8_9") == 1) {
            nodeId = 3;
        }
        else if(GPIOWrapper::getValue("P8_7") == 1 && GPIOWrapper::getValue("P8_10") == 0 && GPIOWrapper::getValue("P8_9") == 0) {
            nodeId = 4;
        }
        else if(GPIOWrapper::getValue("P8_7") == 1 && GPIOWrapper::getValue("P8_10") == 0 && GPIOWrapper::getValue("P8_9") == 1) {
            nodeId = 5;
        }
        else if(GPIOWrapper::getValue("P8_7") == 1 && GPIOWrapper::getValue("P8_10") == 1 && GPIOWrapper::getValue("P8_9") == 0) {
            nodeId = 6;
        }
        else if(GPIOWrapper::getValue("P8_7") == 1 && GPIOWrapper::getValue("P8_10") == 1 && GPIOWrapper::getValue("P8_9") == 1) {
            nodeId = 7;
        }

        return true;

    }

    std::string NodeConfig::calculateHash() {
        SHA_CTX context;
        SHA1_Init(&context);

        // Hash non-unique parameters
        util::hashElement(&context, (unsigned int)platform);
        util::hashElement(&context, maxNumNodes);
        util::hashElement(&context, nodeUpdateTimeout);
        util::hashElement(&context, (unsigned int)commType);
        util::hashElement(&context, uartNumBytesToRead);
        util::hashElement(&context, parseMsgMax);
        util::hashElement(&context, rxBufferSize);
        util::hashElement(&context, meshBaudrate);
        util::hashElement(&context, FCBaudrate);
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
        util::hashElement(&context, FCCommDevice);
        util::hashElement(&context, cmdInterval);
        util::hashElement(&context, logInterval);
       
        // Comm params
        util::hashElement(&context, commConfig.preTxGuardLength);
        util::hashElement(&context, commConfig.postTxGuardLength);
        util::hashElement(&context, commConfig.txLength);
        util::hashElement(&context, commConfig.txBaudrate);
        util::hashElement(&context, commConfig.enableLength);
        util::hashElement(&context, commConfig.rxDelay);
        util::hashElement(&context, commConfig.maxNumSlots);
        util::hashElement(&context, commConfig.slotGuardLength);
        util::hashElement(&context, commConfig.desiredDataRate);
        util::hashElement(&context, commConfig.initTimeToWait);
        util::hashElement(&context, commConfig.initSyncBound);
        util::hashElement(&context, commConfig.operateSyncBound);
        util::hashElement(&context, commConfig.offsetTimeout);
        util::hashElement(&context, commConfig.offsetTxInterval);
        util::hashElement(&context, commConfig.statusTxInterval);
        util::hashElement(&context, commConfig.linksTxInterval);
        util::hashElement(&context, commConfig.maxTxBlockSize);
        util::hashElement(&context, commConfig.blockTxRequestTimeout);
        util::hashElement(&context, commConfig.minBlockTxDelay);
        util::hashElement(&context, commConfig.rxLength);
        util::hashElement(&context, commConfig.slotLength);
        util::hashElement(&context, commConfig.frameLength);
        util::hashElement(&context, commConfig.cycleLength);
        util::hashElement(&context, commConfig.maxTransferSize);
        util::hashElement(&context, commConfig.maxBlockTransferSize);

        // Platform specific params
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
        return std::string(reinterpret_cast<char*>(hash));
            
    }
    
    bool NodeConfig::updateParam(ParamName param, std::vector<uint8_t> value) {
        bool retValue = false;

        // Update desired parameter
        switch (param) {
        }

        return retValue;
    } 
}       
