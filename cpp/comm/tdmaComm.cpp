#include "comm/tdmaComm.hpp"
#include "node/nodeParams.hpp"
#include "comm/utilities.hpp"
#include "comm/tdmaCmds.hpp"
#include "comm/command.hpp"
#include "comm/tdmaCmds.hpp"
#include "comm/radio.hpp"
#include "comm/SLIPMsg.hpp"
#include <iostream>
#include <cmath>
#include <string>
#include <unistd.h>
#include <thread>

using std::vector;
using std::unique_ptr;
using node::NodeParams;

namespace comm {

    TDMAComm::TDMAComm(CommProcessor * commProcessorIn, Radio * radioIn, MsgParser * msgParserIn) :
        Comm(commProcessorIn, radioIn, msgParserIn),
        enabled(true),
        transmitSlot(NodeParams::config.commConfig.transmitSlot),
        frameLength(NodeParams::config.commConfig.frameLength),
        slotLength(NodeParams::config.commConfig.slotLength),
        frameTime(0.0),
        cycleLength(NodeParams::config.commConfig.cycleLength),
        tdmaMode(TDMA_SLEEP),
        frameStartTime(0.0),
        maxNumSlots(NodeParams::config.commConfig.maxNumSlots),
        enableLength(NodeParams::config.commConfig.enableLength),
        slotTime(0.0),
        slotNum(1),
        slotStartTime(0.0),
        inited(false),
        initTimeToWait(NodeParams::config.commConfig.initTimeToWait),
        initStartTime(-1.0),
        beginTxTime(enableLength + NodeParams::config.commConfig.preTxGuardLength),
        endTxTime(beginTxTime + NodeParams::config.commConfig.txLength),
        transmitComplete(false),
        beginRxTime(enableLength),
        endRxTime(beginRxTime + NodeParams::config.commConfig.rxLength),
        rxLength(NodeParams::config.commConfig.rxLength),
        rxReadTime(beginTxTime + NodeParams::config.commConfig.rxDelay),
        receiveComplete(false),
        rxBufferReadPos(0),
        lastModeChangeSlot(0)

    {
        // Reset comm start time
        NodeParams::commStartTime = -1.0;

        // Block Tx init *** EXPERIMENTAL ***
        resetBlockTxStatus();
        clearDataBlock();

    }

    void TDMAComm::execute() {
        double currentTime = util::getTime();

        // Initialize mesh network
        if (inited == false) {
            init(currentTime);
            return;
        }
        else {
            executeTDMAComm(currentTime);
        }
        
    }

    int TDMAComm::updateFrameTime(double currentTime) {
        // Update frame time
        frameTime = currentTime - frameStartTime;
        if (frameTime >= frameLength) { // Start new frame
            syncTDMAFrame(currentTime);
        }

        // Execute comm algorithms
        if (frameTime < cycleLength) {
            return 0;
        }
	    else {
            return 1;
	    }
    }

    void TDMAComm::executeTDMAComm(double currentTime) {
        // Check for block transfers
        monitorBlockTx();

        // Update frame time
        int frameStatus = updateFrameTime(currentTime);
        if (frameStatus == 1) { // sleep
            sleep();
            return;
        }

        // Check for mode updates
        updateMode(frameTime);

        // Perform mode specific behavior
        switch (tdmaMode) {
            case TDMA_SLEEP:
                // Set radio to sleep mode
                radio->setMode(SLEEP);
                break;

            case TDMA_INIT:
                // Prepare radio to receive or transmit
                if (slotNum == transmitSlot) {
                    // Set radio to transmit mode
                    radio->setMode(TRANSMIT);
                }
                else {
                    // Set radio to receive mode
                    radio->setMode(RECEIVE);
                }
                break;

            case TDMA_RECEIVE:
                // Read data if TDMA message end not yet found
                if (receiveComplete == false && slotTime >= rxReadTime) {
                    radio->setMode(RECEIVE);
                    receiveComplete = readMsg();
                    if (receiveComplete == true) {
                        // Set radio to sleep
                        radio->setMode(SLEEP);
                    }
                }
                break;

            case TDMA_TRANSMIT:
                // Send data
                if (transmitComplete == false) {
                    radio->setMode(TRANSMIT);
                    sendMsg();
                }
                else { // Set radio to sleep
                    radio->setMode(SLEEP);
                }
                break;

            case TDMA_FAILSAFE: // Read only failsafe mode
                // Enable radio in receive mode and read data
                radio->setMode(RECEIVE);
                readMsg();
                break;

            case TDMA_BLOCKRX: // Block receive mode
                radio->setMode(RECEIVE);
                readMsg();
                break;

            case TDMA_BLOCKTX: // Block transmit mode
                radio->setMode(TRANSMIT);
                sendBlock();
                break;
        }
    }

