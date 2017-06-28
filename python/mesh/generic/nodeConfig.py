import json
import os
import sys
import hashlib
#from collections import namedtuple
from mesh.generic.nodeTools import isBeaglebone

class NodeConfig(dict):
    """Node configuration parameters for formation.

    Attributes:

        platform (string): The type of vehicle the software is being run on.  Used to load platform-speciic configuration parameters.
        maxNumNodes (int): The maximum number of nodes allowed in the formation.  The actual number of nodes present may be less than this, but it may no be greater.
        nodeUpdateTimeout (double): The maximum allowable time (in seconds) between node state updates.
        commType (string): The communication protocol used by the nodes to communicate with one another.  Valid values are: TDMA- Time division multiple access communication scheme managed by formation software; standard- direct communication with no control by the formation software.  Any timing/conflict resolution is done by an outside entity such as the radio.
        uartNumBytesToRead: (int): The maximum number of message bytes that will be read per communication attempt.
        parseMsgMax (int): The maximum number of messages that will be attempted to be parsed from each communication byte packet.
        rxBufferSize (int): The size to pre-allocate for the communication receive buffer.
        FCCommWriteInterval (float): The minimum interval (in seconds) between successive flight computer communication write attempts.
        numMeshNetworks (int): The number of redundant mesh networks.  The minimum is 1 (non-redundant). 
        meshDevices (array of strings):  The address of the serial port for each mesh network.  The number of entries must match the value of numMeshNetworks.  
        radios (array of strings): The type of radio for each mesh network.  There must be an entry for each mesh network.  Valid values are: Li-1- Astrodev Lithium 1 radio; Xbee- XBee radio; Radio- generic radio type.
        msgParsers (array of strings): The type of message parser for each mesh network.  There must be an entry for each mesh network.  Valid values: SLIP- Serial Line Internet Protocol; standard: generic parser.
        meshBaudrate (int): Speed of serial interface connection to mesh network radios.  The value is in bits per second.
        FCCommDevice (string): The address of the serial port for communicating with the vehicle's flight computer.
        FCBaudrate (int): Speed of serial interface connection to the vehicle's flight computer in bits per second. 
        cmdInterval (float): Interval in seconds between successive send times of repeating commands.
        logInterval (float): Interval in seconds between logging attempts. 

        commConfig (dict): This object contains all of the communication configuration parameters.

    """
    
    def __init__(self,configFile=[]):
        self.__dict__ = self

        if configFile:
            self.loadConfigFile(configFile)
        else:
                
            self.nodeId = -1
            self.maxNumNodes = -1
            self.uartNumBytesToRead = 100 
            self.numMeshNetworks = 2        

        # Parameter map for sending/receiving config updates
        #Param = namedtuple('Param', ['id', 'serialType', 'varType'])
        #self.paramMap = ParamMap({'nodeId': Param(1, 'B', int), 'maxNumNodes': Param(2, 'B', int)}) 
        
        # Calculate hash size
        self.hashSize = len(self.calculateHash())
        
    def loadConfigFile(self, configFile):
        '''This function loads configuration data from the provided config file.
        
        Args:
            configFile: File path of configuration file.
        '''

        # Read config file
        if os.path.isfile(configFile):
            print('\nConfig file found. Loading configuration.')
            jsonFile = open(configFile,'r')
            configData = json.load(jsonFile)
            try:

                # General node configuration
                self.loadNodeConfig(configData)

                # Load software interface configuration
                self.loadInterfaceConfig(configData)

                # Mesh network configuration
                self.loadCommConfig(configData)

            except KeyError as e:
                print('\nConfiguration parameter \'' + e.args[0] + '\' missing. Exiting script.')
                sys.exit()
            jsonFile.close()
        else:
            print('\nConfig file not present. Exiting script.')
            sys.exit()

    def loadNodeConfig(self, config):
        configData = config['node']

        # General node configuration
        self.maxNumNodes = configData['maxNumNodes']
        self.gcsPresent = configData['gcsPresent']
        if (self.gcsPresent):
            self.gcsNodeId = self.maxNumNodes        
        self.readNodeId() # get node Id
        self.platform = configData['platform']
        self.nodeUpdateTimeout = configData['nodeUpdateTimeout']
        self.FCCommWriteInterval = configData['FCCommWriteInterval']
        self.FCCommDevice = configData['FCCommDevice']
        self.FCBaudrate = configData['FCBaudrate']
        self.cmdInterval = configData['cmdInterval'] 
        self.logInterval = configData['logInterval'] 
        self.enablePin = configData['enablePin']        
        self.statusPin = configData['statusPin']        
        
        # Network config
        self.commType = configData['commType']
        self.parseMsgMax = configData['parseMsgMax']
        self.rxBufferSize = configData['rxBufferSize']
        self.meshBaudrate = configData['meshBaudrate']
        self.uartNumBytesToRead = int(max(self.FCBaudrate,self.meshBaudrate)/8)
        self.numMeshNetworks = configData['numMeshNetworks']
        self.meshDevices = configData['meshDevices']
        self.radios = configData['radios']
        self.msgParsers = configData['msgParsers']

        # Platform specific configuration
        self.loadPlatformConfig(config)

    def loadInterfaceConfig(self, config):
        self.interface = config['interface']
        
        # Node interface
        #self.interface = {"node": configData['node'], "comm": configData['comm']}


    def loadCommConfig(self, config):
        # Comm type specific configuration
        self.commConfig = {}
        if self.commType == "TDMA":
            self.commConfig = config['tdmaConfig']
            self.commConfig['rxLength'] = self.commConfig['preTxGuardLength'] + self.commConfig['txLength'] + self.commConfig['postTxGuardLength'] # receive length
            self.commConfig['slotLength'] = self.commConfig['enableLength'] + self.commConfig['rxLength'] + self.commConfig['slotGuardLength'] # total length of slot
            self.commConfig['frameLength'] = 1.0/self.commConfig['desiredDataRate'] # frame length
            self.commConfig['cycleLength'] = self.commConfig['slotLength'] * self.commConfig['maxNumSlots'] # cycle length
           
            if 'fpga' not in self.commConfig.keys():
                self.commConfig['fpga'] = False
            
            # Maximum TDMA transfer size
            self.commConfig['maxTransferSize'] = self.commConfig['txLength'] * self.meshBaudrate/8.0
            if self.commConfig['fpga']:
                self.commConfig['maxTransferSize'] = min(self.commConfig['maxTransferSize'], self.commConfig['fpgaFifoSize']) # minimum of baudrate*txLength and FPGA buffer size
            self.commConfig['maxTransferSize'] = int(0.8 * self.commConfig['maxTransferSize']) 
            
            self.rxBufferSize = self.commConfig['maxNumSlots']*self.commConfig['maxTransferSize'] # update buffer size based on TDMA parameters
            self.commConfig['maxBlockTransferSize'] = int(0.8 * self.commConfig['cycleLength'] * self.meshBaudrate/8.0)
            if self.commConfig['rxDelay'] > 1.0 or self.commConfig['rxDelay'] < 0.0:
                print("ERROR: Invalid TDMA Rx Delay percentage!")
                sys.exit()
            else: # calculate rx delay from input percentage
                self.commConfig['rxDelay'] = self.commConfig['rxDelay'] * self.commConfig['txLength']
            
            sleepLength = self.commConfig['frameLength'] - self.commConfig['cycleLength']
            if sleepLength < 0: # Config infeasible
                print("ERROR: TDMA Frame length is less than Cycle length!")
                sys.exit()
                    
            if 'transmitSlot' not in self.commConfig:
                self.commConfig['transmitSlot'] = self.nodeId           

    def loadPlatformConfig(self, config):
        '''This function loads platform specific configuration data and should be overriden by sub-classes.''' 
        pass

    def readNodeId(self):
        '''Determines node ID of this node by reading the GPIO input values wired to the DIP switches on the node formation cape.'''
        if not isBeaglebone(): # not a Beaglebone (assumed to be gcs)
            self.nodeId = self.maxNumNodes
            return

        import mesh.generic.gpio as GPIO
        # Enable switches
        GPIO.setup("P8_7", "in")
        GPIO.setup("P8_8", "in")
        GPIO.setup("P8_10", "in")
        if(GPIO.input("P8_7") == 0 and GPIO.input("P8_8") == 0 and GPIO.input("P8_10") == 0):
            if (self.gcsPresent): # ground node
                self.nodeId = self.maxNumNodes
            else: # Node disabled
                print("Invalid Node ID switch settings.  Exiting node control script")
                sys.exit()
        elif(GPIO.input("P8_7") == 0 and GPIO.input("P8_8") == 1 and GPIO.input("P8_10") == 0):
            self.nodeId = 1
        elif(GPIO.input("P8_7") == 1 and GPIO.input("P8_8") == 0 and GPIO.input("P8_10") == 0):
            self.nodeId = 2
        elif(GPIO.input("P8_7") == 1 and GPIO.input("P8_8") == 1 and GPIO.input("P8_10") == 0):
            self.nodeId = 3
        elif(GPIO.input("P8_7") == 0 and GPIO.input("P8_8") == 0 and GPIO.input("P8_10") == 1):
            self.nodeId = 4
        elif(GPIO.input("P8_7") == 0 and GPIO.input("P8_8") == 1 and GPIO.input("P8_10") == 1):
            self.nodeId = 5
        elif(GPIO.input("P8_7") == 1 and GPIO.input("P8_8") == 0 and GPIO.input("P8_10") == 1):
            self.nodeId = 6
        elif(GPIO.input("P8_7") == 1 and GPIO.input("P8_8") == 1 and GPIO.input("P8_10") == 1):
            self.nodeId = 7
        else:
            # Node disabled
            print("Node is disabled.  Exiting node control script")
            sys.exit()

        print("Node id: " + str(self.nodeId))


        # Set ip address and hostname based on node id
        if self.nodeId > 0:
            os.system('sudo hostname node' + str(self.nodeId))
            os.system('sudo ifconfig eth0 192.168.0.' + str(self.nodeId) + '0')
            os.system('sudo route add default gw 192.168.0.1')
            with open("hostname", "a") as f:
                f.write("node" + str(self.nodeId))
            
            with open("hosts", "a") as f:
                f.write("127.0.0.1 localhost.localdomain localhost \n")
                f.write("127.0.0.1 node" + str(self.nodeId))
            os.system("sudo mv hostname /etc/")
            os.system("sudo mv hosts /etc/")
    
    def calculateHash(self):
        '''Calculates SHA1 hash of the current configuration data.'''
        configHash = hashlib.sha1()
    
        # Get all attribute names and sort
        allAttrsDict = self.__dict__
        allAttrNames = list(allAttrsDict.keys())
        sortedAttrNames = sorted(allAttrNames)
        
        # Remove unique node specific values before hashing
        #sortedAttrNames.remove('nodeId')
        #sortedAttrNames.remove('formationCmd')
        #if self.platform == 'Pixhawk':
        #   sortedAttrNames.remove('failsafeAlt')
        #if self.commType == 'TDMA':
        #   allAttrsDict['commConfig'].remove('transmitSlot') # remove transmit slot

        
        ### Create hash
        # Generic parameters
        if (self.platform == "Pixhawk"):
            self.hashElem(configHash, 0)
        elif (self.platform == "SatFC"):
            self.hashElem(configHash, 1)
        self.hashElem(configHash, self.maxNumNodes)
        if self.commType == 'standard':
            self.hashElem(configHash, 0)
        if self.commType == 'TDMA':
            self.hashElem(configHash, 1)
        self.hashElem(configHash, self.uartNumBytesToRead)
        self.hashElem(configHash, self.parseMsgMax)
        self.hashElem(configHash, self.rxBufferSize)
        self.hashElem(configHash, self.meshBaudrate)
        self.hashElem(configHash, self.FCBaudrate)
        self.hashElem(configHash, self.numMeshNetworks)
        for meshDevice in self.meshDevices:
            self.hashElem(configHash, meshDevice)
        for radio in self.radios:
            if radio == 'Xbee':
                self.hashElem(configHash, 0)
            elif radio == "Li-1":
                self.hashElem(configHash, 1)
        for msgParser in self.msgParsers:
            if msgParser == 'SLIP':
                self.hashElem(configHash, 0)
            if msgParser == 'standard':
                self.hashElem(configHash, 1)
        self.hashElem(configHash, self.FCCommDevice)
        self.hashElem(configHash, self.cmdInterval)
        self.hashElem(configHash, self.logInterval)

        # Comm parameters
        self.hashElem(configHash, self.commConfig['preTxGuardLength'])
        self.hashElem(configHash, self.commConfig['postTxGuardLength'])
        self.hashElem(configHash, self.commConfig['txLength'])
        self.hashElem(configHash, self.commConfig['txBaudrate'])
        self.hashElem(configHash, self.commConfig['enableLength'])
        self.hashElem(configHash, self.commConfig['rxDelay'])
        self.hashElem(configHash, self.commConfig['maxNumSlots'])
        self.hashElem(configHash, self.commConfig['slotGuardLength'])
        self.hashElem(configHash, self.commConfig['desiredDataRate'])
        self.hashElem(configHash, self.commConfig['initTimeToWait'])
        self.hashElem(configHash, self.commConfig['initSyncBound'])
        self.hashElem(configHash, self.commConfig['operateSyncBound'])
        self.hashElem(configHash, self.commConfig['offsetTimeout'])
        self.hashElem(configHash, self.commConfig['offsetTxInterval'])
        self.hashElem(configHash, self.commConfig['statusTxInterval'])
        self.hashElem(configHash, self.commConfig['maxTxBlockSize'])
        self.hashElem(configHash, self.commConfig['blockTxRequestTimeout'])
        self.hashElem(configHash, self.commConfig['minBlockTxDelay'])
        self.hashElem(configHash, self.commConfig['rxLength'])
        self.hashElem(configHash, self.commConfig['slotLength'])
        self.hashElem(configHash, self.commConfig['frameLength'])
        self.hashElem(configHash, self.commConfig['cycleLength'])
        self.hashElem(configHash, self.commConfig['maxTransferSize'])
        self.hashElem(configHash, self.commConfig['maxBlockTransferSize'])

        # Platform specific params
        #if (self.platform == "Pixhawk"):
        #    self.hashElem(configHash, self.positionUpdateFail)
        #    self.hashElem(configHash, self.targetUpdateFail)
        #    self.hashElem(configHash, self.nodeUpdateTimeout)
        #    self.hashElem(configHash, self.positionTimer)
        #    self.hashElem(configHash, self.leaderTimeout)
            
            # Command fence
        #    self.hashElem(configHash, self.posCmdFence[0]) # min lat
        #    self.hashElem(configHash, self.posCmdFence[2]) # max lat
        #    self.hashElem(configHash, self.posCmdFence[1]) # min lon
        #    self.hashElem(configHash, self.posCmdFence[3]) # max lon
        #    self.hashElem(configHash, self.posCmdFence[4]) # min alt
        #    self.hashElem(configHash, self.posCmdFence[5]) # max alt
            
            # Formation command
        #    self.hashElem(configHash, self.formationCmd[1]) # lat
        #    self.hashElem(configHash, self.formationCmd[2]) # lon
        #    self.hashElem(configHash, self.formationCmd[3]) # alt
        #    self.hashElem(configHash, self.formationCmd[4]) # shape
            
        #    self.hashElem(configHash, self.altSpacing)
        #    self.hashElem(configHash, self.lateralDrift)
        #    self.hashElem(configHash, self.altitudeDrift)
        #    self.hashElem(configHash, self.radius)
        #    self.hashElem(configHash, self.lineAngle)
        #    self.hashElem(configHash, self.vehSpacing)
        
        #elif (self.platform == "SatFC"):
        #    if self.satFormationType == "EIVecSep":
        #        self.hashElem(configHash, 0)
        #        self.hashElem(configHash, self.chiefId)
        #        for elem in self.nomOrbElems:
        #            self.hashElem(configHash, elem)
        #        self.hashElem(configHash, self.deltaA)
        #        self.hashElem(configHash, self.deltaU)
        #        for i in range(2):
        #            self.hashElem(configHash, self.eccDelta[i])
        #            self.hashElem(configHash, self.inclDelta[i])
        #            self.hashElem(configHash, self.deltaE[i])
        #            self.hashElem(configHash, self.deltaI[i])
        #        self.hashElem(configHash, self.maxEIAngle)
        #        self.hashElem(configHash, self.burnSpacing)


        # Create hash
