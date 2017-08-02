
#include "node/nodeConfig.hpp"
#include "node/nodeParams.hpp"
#include "comm/commControl.hpp"
#include "node/nodeControl.hpp"
#include "comm/udpRadio.hpp"
#include <serial/serial.h>
#include <iostream>
#include <fstream>
#include <thread>
#include <unistd.h>

int main(void) {

    std::cout << "Executing comm control." << std::endl;

    // Load node parameters
    node::NodeConfig config("nodeConfig.json");    
    node::NodeParams::loadParams(config);
        
    // Node and comm interface
    comm::RadioConfig rConfig(200,100,100);
    serial::Serial ser_comm("/dev/ttyV2", 57600, serial::Timeout::simpleTimeout(10));
    comm::SerialRadio radio(&ser_comm, rConfig);
    //serial::Serial ser_comm(config.comm, 57600, serial::Timeout::simpleTimeout(10));
    node::NodeInterface nodeInterface;
    
    // Create communication control
    comm::CommControl commControl(0, &radio, &nodeInterface);
    
    // Node and comm interface
    serial::Serial ser_commNode("/dev/ttyV1", 57600, serial::Timeout::simpleTimeout(10));
    comm::SerialRadio radioNode(&ser_commNode, rConfig);
    
    // Create log files
    std::ofstream fcLogFile("test.log");
    std::ofstream nodeLogFile("test2.log");
    std::ofstream cmdLogFile("test3.log");

    // Node Control
    node::NodeControl nodeControl(0, &radioNode, &nodeInterface, &nodeLogFile, &fcLogFile, &cmdLogFile);
    
    // Start execution threads
    nodeControl.execute();
    commControl.execute();    


    while (true) {
        usleep(10*1e6);
    }
    return 0;

}
