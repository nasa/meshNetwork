from multiprocessing import Process
import serial, time
from mesh.generic.nodeParams import NodeParams
from mesh.generic.xbeeRadio import XbeeRadio
from mesh.generic.li1Radio import Li1Radio
from mesh.generic.udpRadio import UDPRadio
from mesh.generic.slipMsgParser import SLIPMsgParser
from mesh.generic.msgParser import MsgParser
from mesh.generic.tdmaComm import TDMAComm    
from mesh.generic.serialComm import SerialComm    
from mesh.generic.multiProcess import getNewMsgs
from mesh.interface.nodeInterface_pb2 import NodeThreadMsg

class CommProcess(Process):
    def __init__(self, configFile, meshNum, runFlag):
        super().__init__(name="CommProcess")        

        # Node control run flag
        self.nodeControlRunFlag = runFlag

        # Configuration
        self.nodeParams = NodeParams(configFile=configFile)

        # Node/Comm interface
        interfaceConfig = {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': self.nodeParams.config.rxBufferSize, 'ipAddr': self.nodeParams.config.interface['nodeCommIntIP'], 'readPort': self.nodeParams.config.interface['commRdPort'], 'writePort': self.nodeParams.config.interface['commWrPort']}
        self.interface = SerialComm([], UDPRadio(interfaceConfig), SLIPMsgParser({'parseMsgMax': self.nodeParams.config.parseMsgMax}))

        # Interprocess data package
        self.dataPackage = NodeThreadMsg()
        self.cmdTxLog = {}
        self.lastNodeCmdTime = []

        ## Create comm object
        # Serial connection
        ser = serial.Serial(port = self.nodeParams.config.meshDevices[meshNum], baudrate=self.nodeParams.config.meshBaudrate, timeout=0)

        # Radio
        radioConfig = {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': self.nodeParams.config.rxBufferSize}
        if self.nodeParams.config.radios[meshNum] == "Xbee":
            radio = XbeeRadio(ser, radioConfig, "P8_12")
        elif self.nodeParams.config.radios[meshNum] == "Li-1":
            radio = Li1Radio(ser, radioConfig)
    
        # Message parser
        parserConfig = {'parseMsgMax': self.nodeParams.config.parseMsgMax}
        if self.nodeParams.config.msgParsers[meshNum] == "SLIP":
            msgParser = SLIPMsgParser(parserConfig)
        elif self.nodeParams.config.msgParsers[meshNum] == "standard":
            msgParser = MsgParser(parserConfig)

        self.comm = TDMAComm([], radio, msgParser, self.nodeParams)

        # Node control run time bounds
        if self.comm.transmitSlot == 1:
            self.maxNodeControlTime = self.comm.frameLength - self.comm.slotLength
            self.minNodeControlTime = self.comm.transmitSlot * self.comm.slotLength
        else:
            self.minNodeControlTime = (self.comm.transmitSlot-2) * self.comm.slotLength # don't run within 1 slot of transmit 
            self.maxNodeControlTime = self.comm.transmitSlot * self.comm.slotLength
        #self.minNodeControlTime = 0.8*((self.comm.transmitSlot-1) * self.comm.slotLength)
    def run(self):
        while 1:
            try:
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
                   
                        # Update link status
                        if (self.nodeParams.config.nodeId == self.nodeParams.config.gcsNodeId): # ground node
                            entry = self.nodeParams.config.maxNumNodes - 1
                        else:
                            entry = self.nodeParams.config.nodeId - 1
                        self.nodeParams.linkStatus[entry] = nodeMsg.linkStatus
     
                        if (nodeMsg.cmdRelay): # command relay data                    
                            for cmd in nodeMsg.cmdRelay:
                                self.comm.cmdRelayBuffer.append(cmd)
                                #print("Cmds to relay:",self.comm.cmdRelayBuffer)
                        if (nodeMsg.cmds): # commands received
                            #self.comm.cmdBuffer = [] # clear existing buffer
                            for cmd in nodeMsg.cmds:
                                self.comm.cmdBuffer[cmd.cmdId] = {'bytes': cmd.msgBytes, 'txInterval': cmd.txInterval}
                                #self.comm.cmdBuffer.append({'bytes': cmd.msgBytes, 'txInterval': cmd.txInterval})
                self.interface.msgParser.parsedMsgs = [] # clear out processed parsed messages
                
                # Execute comm  
                self.comm.execute()

                # Run node control
                if self.comm.transmitSlot == 1 and (self.comm.frameTime > self.minNodeControlTime and self.comm.frameTime < self.maxNodeControlTime):
                        self.nodeControlRunFlag.value = 1
                elif self.comm.transmitSlot != 1 and (self.comm.frameTime < self.minNodeControlTime or self.comm.frameTime > self.maxNodeControlTime):
                    self.nodeControlRunFlag.value = 1
                else: # restrict node control process running
                    self.nodeControlRunFlag.value = 0
                
                # Send any received bytes to node control process
                if self.comm.frameTime > self.comm.cycleLength and self.comm.radio.bytesInRxBuffer > 0:
                    rcvdBytes = self.comm.radio.getRxBytes()
                    self.comm.radio.clearRxBuffer()
                    self.interface.send_bytes(rcvdBytes) 
                
                if self.comm.radio.bytesInRxBuffer > 0: # TODO: What is this doing?
                    rcvdBytes = self.comm.radio.getRxBytes()


            except KeyboardInterrupt:
                print("\nTerminating Comm Process.")
    
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
                   
                        # Update link status
                        if (self.nodeParams.config.nodeId == self.nodeParams.config.gcsNodeId): # ground node
                            entry = self.nodeParams.config.maxNumNodes - 1
                        else:
                            entry = self.nodeParams.config.nodeId - 1
                        self.nodeParams.linkStatus[entry] = nodeMsg.linkStatus
     
                        if (nodeMsg.cmdRelay): # command relay data                    
                            for cmd in nodeMsg.cmdRelay:
                                self.comm.cmdRelayBuffer.append(cmd)
                                #print("Cmds to relay:",self.comm.cmdRelayBuffer)
                        if (nodeMsg.cmds): # commands received
                            #self.comm.cmdBuffer = [] # clear existing buffer
                            for cmd in nodeMsg.cmds:
                                self.comm.cmdBuffer[cmd.cmdId] = {'bytes': cmd.msgBytes, 'txInterval': cmd.txInterval}
                                #self.comm.cmdBuffer.append({'bytes': cmd.msgBytes, 'txInterval': cmd.txInterval})
                self.interface.msgParser.parsedMsgs = [] # clear out processed parsed messages

                # Execute comm  
                self.comm.execute()

                # Send any received bytes to node control process
                if self.comm.radio.bytesInRxBuffer > 0:
                    rcvdBytes = self.comm.radio.getRxBytes()
                    self.comm.radio.clearRxBuffer()
                    self.interface.sendBytes(rcvdBytes) 
                
                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\nTerminating Comm Process.")
                self.terminate()
                self.terminate()
