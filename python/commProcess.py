from multiprocessing import Process
import serial, time
from mesh.generic.nodeParams import NodeParams
from mesh.generic.xbeeRadio import XbeeRadio
from mesh.generic.li1Radio import Li1Radio
from mesh.generic.udpRadio import UDPRadio
#from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.hdlcMsg import HDLCMsg
from mesh.generic.slipMsg import SLIPMsg
from mesh.generic.msgParser import MsgParser
from mesh.generic.serialComm import SerialComm    
from mesh.generic.meshController import MeshController
from mesh.generic.multiProcess import getNewMsgs
from mesh.interface.nodeInterface_pb2 import NodeThreadMsg, MeshMsg, MeshMsgs

class CommProcess(Process):
    def __init__(self, configFile, meshNum, runFlag):
        super().__init__(name="CommProcess")        

        # Node control run flag
        self.nodeControlRunFlag = runFlag

        # Configuration
        self.nodeParams = NodeParams(configFile=configFile)

        # Node/Comm interface
        interfaceConfig = {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': self.nodeParams.config.rxBufferSize, 'ipAddr': self.nodeParams.config.interface['nodeCommIntIP'], 'readPort': self.nodeParams.config.interface['commRdPort'], 'writePort': self.nodeParams.config.interface['commWrPort']}
        #self.interface = SerialComm([], UDPRadio(interfaceConfig), SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax}))
        self.interface = SerialComm([], self.nodeParams, UDPRadio(interfaceConfig), MsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax}, SLIPMsg(256))) # UDP connection to node control process

        # Interprocess data package (Google protocol buffer interface to node control process)
        self.dataPackage = NodeThreadMsg()
        self.cmdTxLog = {}
        self.lastNodeCmdTime = []

        ## Create comm object
        # Serial connection
        ser = None
        try:
            ser = serial.Serial(port = self.nodeParams.config.meshDevices[meshNum], baudrate=self.nodeParams.config.meshBaudrate, timeout=0)
        except serial.SerialException:
            pass

        # Radio
        radioConfig = {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': self.nodeParams.config.rxBufferSize}
        if (self.nodeParams.config.commConfig['fpga'] == True):
            from mesh.generic.fpgaRadio import FPGARadio
            radio = FPGARadio(ser, radioConfig)
        else:
            if self.nodeParams.config.radios[meshNum] == "Xbee":
                radio = XbeeRadio(ser, radioConfig, "P8_12")
            elif self.nodeParams.config.radios[meshNum] == "Li-1":
                radio = Li1Radio(ser, radioConfig)
    
        # Message parser
        parserConfig = {'parseMsgMax': self.nodeParams.config.parseMsgMax}
        if self.nodeParams.config.msgParsers[meshNum] == "HDLC":
            msgParser = MsgParser(parserConfig, HDLCMsg(256))
        elif self.nodeParams.config.msgParsers[meshNum] == "standard":
            msgParser = MsgParser(parserConfig)


        # Create comm and mesh interface
        if (self.nodeParams.config.commConfig['fpga'] == True):
            from mesh.generic.tdmaComm_fpga import TDMAComm_FPGA as TDMAComm
        else:    
            from mesh.generic.tdmaComm import TDMAComm
        
        self.comm = TDMAComm([], radio, msgParser, self.nodeParams)
        self.meshController = MeshController(self.nodeParams, self.comm)

        # Node control run time bounds
        if (self.nodeParams.config.commConfig['fpga'] == False): # only needed for software-controlled comm
            if self.comm.transmitSlot == 1: # For first node, run any time after transmit slot
                self.maxNodeControlTime = self.comm.frameLength - self.comm.slotLength
                self.minNodeControlTime = self.comm.slotLength
            else: # For other nodes, avoid running near transmit slot
                self.minNodeControlTime = (self.comm.transmitSlot-2) * self.comm.slotLength # don't run within 1 slot of transmit 
                self.maxNodeControlTime = self.comm.transmitSlot * self.comm.slotLength
            #self.minNodeControlTime = 0.8*((self.comm.transmitSlot-1) * self.comm.slotLength)

    def run(self):
        while 1:
            try:
                # Check for loss of node commands
                if self.lastNodeCmdTime and (time.time() - self.lastNodeCmdTime) > 5.0:
                    # No node interface link so disable comm 
                    self.comm.enabled = False
                else:
                    self.comm.enabled = True
                
                # Check for new messages from node control process
                self.interface.readMsgs()
                
                # Parse protocol buffer messages 
                for msg in self.interface.msgParser.parsedMsgs: # Process received messages
                    nodeMsg = NodeThreadMsg()
                    nodeMsg.ParseFromString(msg)
                    
                    # Check if new message
                    if (nodeMsg.timestamp > 0.0 and nodeMsg.timestamp > self.dataPackage.timestamp):
                        self.lastNodeCmdTime = time.time()
                        self.dataPackage = nodeMsg
                   
     
                        # Parse messages for transmission
                        if (nodeMsg.cmds): # commands received
                            for cmd in nodeMsg.cmds:
                                self.meshController.sendMsg(cmd.destId, cmd.msgBytes)
                
                self.interface.msgParser.parsedMsgs = [] # clear out processed parsed messages
                
                # Execute network
                self.meshController.execute()

                # Managed node control run flag (only when comm is running in software)
                if (self.nodeParams.config.commConfig['fpga'] == False):
                    if self.comm.transmitSlot == 1 and (self.comm.frameTime > self.minNodeControlTime and self.comm.frameTime < self.maxNodeControlTime):
                        self.nodeControlRunFlag.value = 1
                    elif self.comm.transmitSlot != 1 and (self.comm.frameTime < self.minNodeControlTime or self.comm.frameTime > self.maxNodeControlTime):
                        self.nodeControlRunFlag.value = 1
                    else: # restrict node control process running
                        self.nodeControlRunFlag.value = 0
                
                # Send any received bytes to node control process
                #if (self.nodeParams.config.commConfig['fpga'] == False or self.comm.frameTime > self.comm.cycleLength):
                msgs = self.meshController.getMsgs()
                    
                # Package messages and pass to control thread
                meshMsgs = MeshMsgs()
                if (msgs):
                    for msg in msgs:
                        meshMsg = MeshMsg()
                        meshMsg.msgType = msg.msgType
                        meshMsg.cmdId = msg.cmdId
                        meshMsg.status = msg.status
                        meshMsg.msgBytes = msg.msgBytes
                        
                        meshMsgs.append(msgMsg)
                        
                meshMsgsBytes = meshMsgs.SerializeToString()        

                self.interface.sendBytes(meshMsgsBytes) 
                
            except KeyboardInterrupt:
                print("\nTerminating Comm Process.")
                self.terminate()
