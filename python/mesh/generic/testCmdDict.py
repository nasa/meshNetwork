from struct import pack
from mesh.generic.commandType import CommandType
from mesh.generic.cmds import TestCmds

# Serialize methods
def serialize_TestCmds_SendDataBlock(cmdData, timestamp):
    """Method for serializing TestCmds['SendDataBlock'] command for serial transmission."""
    return pack(TestCmdDict[TestCmds['SendDataBlock']].packFormat, cmdData['destId']) 

TestCmdDict = {TestCmds['SendDataBlock']: CommandType('=B', serialize_TestCmds_SendDataBlock, ['destId'], header='NodeHeader')}
