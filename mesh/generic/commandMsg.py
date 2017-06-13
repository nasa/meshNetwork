from mesh.generic.cmdDict import CmdDict
import time

class CommandMsg(object):
    """Command message class for storing command parameters.

    Attributes:
        destId: Node ID of command destination.
        cmdData: Command data payload.
        timestamp: Creation time of command. 
    """
    def __init__(self, cmdId=[], cmdData=[], time=time.time(), destId=None):
        if cmdId and cmdData: # Create command data based on command ID 
            self.cmdData = self.parseCommand(cmdId, cmdData)
        else: # Store command data directly
            self.cmdData = cmdData
        self.timestamp = time
        if destId != None:
            self.destId = destId


    def parseCommand(self, cmdId=[], cmdData=[]):
        """Parses command data based on message format of command ID."""
        #if cmdId and cmdData and cmdId in MessageFormat: # Parse command data based on command ID
        if cmdId and cmdData and CmdDict[cmdId].messageFormat: # Parse command data based on command ID
            cmdBody = dict()
            for i in range(len(CmdDict[cmdId].messageFormat)):
                cmdBody[CmdDict[cmdId].messageFormat[i]] = cmdData[i]
            return cmdBody
        else: # Store raw command data input
            return cmdData
