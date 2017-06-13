from mesh.generic.nodeHeader import createHeader, packHeader, headers
from struct import pack

class TestNodeHeader:
    

    def setup_method(self, method):
        self.nodeHeaderIn = ['NodeHeader', [3, 4, 5]]
        self.minimalHeaderIn = ['MinimalHeader', [3]]
        self.sourceHeaderIn = ['SourceHeader', [3, 4]]
        pass            

            
    def test_createHeader(self):
        """Test creation of all header types."""
        # NodeHeader
        header = createHeader(self.nodeHeaderIn)    
        self.checkHeaderContents(header, self.nodeHeaderIn)

        # MinimalHeader
        header = createHeader(self.minimalHeaderIn) 
        self.checkHeaderContents(header, self.minimalHeaderIn)
        
        # SourceHeader
        header = createHeader(self.sourceHeaderIn)  
        self.checkHeaderContents(header, self.sourceHeaderIn)

    def test_packHeader(self):
        """Test packing of all defined header types."""
        # NodeHeader
        nodeHeader = createHeader(self.nodeHeaderIn)
        packedHeader = pack(headers[self.nodeHeaderIn[0]]['format'], *self.nodeHeaderIn[1])
        assert(packHeader(nodeHeader) == packedHeader)
        
        # MinimalHeader
        minimalHeader = createHeader(self.minimalHeaderIn)
        packedHeader = pack(headers[self.minimalHeaderIn[0]]['format'], *self.minimalHeaderIn[1])
        assert(packHeader(minimalHeader) == packedHeader)
        
        # SourceHeader
        sourceHeader = createHeader(self.sourceHeaderIn)
        packedHeader = pack(headers[self.sourceHeaderIn[0]]['format'], *self.sourceHeaderIn[1])
        assert(packHeader(sourceHeader) == packedHeader)

    def checkHeaderContents(self, header, headerIn):
        headerType = headerIn[0]
        assert(header['type'] == headerType)
        assert(len(header['header']) == len(headerIn[1]))
        for i in range(len(headers[headerType]['entries'])):
            assert(header['header'][headers[headerType]['entries'][i]] == headerIn[1][i])
        
        
