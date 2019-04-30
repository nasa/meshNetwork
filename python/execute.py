import serial
import os, time, sys
from multiprocessing import Value
from mesh.generic.nodeParams import NodeParams
from commProcess import CommProcess
from nodeControlProcess import NodeControlProcess

# Example of how to execute and communicate between TDMA comm element and generic node control software
if __name__ == '__main__':
    # Node control shared run flag 
    # Used by comm process to trigger node control software.  Since comm process is time critical, flags keeps node control from unintentionally blocking comm.
    runFlag = Value('B', 1)

    # Load network node configuration
    configFile = 'nodeConfig.json'
    nodeParams = NodeParams(configFile=configFile)
    
    # Create node communication processes (one process per network)
    commProcesses = [None]*nodeParams.config.numMeshNetworks
    for i in range(nodeParams.config.numMeshNetworks):
        commProcesses[i] = CommProcess(configFile, i, runFlag)
        commProcesses[i].daemon = True 

    # Create node control process
    nodeControlProcess = NodeControlProcess(configFile, runFlag)
    nodeControlProcess.daemon = True

    # Start all processes
    for process in commProcesses:
        process.start()

    nodeControlProcess.start()

    # Monitor running processes and look for termination signal from user
    while 1:
        try:
            time.sleep(10.0)
        except KeyboardInterrupt:
            print("Stopping program")
            for process in commProcesses:
                process.terminate()
            nodeControlProcess.terminate()
            break
        
