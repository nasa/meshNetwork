from collections import OrderedDict
from struct import unpack, pack

class CommProcessor():
    """The comm processor creates messages for serial transmission and parses received messages.  

    Attributes:
        crc16: 16-bit CRC calculator to generate CRC and attach to messages prior to transmission.
        cmdQueue: Ordered dictionary for storing received and parsed commands prior to processing by node.
        msgProcessors: An array of message processors for processing of received commands.  Each processor has a list of command IDs that it is to be used to process.
        nodeParams: Node parameters for this node.  
    """
    def __init__(self, msgProcessors, nodeParams):
        self.cmdQueue = OrderedDict()   
        self.msgProcessors = msgProcessors
        self.nodeParams = nodeParams
    
    def processMsg(self, msg, args):
        """Processes parsed serial messages.
        Args:
            msg: Serial message to be processed.
            args: Other arguments needed for processing serial message.
        """
        if len(msg) > 0:
            # Parse command id
            cmdId = unpack('B',msg[0:1])[0]
            # Pass command to proper processor
            for processor in self.msgProcessors:
                if cmdId in processor['cmdList'].values():
                    processor['msgProcessor'](self, cmdId, msg, args)
                    break
            
