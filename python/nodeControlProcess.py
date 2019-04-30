from multiprocessing import Process
import serial, time, random
from mesh.generic.nodeParams import NodeParams
from mesh.generic.radio import Radio
from mesh.generic.udpRadio import UDPRadio
#from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.slipMsg import SLIPMsg
from mesh.generic.msgParser import MsgParser
from switch import switch

class NodeControlProcess(Process):
    def __init__(self, configFile, runFlag):
        super().__init__(name="NodeControlProcess", )       

        # Run flag
        self.runFlag = runFlag
    
        # Configuration
        nodeParams = NodeParams(configFile=configFile)
    

        # Create radios
        radios = []
        radioConfig = {'uartNumBytesToRead': nodeParams.config.uartNumBytesToRead, 'rxBufferSize': nodeParams.config.rxBufferSize, 'ipAddr': nodeParams.config.interface['nodeCommIntIP'], 'readPort': nodeParams.config.interface['commWrPort'], 'writePort': nodeParams.config.interface['commRdPort']}
        for i in range(nodeParams.config.numMeshNetworks):
            radios.append(UDPRadio(radioConfig)) # connection to communication processes

        # Create message parsers
        msgParsers = []
        parserConfig = {'parseMsgMax': nodeParams.config.parseMsgMax}
        for i in range(nodeParams.config.numMeshNetworks):
            #if nodeParams.config.msgParsers[i] == "SLIP":
                msgParsers.append(MsgParser(parserConfig, SLIPMsg(256)))
            #elif nodeParams.config.msgParsers[i] == "standard":
            #    msgParsers.append(MsgParser(parserConfig))
    
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
                from mesh.generic.serialComm import SerialComm  
                from demoController import DemoController  
                from mesh.generic.nodeExecutive import NodeExecutive
                
                print("Initializing generic node")

                # Initialize communication variables
                for i in range(nodeParams.config.numMeshNetworks):
                    nodeComm[i] = SerialComm([], nodeParams, radios[i], msgParsers[i])
        
                # Flight computer comm
                if (nodeParams.config.FCCommDevice):
                    FCSer = serial.Serial(port = nodeParams.config.FCCommDevice, baudrate=nodeParams.config.FCBaudrate, timeout=0)
                    FCRadio = Radio(FCSer, radioConfig)
                    FCMsgParser = MsgParser(parserConfig, SLIPMsg(256))
                    FCComm = SerialComm([], FCRadio, FCMsgParser, nodeParams)
                else:
                    FCComm = None
    
                # Node controller
                self.nodeController = DemoController(nodeParams, self.nodeCommLogFile)

                # Node executive
                self.nodeExecutive = NodeExecutive(nodeParams, self.nodeController, nodeComm, FCComm, self.FCLogFile)
                

    def run(self):
        # Execute node control
        while 1:
            try:
                # Run if flag is set or comm is running on FPGA
                if self.nodeExecutive.nodeParams.config.commConfig['fpga'] == True or self.runFlag.value == 1: 
                    # Run node executive            
                    #print("Node execution start time:", time.time())
                    self.nodeExecutive.executeNodeSoftware()
                    
                    #self.runFlag.value = 0 # reset run flag
                
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