    void TDMAComm::init(double currentTime) {
        if (NodeParams::commStartTime < 0.0) { // Mesh not initialized
                initComm(currentTime);
                return;
        }
        else { // Join existing network
            initMesh();
        }

    }

    void TDMAComm::initMesh(double currentTime) {
        // Create TDMA comm messages
        int flooredStartTime = floor(NodeParams::commStartTime);
        tdmaCmds[TDMACmds::MeshStatus] = unique_ptr<Command>(new TDMA_MeshStatus(flooredStartTime, NodeParams::tdmaStatus, CmdHeader(TDMACmds::MeshStatus), NodeParams::config.commConfig.statusTxInterval));
        tdmaCmds[TDMACmds::LinkStatus] = unique_ptr<Command>(new TDMA_LinkStatus(NodeParams::linkStatus[NodeParams::config.nodeId-1], CmdHeader(TDMACmds::LinkStatus, NodeParams::config.nodeId), NodeParams::config.commConfig.linksTxInterval));
        
        //if (NodeParams::config.nodeId != 0) { // do not do for ground node
        tdmaCmds[TDMACmds::TimeOffset] = unique_ptr<Command>(new TDMA_TimeOffset(NodeParams::nodeStatus[NodeParams::config.nodeId-1].timeOffset, CmdHeader(TDMACmds::TimeOffset, NodeParams::config.nodeId), NodeParams::config.commConfig.offsetTxInterval));
        //}

        // Determine where in frame mesh network currently is
        syncTDMAFrame(currentTime);

        inited = true;
        std::cout << "Node " << NodeParams::config.nodeId << " - Initializing comm" << std::endl;
    }

    void TDMAComm::initComm(double currentTime) {
        if (initStartTime < 0.0) {
            // Start mesh initialization timer
            initStartTime = currentTime;
            std::cout << "Node " << NodeParams::config.nodeId << " - Starting initialization timer" << std::endl;
            return;
        }
        else if ((currentTime - initStartTime) >= initTimeToWait) { // init timer expired
            // Assume no existing mesh and initialize network
            NodeParams::commStartTime = floor(currentTime);
            std::cout << "Initializing new mesh network" << std::endl;
            initMesh();
        }
        else { // Wait for initialization timer to lapse
            // Turn on radio and check for comm messages
            checkForInit();
        }
    }

    void TDMAComm::checkForInit() {
        // Look for tdma status message
        radio->setMode(RECEIVE);
        readBytes(true);
        if (radio->rxBuffer.size() > 0) {
            parseMsgs();
            while (msgParser->parsedMsgs.size() > 0) {

                std::vector<uint8_t> msg;
                msgParser->getMsg(msg);
                uint8_t cmdId = msg[0]; // first element should be the command ID
                if (cmdId == TDMACmds::MeshStatus) {
                    MsgProcessorArgs args;
                    args.relayBuffer = &cmdRelayBuffer;
                    processMsg(msg, args);
                }
            }
        }
    }

