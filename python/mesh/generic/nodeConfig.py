import json
import os
import hashlib
from enum import IntEnum
from switch import switch
from mesh.generic.customExceptions import NodeConfigFileError, TDMAConfigError

class ParamId(IntEnum):
    """Enumeration of configuration parameter ID numbers."""
    nodeId = 1
    parseMsgMax = 2

    # TODO: Add remaining parameters

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

        self.loadSuccess = False
        self.hashSize = 20 # length of configuration hash (SHA1)

        if configFile:
            self.loadConfigFile(configFile)
        else:
            self.nodeId = -1
            self.maxNumNodes = -1
            self.uartNumBytesToRead = 100 
            self.numMeshNetworks = 1        

    def loadConfigFile(self, configFile):
        '''This function loads configuration data from the provided config file.
        
        Args:
            configFile: File path of configuration file.
        '''

        # Read config file
        if os.path.isfile(configFile):
            print('\nConfig file found. Loading configuration.')
        
            with open(configFile, 'r') as jsonFile:
                configData = json.load(jsonFile)

                try:

                    # General node configuration
                    self.loadNodeConfig(configData)

                    # Load software interface configuration
                    self.loadInterfaceConfig(configData)

                    # Mesh network configuration
                    self.loadCommConfig(configData)
        
                    self.loadSuccess = True

                except KeyError as e:
                    raise e
                    #print('\nConfiguration parameter \'' + e.args[0] + '\' missing. Exiting script.')
        else:
            raise NodeConfigFileError("Configuration file not found.")
            

    def loadNodeConfig(self, config):
        configData = config['node']

        # General node configuration
        self.maxNumNodes = configData['maxNumNodes']
        self.gcsPresent = configData['gcsPresent']
        if (self.gcsPresent):
            self.gcsNodeId = self.maxNumNodes        
        else:
            self.gcsNodeId = 0 
        if ("nodeId" in configData):
            self.nodeId = configData['nodeId']
        else: # get node Id
            self.readNodeId()
        self.nodeUpdateTimeout = configData['nodeUpdateTimeout']
        self.FCCommWriteInterval = configData['FCCommWriteInterval']
        self.FCCommDevice = configData['FCCommDevice']
        self.FCBaudrate = configData['FCBaudrate']
        self.cmdInterval = configData['cmdInterval'] 
        self.logInterval = configData['logInterval'] 
        
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
        self.platform = configData['platform']
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
                self.commConfig['fpgaFailsafePin'] = ""
            
            # Maximum TDMA transfer size
            self.commConfig['maxTransferSize'] = self.commConfig['txLength'] * self.meshBaudrate/8.0
            if self.commConfig['fpga']:
                self.commConfig['maxTransferSize'] = min(self.commConfig['maxTransferSize'], self.commConfig['fpgaFifoSize']) # minimum of baudrate*txLength and FPGA buffer size
            self.commConfig['maxTransferSize'] = int(0.8 * self.commConfig['maxTransferSize']) # apply margin 
            
            self.rxBufferSize = self.commConfig['maxNumSlots']*self.commConfig['maxTransferSize'] # update buffer size based on TDMA parameters
            self.commConfig['maxBlockTransferSize'] = int(0.8 * self.commConfig['cycleLength'] * self.meshBaudrate/8.0)
            if self.commConfig['rxDelay'] > 1.0 or self.commConfig['rxDelay'] < 0.0:
                raise TDMAConfigError("Invalid TDMA Rx Delay percentage.")
            else: # calculate rx delay from input percentage
                self.commConfig['rxDelay'] = self.commConfig['rxDelay'] * self.commConfig['txLength']
            
            sleepLength = self.commConfig['frameLength'] - self.commConfig['cycleLength']
            if sleepLength < 0: # Config infeasible
                print("ERROR: TDMA Frame length is less than Cycle length!")
                raise TDMAConfigError("TDMA Frame length is less than Cycle length.")
                    
            if 'transmitSlot' not in self.commConfig:
                self.commConfig['transmitSlot'] = self.nodeId           

    def loadPlatformConfig(self, config):
        '''This function loads platform specific configuration data and should be overriden by sub-classes.''' 
        pass

    def readNodeId(self):
        '''Determines node ID of this node in a platform specific way.  This method should be overriden by derived classes.'''
        self.nodeId = 1 # set a default value   
 
    def updateParameter(self, paramId, paramValue):
        """This method is used to update configuration values received via the ParamUpdate command."""
        updateSuccess = True

        for case in switch(paramId):
            if case(ParamId.parseMsgMax):
                self.parseMsgMax = paramValue
            else: # Just accept all updates for now
                try:
                    self.__dict__[paramId.name] = paramValue
                    updateSuccess = True
                except KeyError as e: # not a valid parameter name
                    updateSuccess = False
                except: # other error
                    updateSuccess = False        
        
        return updateSuccess

    def calculateHash(self):
        '''Calculates SHA1 hash of the current configuration data.'''
        
        if (self.loadSuccess == False): # Don't calculate hash if configuration not loaded
            return b''

        configHash = hashlib.sha1()
    
        # Get all attribute names and sort
        allAttrsDict = self.__dict__
        allAttrNames = list(allAttrsDict.keys())
        sortedAttrNames = sorted(allAttrNames)
        
        ### Create hash (from global parameters only)
        # Node configuration parameters
        nodeParams = ['maxNumNodes', 'gcsPresent', 'gcsNodeId', 'nodeUpdateTimeout', 'FCCommWriteInterval', 'FCCommDevice', 'FCBaudrate', 'cmdInterval', 'logInterval', 'commType', 'parseMsgMax', 'rxBufferSize', 'meshBaudrate', 'uartNumBytesToRead', 'numMeshNetworks', 'meshDevices', 'radios', 'msgParsers']
        for param in nodeParams:
            self.hashElem(configHash, allAttrsDict[param])
        
        # Interface configuration parameters 
        intParams = sorted(list(self.interface.keys()))
        for param in intParams:
            self.hashElem(configHash, self.interface[param])
             
        # Comm configuration parameters
        commParams = sorted(list(self.commConfig.keys()))
        if ('transmitSlot' in commParams): # remove unique config parameters
            commParams.remove('transmitSlot')
        for param in commParams:
            self.hashElem(configHash, self.commConfig[param])

        # Platform specific params
        self.hashPlatformConfig(configHash)
        
        return configHash.digest()

    def hashPlatformConfig(self, configHash):
        '''Hash platform specific configuration parameters.  This method should be overriden by derived classes.'''
        pass

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
        
        
        
