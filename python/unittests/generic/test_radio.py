import serial, time
from mesh.generic.radio import Radio, RadioMode
from mesh.generic.radio import Radio, RadioMode
from mesh.generic.nodeParams import NodeParams
from unittests.testConfig import configFilePath, testSerialPort
from mesh.generic.customExceptions import NoSerialConnection
import pytest

class TestRadio:
    def setup_method(self, method):
        self.serialPort = serial.Serial(port=testSerialPort, baudrate=57600, timeout=0)

        self.nodeParams = NodeParams(configFile=configFilePath)
        self.radio = Radio(self.serialPort, {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000})
    
    def test_setMode(self):
        """Test setMode method of RadioInterface."""
        assert(self.radio.mode == RadioMode.off)
        
        # Set mode to receive
        self.changeMode(RadioMode.receive)

        # Set mode to off
        self.changeMode(RadioMode.off)

        # Set mode to transmit
        self.changeMode(RadioMode.transmit)
            
        # Set mode to sleep
        self.changeMode(RadioMode.sleep)

    def changeMode(self, mode):
        self.radio.setMode(mode)
        assert(self.radio.mode == mode)
            
    def test_clearRxBuffer(self):
        """Test clearRxBuffer method of Radio."""
        self.radio.rxBuffer = [1,2,3,4,5]
        self.radio.clearRxBuffer()
        assert(self.radio.rxBuffer == bytearray(self.radio.rxBufferSize))
        assert(self.radio.bytesInRxBuffer == 0)

    def test_getRxBytes(self):
        """Test getRxBytes method of Radio."""
        msg = b'12345'
        self.radio.bufferRxMsg(msg, True)
        assert(self.radio.getRxBytes() == msg)

    def test_sendMsg(self):
        """Test sendMsg method of Radio."""
        # Send test message
        testMsg = b'123456789'
        msgBytes = testMsg
        self.radio.sendMsg(testMsg)
        time.sleep(0.1)
        self.radio.readBytes(True)
        readBytes = self.radio.getRxBytes()
        assert(readBytes == msgBytes)

    def test_bufferTxMsg(self):
        """Test bufferTxMsg method of Radio."""
        msg = b'12345'
        self.radio.bufferTxMsg(msg)
        assert(self.radio.txBuffer == msg)

    def test_createMsg(self):
        """Test createMsg method of Radio."""
        msg = b'12345'
        assert(self.radio.createMsg(msg) == msg)

    def test_sendCommand(self):
        pass    
    
    def test_readBytes(self):
        """Test readBytes method of Radio."""       
        # Write bytes and read
        msgBytes = b'ABC'
        self.serialPort.write(msgBytes)
        time.sleep(0.1)
        self.radio.readBytes(False)
        assert(self.radio.bytesInRxBuffer == len(msgBytes))
        serBytes = self.radio.getRxBytes()
        assert(serBytes == msgBytes)
        
        # Write again and confirm buffer is not kept
        msgBytes = b'DEF'
        self.serialPort.write(msgBytes)
        time.sleep(0.1)
        self.radio.readBytes(False)
        assert(self.radio.bytesInRxBuffer == len(msgBytes))
        serBytes = self.radio.getRxBytes()
        assert(serBytes == msgBytes)

        # Write again and confirm buffer is kept
        msgBytes = b'ABC'
        self.serialPort.write(msgBytes)
        time.sleep(0.1)
        self.radio.readBytes(True)
        assert(self.radio.bytesInRxBuffer == 2*len(msgBytes))
        serBytes = self.radio.getRxBytes()
        assert(serBytes == b'DEFABC')
        
        # Test exception raising
        self.radio.serial = []
        with pytest.raises(NoSerialConnection):
            self.radio.readBytes(False)
    
    def test_sendBuffer(self):
        """Test sendBuffer method of Radio."""
        msg = b'12345'
        self.radio.bufferTxMsg(msg)
        self.radio.sendBuffer()
        time.sleep(0.1)
        self.radio.readBytes(True)
        assert(self.radio.getRxBytes() == msg)
    
        # Test maximum bytes sent
        self.radio.clearRxBuffer()
        msg = b'1'*100
        self.radio.bufferTxMsg(msg)
        self.radio.sendBuffer(50)
        time.sleep(0.1)
        self.radio.readBytes(True)
        assert(len(self.radio.txBuffer) == 50)
        assert(self.radio.bytesInRxBuffer == 50)

