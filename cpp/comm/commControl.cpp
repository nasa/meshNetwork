#include "comm/commControl.hpp"
#include "comm/msgProcessor.hpp"
#include "comm/tdmaComm_fpga.hpp"
#include "node/nodeParams.hpp"
#include "comm/xbeeRadio.hpp"
#include "comm/li1Radio.hpp"
#include "comm/fpgaRadio.hpp"
#include "comm/SLIPMsgParser.hpp"
#include "GPIOWrapper.hpp"
#include "node/nodeConfigSupport.hpp"

#include <thread>
#include <vector>

using node::NodeParams;
using std::vector;

namespace comm {

    CommControl::CommControl(unsigned int meshNum, Radio * radioIn, node::NodeInterface * commInterfaceIn) :
        ser(NodeParams::config.meshDevices[meshNum], NodeParams::config.meshBaudrate, serial::Timeout::simpleTimeout(10)),
        commInterface(commInterfaceIn)
    {
        
        // Setup mesh radio
        RadioConfig config;
        config.numBytesToRead = NodeParams::config.uartNumBytesToRead;
        config.rxBufferSize = NodeParams::config.rxBufferSize;
        if (NodeParams::config.commConfig.fpga == true) {
            radio = std::unique_ptr<comm::FPGARadio>(new comm::FPGARadio(&ser, config));
        }
        else {
            switch (NodeParams::config.radios[meshNum]) {
                case node::XBEE:
                    if (NodeParams::config.commConfig.sleepPin.length() > 0) {
                        printf("Xbee sleep pin: %s\n", NodeParams::config.commConfig.sleepPin.c_str());
                        //radio = comm::XbeeRadio(&ser, config, (int)GPIOWrapper::getPin(NodeParams::config.commConfig.sleepPin));
                        radio = std::unique_ptr<comm::Radio>(new comm::XbeeRadio(&ser, config, (int)GPIOWrapper::getPin(NodeParams::config.commConfig.sleepPin)));
                    }
                    else {
                        radio = std::unique_ptr<comm::Radio>(new comm::XbeeRadio(&ser, config));
                    }
                    break;
                case node::LI1:
                    radio = std::unique_ptr<comm::Radio>(new comm::Li1Radio(&ser, config));
                    break;
            }
        }

        // Create mesh comm instance
        switch (NodeParams::config.msgParsers[meshNum]) {
            case node::SLIP_PARSER:
                msgParser = std::unique_ptr<comm::SLIPMsgParser>(new SLIPMsgParser(NodeParams::config.parseMsgMax, 256));
                nodeMsgParser = std::unique_ptr<comm::SLIPMsgParser>(new SLIPMsgParser(NodeParams::config.parseMsgMax, 256));
                break;
            case node::STANDARD_PARSER:
                msgParser = std::unique_ptr<comm::MsgParser>(new MsgParser(NodeParams::config.parseMsgMax));
                nodeMsgParser = std::unique_ptr<comm::MsgParser>(new MsgParser(NodeParams::config.parseMsgMax));
                break;
        }
        tdmaMsgProcessor = TDMAMsgProcessor();
        //commProcessor = CommProcessor(std::vector<MsgProcessor *>({&tdmaMsgProcessor}));

        if (NodeParams::config.commConfig.fpga == true) {
            //comm = std::unique_ptr<comm::TDMAComm_FPGA>(new comm::TDMAComm_FPGA(&commProcessor, radio.get(), msgParser.get()));
            comm = std::unique_ptr<comm::TDMAComm_FPGA>(new comm::TDMAComm_FPGA(std::vector<MsgProcessor *>({&tdmaMsgProcessor}), radio.get(), msgParser.get()));
        }
        else {
            //comm = std::unique_ptr<comm::TDMAComm>(new comm::TDMAComm(&commProcessor, radio.get(), msgParser.get()));
            comm = std::unique_ptr<comm::TDMAComm>(new comm::TDMAComm(std::vector<MsgProcessor *>({&tdmaMsgProcessor}), radio.get(), msgParser.get()));
        }
        
        // Setup node comm interface
        nodeComm = SerialComm(std::vector<MsgProcessor *>(), radioIn, nodeMsgParser.get());        

        // Set node control run time bounds
        if (comm.get()->transmitSlot == 1) {
            maxNodeControlTime = comm.get()->frameLength - comm.get()->slotLength;
            minNodeControlTime = comm.get()->transmitSlot * comm.get()->slotLength;
        }
        else {
            minNodeControlTime = (comm.get()->transmitSlot - 2) * comm.get()->slotLength; // don't run within 1 slot of transmit
            maxNodeControlTime = comm.get()->transmitSlot * comm.get()->slotLength;
        }

    }

