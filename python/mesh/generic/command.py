from struct import pack
from mesh.generic.nodeHeader import headers, createHeader, packHeader
from mesh.generic.cmdDict import CmdDict
from mesh.generic.customExceptions import CommandIdNotFound

class Command(object):
    def __init__(self, cmdId, cmdData, header=[], txInterval=[], lastTxTime=0.0):
        self.cmdId = cmdId
        self.cmdData = cmdData
        self.txInterval = txInterval
        self.lastTxTime = lastTxTime

        try:
            if header: # create standard header for cmdId
                self.header = createHeader([CmdDict[cmdId].header, header]) # command header
            else:
                self.header = []
            self.packFormat = CmdDict[cmdId].packFormat # serial pack format
            self.serializeMethod = CmdDict[cmdId].serialize # method to serialize command
        except KeyError as e:
            raise CommandIdNotFound("Command Id {} not found", cmdId)

    def serialize(self, timestamp=[]):

        # Serialize and return command data
        return self.packHeader() + self.packBody(timestamp) # combine header with command payload data

    def packBody(self, timestamp=[]):
        body = bytearray()

        if self.serializeMethod:
            body = self.serializeMethod(self.cmdData, timestamp)
             
        return body

    def packHeader(self):
        header = bytearray()

        # Serialize command data
        if self.header: # Pack header
            header = packHeader(self.header)

        return header
