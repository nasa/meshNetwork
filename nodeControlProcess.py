from multiprocessing import Process
import serial, time, random
from mesh.generic.nodeParams import NodeParams
from mesh.generic.radio import Radio
from mesh.generic.udpRadio import UDPRadio
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.msgParser import MsgParser
from switch import switch

class NodeControlProcess(Process):
    def __init__(self, configFile, runFlag):
        super().__init__(name="NodeControlProcess", )       

        # Run flag
        self.runFlag = runFlag
    
        # Configuration
        nodeParams = NodeParams(configFile=configFile)
    
        # Flight computer serial port
        FCSer = serial.Serial(port = nodeParams.config.FCCommDevice, baudrate=nodeParams.config.FCBaudrate, timeout=0)

        # Create radios
        radios = []
        radioConfig = {'uartNumBytesToRead': nodeParams.config.uartNumBytesToRead, 'rxBufferSize': nodeParams.config.rxBufferSize, 'ipAddr': nodeParams.config.interface['nodeCommIntIP'], 'readPort': nodeParams.config.interface['commWrPort'], 'writePort': nodeParams.config.interface['commRdPort']}
        for i in range(nodeParams.config.numMeshNetworks):
            radios.append(UDPRadio(radioConfig)) # connection to communication processes
        FCRadio = Radio(FCSer, radioConfig)

        # Create message parsers
        msgParsers = []
        parserConfig = {'parseMsgMax': nodeParams.config.parseMsgMax}
        for i in range(nodeParams.config.numMeshNetworks):
            if nodeParams.config.msgParsers[i] == "SLIP":
                msgParsers.append(SLIPMsgParser(parserConfig))
            elif nodeParams.config.msgParsers[i] == "standard":
                msgParsers.append(MsgParser(parserConfig))
        FCMsgParser = SLIPMsgParser(parserConfig)
    
        # Open logfiles
        currentTime = str(time.time())
        FCLogFilename = 'fc_' + currentTime + '.log'
        self.FCLogFile = open(FCLogFilename,'w')
        nodeCommLogFilename = 'node_' + currentTime + '.log'
        self.nodeCommLogFile = open(nodeCommLogFilename,'w')
    
        # Failsafe LED interval
        failsafeLEDTime = 1.0 # seconds
        failsafeLEDOnTime = -1.0
        failsafeLEDOn = False

        # Initialize node and flight computer communication variables
        nodeComm = [[]]*nodeParams.config.numMeshNetworks
        FCComm = []

        # Instantiate specific node software
        self.nodeController = []
        self.nodeExecutive = []
        for case in switch(nodeParams.config.platform): # Platform specific initializations
            if case("SpecificNode"):
                pass
            else: # generic node
                from mesh.generic.nodeComm import NodeComm  
                from mesh.generic.nodeController import NodeController  
                from mesh.generic.nodeExecutive import NodeExecutive
                
                print("Initializing generic node")

                # Initialize communication variables
                for i in range(nodeParams.config.numMeshNetworks):
                        nodeComm[i] = NodeComm([], radios[i], msgParsers[i], nodeParams)
                FCComm = NodeComm([], FCRadio, FCMsgParser, nodeParams)
    
                # Node controller
                self.nodeController = NodeController(nodeParams, self.nodeCommLogFile)

                # Node executive
                self.nodeExecutive = NodeExecutive(nodeParams, self.nodeController, nodeComm, FCComm, self.FCLogFile)
                

    def run(self):
        # Execute node control
        while 1:
            try:
                if self.runFlag.value == 1: 
                    # Run node executive            
                    #print("Node execution start time:", time.time())
                    self.nodeExecutive.executeNodeSoftware()
                    #print("Node execution end time:", time.time())
                    self.runFlag.value = 0 # reset run flag
                
                    # Minimum delay time between executions
                    time.sleep(0.5)
                
                else:
                    #print(time.time(), "- Can't run")
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nTerminating Node Control Process.")
                self.terminate()

    def terminate(self):
        # Close logfiles
        self.FCLogFile.close()
        self.nodeCommLogFile.close()
