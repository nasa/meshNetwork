import socket, time
from mesh.generic.udpRadio import UDPRadio
from mesh.generic.nodeParams import NodeParams
from unittests.testConfig import configFilePath
from mesh.generic.customExceptions import NoSocket
import pytest

class TestUDPRadio:
    def setup_method(self, method):

        self.nodeParams = NodeParams(configFile=configFilePath)
        self.radio = UDPRadio({'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000, 'ipAddr': "127.0.0.1", 'readPort': 5000, 'writePort': 5000})
    
    def test_readBytes(self):
        """Test readBytes method of Radio."""       
        # Write bytes and read
        msgBytes = b'ABC'
        self.radio.sockWrite.sendto(msgBytes, (self.radio.sockWriteIp, self.radio.sockWritePort))
        time.sleep(0.1)
        self.radio.readBytes(False)
        assert(self.radio.bytesInRxBuffer == len(msgBytes))
        serBytes = self.radio.getRxBytes()
        assert(serBytes == msgBytes)
        
        # Test exception raising
        self.radio.sockRead = []
        with pytest.raises(NoSocket):
            self.radio.readBytes(False)
    
    def test_sendMsg(self):
        """Test sendMsg method of UDPRadio (using UDPRadio implementation of sendBytes)."""
        # Send test message
        testMsg = b'123456789'
        msgBytes = testMsg
        self.radio.sendMsg(testMsg)
        time.sleep(0.1)
        self.radio.readBytes(True)
        readBytes = self.radio.getRxBytes()
        assert(readBytes == msgBytes)
        
        # Test exception raising
        self.radio.sockWrite = []
        with pytest.raises(NoSocket):
            self.radio.sendMsg(testMsg)
    