#       for i in range(len(sortedAttrNames)):
#           #print(allAttrsDict[sortedAttrNames[i]])
#           if isinstance(allAttrsDict[sortedAttrNames[i]], list): # entry is a list
#               for elem in allAttrsDict[sortedAttrNames[i]]:
#                   self.hashElem(configHash, elem)
#                   #if isinstance(elem, float): # Truncate float decimal places
#                   #   configHash.update(('%.*f' % (7, elem))[:-1].encode('utf-8'))
#                   #else:  
#                   #   configHash.update(str(elem).encode('utf-8'))
#           elif isinstance(allAttrsDict[sortedAttrNames[i]], dict):
#               # Sort dict for consistent hash
#               keys = list(allAttrsDict[sortedAttrNames[i]].keys())
#               sortedEntries = sorted(keys)
#               if sortedAttrNames[i] == 'commConfig' and self.commType == 'TDMA':
#                   sortedEntries.remove('transmitSlot') # remove transmit slot
#               for key in sortedEntries:
#                   self.hashElem(configHash, allAttrsDict[sortedAttrNames[i]][key])
#                   #elem = allAttrsDict[sortedAttrNames[i]][key]
#                   #if isinstance(elem, float): # Truncate float decimal places
#                   #   configHash.update(('%.*f' % (7, elem))[:-1].encode('utf-8'))
#                   #else:  
#                   #   configHash.update(str(elem).encode('utf-8'))
#           else:
#               self.hashElem(configHash, allAttrsDict[sortedAttrNames[i]])
#           #elif isinstance(allAttrsDict[sortedAttrNames[i]], float): # Truncate float decimal places
#           #   configHash.update(('%.*f' % (7, allAttrsDict[sortedAttrNames[i]]))[:-1].encode('utf-8'))
#           #else:  
#           #   configHash.update(str(allAttrsDict[sortedAttrNames[i]]).encode('utf-8'))
                
        #print allAttrsDict[sortedAttrNames[0]]
        return configHash.digest()

    def hashElem(self, m_hash, elem):
        '''Update inputted SHA1 hash with value.
        
        Args:
            m_hash: SHA1 hash.
            elem: Value to append to hash.
        
        ''' 
        if isinstance(elem, float): # Truncate float decimal places
            #print(('%.*f' % (7, elem)).encode('utf-8'))
            m_hash.update(('%.*f' % (7, elem)).encode('utf-8'))
        else:   
            #print(str(elem).encode('utf-8'))
            m_hash.update(str(elem).encode('utf-8'))
        
        

class ParamMap(dict):
    """Class is a dictionary of config parameter names that facilitates sending parameter update values over serial links."""

    def findName(self, id):
        """Finds the name of a parameter by searching the dictionary using a unique ID number.""" 
        for i in range(len(list(self.values()))):
            if list(self.values())[i].id == id:
                return list(self.keys())[i]
