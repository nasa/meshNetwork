class BlockTxPacketStatus(object):
    def __init__(self, packet, packetNum):
        self.packet = packet # outgoing mesh packet
        self.packetNum = packetNum
        self.responsesRcvd = []
        self.retries = 0
        self.framesSinceTx = 0 # counter since this packet sent

class BlockTx(object):
    def __init__(self, reqId, length, srcId, destId, startTime, endTime, rawData=None):
        self.complete = False
        self.reqId = reqId
        self.length = length
        self.srcId = srcId
        self.destId = destId
        self.startTime = startTime
        self.endTime = endTime
        self.packets = dict()
        self.data = rawData
        self.dataLoc = 0
        self.packetNum = 0
        self.dataComplete = False

    def allPacketsRcvd(self):
        for packetNum in range(self.length):
            if (packetNum + 1 not in self.packets): # packet not received
                return False
    
        return True # all packets have been received

    def getData(self):
        # Verify that block data is complete
        if (self.allPacketsRcvd()):
            self.dataComplete = True
            
        outData = b''
            
        for packetNum in range(self.length):
            if (packetNum+1 in self.packets): # packet received
                outData += self.packets[packetNum+1]
            
        return outData
    
        #else: # missing packets
        #    return b''