    void TDMAComm::syncTDMAFrame(double currentTime) {
        // Determine where in the frame the mesh network current is
        frameTime = std::fmod(currentTime - NodeParams::commStartTime, frameLength);
        frameStartTime = currentTime - frameTime;

        // Update periodic mesh messages
        updateMeshMsgs();       
 
        // Reset buffer read position
        rxBufferReadPos = 0;

        // Check for TDMA failsafe
        std::thread offsetThread(NodeParams::checkTimeOffset, FormationClock::invalidOffset);
        offsetThread.detach();
        //NodeParams::checkTimeOffset();
    }

    void TDMAComm::updateMeshMsgs() {
        // Update TDMA status
        if (tdmaCmds.find(TDMACmds::MeshStatus) != tdmaCmds.end()) {
            dynamic_cast<TDMA_MeshStatus *>(tdmaCmds[TDMACmds::MeshStatus].get())->status = NodeParams::tdmaStatus;
        }

        // Update time offset
        if (tdmaCmds.find(TDMACmds::TimeOffset) != tdmaCmds.end()) {
            dynamic_cast<TDMA_TimeOffset *>(tdmaCmds[TDMACmds::TimeOffset].get())->timeOffset = NodeParams::nodeStatus[NodeParams::config.nodeId-1].timeOffset;
        }

        // Update links status
        if (tdmaCmds.find(TDMACmds::LinkStatus) != tdmaCmds.end()) {
            dynamic_cast<TDMA_LinkStatus *>(tdmaCmds[TDMACmds::LinkStatus].get())->linkStatus = NodeParams::linkStatus[NodeParams::config.nodeId-1];
        }
        
    }

    void TDMAComm::sleep() {
        // Sleep until end of frame
        double remainingFrameTime = frameLength - (util::getTime() - frameStartTime);
        if (remainingFrameTime > 0.010) {
            usleep((remainingFrameTime - 0.010)*1.0e6);
        }
        else if (remainingFrameTime < -0.01) { // significant frame exceedance
            std::cout << "WARNING: Frame length exceeded!" << remainingFrameTime << std::endl;
        }
    }

    void TDMAComm::updateMode(double frameTime) {
        // Update slot
        resetTDMASlot(frameTime);

        // Check for TDMA failsafe
        if (NodeParams::tdmaFailsafe == true) {
            setTDMAMode(TDMA_FAILSAFE);
            return;
        }

        // Check for end of cycle
        if (frameTime >= cycleLength) {
            setTDMAMode(TDMA_SLEEP);
            return;
        }

        // Check for block transmit
        if (blockTxStatus.status == BLOCKTX_ACTIVE) {
            if (blockTxStatus.txNode == NodeParams::config.nodeId) { // this node is transmitting
                setTDMAMode(TDMA_BLOCKTX);
            }
            else { // this node is receiving
                setTDMAMode(TDMA_BLOCKRX);
            }
            return;
        }

        // Normal cycle sequence
        if (slotTime < enableLength) { // Initialize comm at start of slot
            setTDMAMode(TDMA_INIT);
        }
        else {
            if (slotNum == transmitSlot) { // transmit slot
                if (slotTime >= beginTxTime) {
                    if (slotTime < endTxTime) { // begin transmitting
                        setTDMAMode(TDMA_TRANSMIT);
                    }
                    else { // sleep
                        setTDMAMode(TDMA_SLEEP);
                    }
                }
            }
            else { // receive slot
                if (slotTime < endRxTime) { // begin receiving
                    setTDMAMode(TDMA_RECEIVE);
                }
                else { // sleep
                    setTDMAMode(TDMA_SLEEP);
                }
            }
        }
    }

    void TDMAComm::setTDMAMode(TDMAMode mode) {
        if (tdmaMode != mode || lastModeChangeSlot != slotNum) { // not current mode in this slot
            lastModeChangeSlot = slotNum;
            tdmaMode = mode;
            if (mode == TDMA_RECEIVE) {
                receiveComplete = false;
            }
            else if (mode == TDMA_TRANSMIT) {
                transmitComplete = false;
            }
        }
    }

