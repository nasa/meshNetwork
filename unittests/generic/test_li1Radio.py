import serial, time
from copy import deepcopy
from mesh.generic.li1Radio import Li1Radio, Li1SyncBytes, Li1HeaderLength, checksumLen
from mesh.generic.li1RadioCmds import Li1RadioCmds
from mesh.generic.checksum import calc8bitFletcherChecksum
from mesh.generic.nodeParams import NodeParams
from unittests.testConfig import configFilePath, testSerialPort
from struct import pack

testCmdType = Li1RadioCmds['Transmit'] 
testPayload = b'12345'
testHeader = Li1SyncBytes + pack('>H', testCmdType) + pack('>H', len(testPayload))
testHeader += pack('BB', *calc8bitFletcherChecksum(testHeader[2:]))

class TestLi1Radio:
    def setup_method(self, method):
        self.serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.li1Radio = Li1Radio(self.serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
    
    def test_createHeader(self):    
        """Test createHeader method of Li1Radio."""
        msg = {'commandType': testCmdType, 'payloadSize': len(testPayload)}
        header = self.li1Radio.createHeader(msg)
        assert(header == testHeader)

    def test_createPayload(self):   
        """Test createPayload method of Li1Radio."""
        msg = {'payload': testPayload}
        payload = self.li1Radio.createPayload(msg)
        # Check for checksum
        assert(len(payload) == len(msg['payload']) + 2)
        assert(payload[-2:] == pack('BB', *calc8bitFletcherChecksum(msg['payload'])))
    
        # Test for empty return when no payload
        assert(self.li1Radio.createPayload([]) == bytearray())

    def test_createCommand(self):
        cmd = {'commandType': testCmdType, 'payloadSize': len(testPayload), 'payload': testPayload, 'msgBytes': bytearray()}
        cmdOut = self.li1Radio.createCommand(cmd)
        assert(cmdOut[0:8] == testHeader) # header
        assert(cmdOut[8:8+len(testPayload)] == testPayload) # payload
        assert(cmdOut[-2:] == pack('BB', *calc8bitFletcherChecksum(testPayload))) # payload checksum
    
    def test_createMsg(self):
        """Test createMsg method of Li1Radio."""
        msgBytes = self.li1Radio.createMsg(testPayload)
        assert(msgBytes[0:8] == testHeader) # header
        assert(msgBytes[8:8+len(testPayload)] == testPayload) # payload
        assert(msgBytes[-2:] == pack('BB', *calc8bitFletcherChecksum(testPayload))) # payload cheksum


    def test_parseCmdHeader(self):  
        """Test parseCmdHeader method of Li1Radio."""
        cmdBytes = self.li1Radio.createHeader({'commandType': 0x2001, 'payloadSize': 0x0A0A}) # no-op ack
        cmd = dict()
        self.li1Radio.parseCmdHeader(cmd, cmdBytes)
        assert('header' in cmd and 'cmdType' in cmd) # header parsed
        assert(cmd['cmdType'] == 0x2001) # command type correct

    def test_parseAX25Msg(self):
        """Test parseAX25Msg method of Li1Radio."""
        msgBytes = b'1234567898765432' + b'98789' + b'12'
        msg = self.li1Radio.parseAX25Msg(msgBytes)
        assert(msg == b'98789') # only message bytes returned

    def test_parseCmdPayload(self):
        """Test parseCmdPayload method of Li1Radio."""
        dummyAX25Bytes = b'123456789876542'
        payloadMsgBytes = b'98789'
        payloadChecksum = b'12'
        totPayloadBytes = dummyAX25Bytes + payloadMsgBytes + payloadChecksum

        msgBytes = self.li1Radio.createHeader({'commandType': Li1RadioCmds.Transmit, 'payloadSize': len(totPayloadBytes)})
        msgBytes += totPayloadBytes
        #msgBytes += pack('BB', *calc8bitFletcherChecksum( 

        pass
 
    def test_parseCommand(self):    
        """Test parseCommand method of Li1Radio."""
        msgBytes = self.li1Radio.createCommand({'commandType': Li1RadioCmds['ReceivedData'], 'payloadSize': len(testPayload), 'payload': testPayload})
        print(msgBytes)
        #msgBytes = self.li1Radio.createMsg(testPayload)
        result = self.li1Radio.parseCommand(msgBytes)
        assert(len(result) == 2) # message end and command returned
        assert(result[1]['header'] == msgBytes[2:6]) # header matches
        assert(result[1]['payload'] == testPayload) # payload matches

    def test_processRxBytes(self):  
        """Test processRxBytes method of Li1Radio."""
        #self.li1Radio.createMsg(
        msgBytes = self.li1Radio.createCommand({'commandType': Li1RadioCmds['ReceivedData'], 'payloadSize': len(testPayload), 'payload': testPayload, 'msgBytes': bytearray()})
        self.li1Radio.processRxBytes(msgBytes, False)
        assert(self.li1Radio.rxBuffer[0:self.li1Radio.bytesInRxBuffer] == testPayload) # payload parsed correctly
    
    def test_sendMsg(self):
        """Test sendMsg method of Li1Radio."""
        # Send message smaller than max payload
        msgBytes = b'1234567890'
        self.li1Radio.sendMsg(msgBytes)
        time.sleep(0.1)
        readBytes = self.serialPort.read(50)
        assert(len(readBytes) == Li1HeaderLength + len(msgBytes) + checksumLen) # check single message sent

        # Send message larger than max payload
        msgBytes = pack(255*'B', *range(255)) + pack(255*'B', *list(reversed(range(255))))
        self.li1Radio.sendMsg(msgBytes)
        time.sleep(0.1)
        readBytes = self.serialPort.read(1000)
        assert(len(readBytes) == 2*Li1HeaderLength + len(msgBytes) + 2*checksumLen) # check two messages sent
        
    def test_sendBuffer(self):
        """Test sendBuffer method of Li1Radio."""
        msgBytes = b'12345'
        self.li1Radio.bufferTxMsg(msgBytes)
        assert(len(self.li1Radio.txBuffer) > 0) # bytes buffered
        self.li1Radio.sendBuffer()
        time.sleep(0.1)
        assert(len(self.li1Radio.txBuffer) == 0) # tx buffer cleared
        readBytes = self.serialPort.read(50)
        assert(len(readBytes) == Li1HeaderLength + len(msgBytes) + checksumLen) # message sent
    
    def test_sendCommand(self): 
        """Test sendCommand method of Li1Radio."""
                        
