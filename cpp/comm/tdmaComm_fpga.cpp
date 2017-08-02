#include "comm/tdmaComm_fpga.hpp"
#include "node/nodeParams.hpp"
#include <iostream>
#include <string>
#include <unistd.h>
#include <memory>
#include "utilities.hpp"
#include "comm/tdmaCmds.hpp"

using node::NodeParams;
using std::unique_ptr;

namespace comm {

    TDMAComm_FPGA::TDMAComm_FPGA(CommProcessor * commProcessorIn, Radio * radioIn, MsgParser * msgParserIn) :
        TDMAComm(commProcessorIn, radioIn, msgParserIn),
        transmitInterval(1.0/NodeParams::config.commConfig.desiredDataRate),
        lastTransmitTime(-1.0)
    {
    }

    void TDMAComm_FPGA::executeTDMAComm(double currentTime) {
        // Read any new bytes
        readMsg();    

        // Send current message data
        if (util::getTime() - lastTransmitTime > transmitInterval) {
            lastTransmitTime = util::getTime();
            tdmaMode = TDMA_TRANSMIT;
            sendMsg();
        }
        else { // wait for next transmit time
            tdmaMode = TDMA_RECEIVE;
        }
    }

    void TDMAComm_FPGA::init(double currentTime) {
        initMesh(currentTime);
    }

    void TDMAComm_FPGA::initMesh(double currentTime) {
        // Create TDMA comm messages
        tdmaCmds[TDMACmds::LinkStatus] = unique_ptr<Command>(new TDMA_LinkStatus(NodeParams::linkStatus[NodeParams::config.nodeId-1], CmdHeader(TDMACmds::LinkStatus, NodeParams::config.nodeId), NodeParams::config.commConfig.linksTxInterval));
        
        //if (NodeParams::config.nodeId != 0) { // do not do for ground node
        tdmaCmds[TDMACmds::TimeOffset] = unique_ptr<Command>(new TDMA_TimeOffset(NodeParams::nodeStatus[NodeParams::config.nodeId-1].timeOffset, CmdHeader(TDMACmds::TimeOffset, NodeParams::config.nodeId), NodeParams::config.commConfig.offsetTxInterval));
        //}

        inited = true;
        std::cout << "Node " << NodeParams::config.nodeId << " - Initializing comm" << std::endl;
    } 

    void TDMAComm_FPGA::sleep() {
        // No actions for sleep
    }

    bool TDMAComm_FPGA::readMsg() {
        // Read from FPGA
        radio->readBytes(true);

        return true;
    }


}
