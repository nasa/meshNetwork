import serial
import os, time, sys
from natsort import natsorted
from multiprocessing import Value

from mesh.generic.nodeParams import NodeParams
from nodeControlProcess import NodeControlProcess

# Execute communication and node control as separate processes
if __name__ == '__main__':
    # Node control shared run flag
    runFlag = Value('B', 1)

    # Load network node configuration
    configFile = 'nodeConfig.json'
    nodeParams = NodeParams(configFile=configFile)
    
    # Create node communication processes (one process per network)
    if nodeParams.config.commConfig['fpga']:
        from commProcess_fpga import CommProcess
    else:
        from commProcess import CommProcess
    commProcesses = [None]*nodeParams.config.numMeshNetworks
    for i in range(nodeParams.config.numMeshNetworks):
        commProcesses[i] = CommProcess(configFile, i, runFlag)
        commProcesses[i].daemon = True

    # Create node control process
    nodeControlProcess = NodeControlProcess(configFile, runFlag)
    nodeControlProcess.daemon = True # run node control as a daemon

    # Start processes
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
        
