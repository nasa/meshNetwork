import time
from mesh.generic.serialComm import SerialComm

class NodeComm(SerialComm):
    """ Generic implementation of SerialComm for all node types.
    
    This class provides the basic structure for all formation node communication.  A specific implementation should be created for each specific node type.

    Attributes:
        nodeId: Id number for this formation node.
        timestamp: Timestamp from received messages. 
    """

    def __init__(self, commProcessor, radio, msgParser, nodeParams=[], config={'uartNumBytesToRead': 50, 'rxBufferSize': 2000, 'parseMsgMax': 50}, node_id=-1):
        if nodeParams:
            self.nodeParams = nodeParams
            config = {'uartNumBytesToRead': nodeParams.config.uartNumBytesToRead, 'rxBufferSize': nodeParams.config.rxBufferSize, 'parseMsgMax': nodeParams.config.parseMsgMax}
            node_id = nodeParams.config.nodeId          
            
        SerialComm.__init__(self, commProcessor, radio, msgParser)
        self.nodeId = node_id # MARKED FOR DELETION
        self.timestamp = -99 # MARKED FOR DELETION
        
        # Command relay buffer
        self.cmdRelayBuffer = bytearray()

    def execute(self):
        """Execute node communication cycle."""
        pass
        
    def processMsgs(self, args=[]):
        """Read and process any received messages."""
        self.readMsgs()
        print(self.msgParser.parsedMsgs)
        if self.msgParser.parsedMsgs:
            for i in range(len(self.msgParser.parsedMsgs)):
                self.processMsg(self.msgParser.parsedMsgs.pop(0), args)
