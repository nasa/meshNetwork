from struct import pack
from mesh.generic.nodeHeader import headers, createHeader, packHeader
from mesh.generic.cmdDict import CmdDict

class Command(object):
    def __init__(self, cmdId, cmdData, header=[], txInterval=[], lastTxTime=0.0):
        self.cmdId = cmdId
        self.cmdData = cmdData
        if header: # create standard header for cmdId
            self.header = createHeader([CmdDict[cmdId].header, header]) # command header
        else:
            self.header = []
        self.txInterval = txInterval
        self.lastTxTime = lastTxTime
        self.packFormat = CmdDict[cmdId].packFormat # serial pack format
        self.serializeMethod = CmdDict[cmdId].serialize # method to serialize command


    def serialize(self, timestamp):
        self.lastTxTime = timestamp

        header = bytearray()
        
        if self.header: # Pack header
            header = packHeader(self.header)
        return header + self.serializeMethod(self.cmdData, timestamp) # combine header with command payload data