    void CommControl::run() {

        TDMAComm * commPtr = comm.get();

        while (true) {
            // Check for loss of node commands
            if (lastNodeCmdTime > 0.0 && (NodeParams::clock.getTime() - lastNodeCmdTime) > 5.0) {
                commPtr->enabled = false;
            }
            else {
                commPtr->enabled = true;
            }  

            // Check for new message from node control
            nodeComm.readMsgs();
            for (auto rawMsg : nodeComm.msgParser->parsedMsgs) {
                printf("Message received\n");
                // Parse NodeThreadMsg from received bytes
                nodeInterface::NodeThreadMsg msg;
                msg.ParseFromString(std::string(rawMsg.begin(), rawMsg.end())); 
                printf("Message timestamp: %f\n", msg.timestamp());       
                // Process message
                if (msg.timestamp() > 0.0 && msg.timestamp() > lastData.timestamp()) { // new message
                    lastData = msg;

                    // Update link status
                    unsigned int ind = 0;
                    //if (NodeParams::config.nodeId == NodeParams::config.gcsNodeId): { // ground node
                    //    ind = NodeParams::config.maxNumNodes - 1;
                    //}
                    //else {
                        ind = NodeParams::config.nodeId - 1;
                    //}
                    unsigned int nodeNum = 0;
                    for (auto linkStatus : msg.linkstatus()) {
                        NodeParams::linkStatus[ind][nodeNum++] = linkStatus;
                    }

                    // Check contents of message
                    //if (msg.datablock().size() > 0) { // data block present
                    //    std::string dataBlock = lastData.datablock();
                    //    comm.sendDataBlock(vector<uint8_t>(dataBlock.begin(),dataBlock.end()));
                    //}
                    if (msg.cmdrelay().size() > 0) { // command relay data
                        //for (auto cmd : msg.cmdrelay()) {
                        //    comm.cmdRelayBuffer.push_back(vector<uint8_t>(cmd.begin(), cmd.end()));
                        //}
                        std::string cmdRelay = msg.cmdrelay();
                        //commPtr->cmdRelayBuffer.push_back(vector<uint8_t>(cmdRelay.begin(), cmdRelay.end()));
                        commPtr->cmdRelayBuffer.insert(commPtr->cmdRelayBuffer.end(), cmdRelay.begin(), cmdRelay.end());
                    }
                    if (msg.cmds().size() > 0) { // cmds received
                        commPtr->cmdBuffer.clear(); // clear existing buffer
                        for (auto cmd : msg.cmds()) {
                            std::string cmdMsg = cmd.msgbytes();
                            /* TODO : UPDATE
                            commPtr->cmdBuffer.push_back(Command(vector<uint8_t>(cmdMsg.begin(), cmdMsg.end()), cmd.txinterval()));*/
                        }
                    }
                }
            }
            nodeComm.msgParser->parsedMsgs.clear(); // clear out messages

            // Execute comm
            commPtr->execute();

            // Manage node control
            if (commPtr->transmitSlot == 1 && commPtr->frameTime > minNodeControlTime && commPtr->frameTime < maxNodeControlTime) {
                commInterface->nodeControlRunFlag = true;
            }
            else if (commPtr->transmitSlot != 1 && commPtr->frameTime < minNodeControlTime && commPtr->frameTime > maxNodeControlTime) {
                commInterface->nodeControlRunFlag = true;
            }
            else { // restrict node control execution
                commInterface->nodeControlRunFlag = false;
            }

            // Send raw received bytes to node control
            if (commPtr->frameTime > commPtr->cycleLength && commPtr->radio->rxBuffer.size() > 0) {
                // Send message to node processing
                vector<uint8_t> rcvdBytes = commPtr->radio->getRxBytes();
                nodeComm.radio->sendMsg(rcvdBytes);
                
                // Clear mesh comm receive buffer
                commPtr->radio->clearRxBuffer();
            }

        }
    }

    void CommControl::execute() {
        std::thread runThread([this] { this->run(); });
        runThread.detach();
    }

}