    void TDMAComm::resetTDMASlot(double frameTime, int slotNumIn) {
        // Reset slot number
        if (slotNumIn > 0) { // slot number provided
            if (slotNum <= maxNumSlots) {
                slotNum = slotNumIn;
            }
        }
        else { // determine slot number
            if (frameTime < cycleLength) { // during cycle
                slotNum = (int)(frameTime / slotLength) + 1;
            }
            else { // sleep period
                slotNum = maxNumSlots;
            }
        }

        // Set slot time parameters
        slotStartTime = (slotNum - 1) * slotLength;
        slotTime = frameTime - slotStartTime;

    }

    void TDMAComm::sendMsg() {
        if (enabled == false) { // Don't transmit when disabled
            return;
        }

        // Send periodic TDMA commands
        sendTDMACmds();

        // Transmit
        if (tdmaMode == TDMA_TRANSMIT) {
            // Send any buffered commands
            vector<uint8_t> nonRepeatCmds;
            for (unsigned int i = 0; i < cmdBuffer.size(); i++) {
                bufferTxMsg(cmdBuffer[i].packed); // encode and buffer command
                cmdBuffer[i].lastTxTime = util::getTime(); // update last transmit time
                if (cmdBuffer[i].txInterval == 0.0) { // non-repeating command
                    nonRepeatCmds.push_back(i);
                }
            }
            // Remove non-repeating commands
            for (unsigned int i = 0; i < nonRepeatCmds.size(); i++) {
                cmdBuffer.erase(cmdBuffer.begin() + nonRepeatCmds[i]);
            }

            // Check for commands to relay
            if (cmdRelayBuffer.size() > 0) {
                // Send buffer and then clear
                for (unsigned int i = 0; i < cmdRelayBuffer.size(); i++) {
                    radio->bufferTxMsg(cmdRelayBuffer[i]); // buffer raw command relay buffer
                }
                cmdRelayBuffer.clear();
            }

            // Send tx buffer
            vector<uint8_t> temp = {(uint8_t)SLIP_END_TDMA};
            radio->bufferTxMsg(temp); // add TDMA END byte
            printf("%f - Transmitting %lu bytes\n", util::getTime(), radio->txBuffer.size());
            radio->sendBuffer(NodeParams::config.commConfig.maxTransferSize);

            // End transmit period
            transmitComplete = true;
        }

    }

    bool TDMAComm::readMsg() {
        // Read from radio and look for end of transmission byte
        radio->readBytes(true);
        for (unsigned int i = rxBufferReadPos; i < radio->rxBuffer.size(); i++) {
            rxBufferReadPos++;
            if (radio->rxBuffer[i] == SLIP_END_TDMA) { // end of transmission
                return true;
            }
        }

        return false; // end of transmission not found
    }

    void TDMAComm::sendTDMACmds() {
        double timestamp = util::getTime();

        // Update time offset
        if (tdmaCmds.find(TDMACmds::TimeOffset) != tdmaCmds.end()) {
            dynamic_cast<TDMA_TimeOffset *>(tdmaCmds[TDMACmds::TimeOffset].get())->timeOffset = NodeParams::nodeStatus[NodeParams::config.nodeId-1].timeOffset;
        }
    
        for (auto iter = tdmaCmds.begin(); iter != tdmaCmds.end(); iter++) {
            if (ceil(timestamp*100)/100.0 >= ceil((iter->second->lastTxTime + iter->second->txInterval)*100)/100.0) { // only compare down to milliseconds
            //if (timestamp - iter->second->lastTxTime) >= iter->second->txInterval) {
                vector<uint8_t> msg = iter->second->pack(timestamp);
                bufferTxMsg(msg);
            }
        }
    }

    void TDMAComm::sendBlock() {
    }

    void TDMAComm::resetBlockTxStatus() {
    }

    void TDMAComm::monitorBlockTx() {
    }

    void TDMAComm::clearDataBlock() {
    }

    bool TDMAComm::sendDataBlock(vector<uint8_t> dataBlock) {
        return false;
    }

    void TDMAComm::populateBlockResponseList() {
    }

    void TDMAComm::checkBlockResponse() {
    }

}
