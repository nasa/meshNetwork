from mesh.generic.nodeTools import isBeaglebone
from mesh.generic.radio import RadioMode
from mesh.generic.nodeParams import NodeParams
from unittests.testConfig import configFilePath
import pytest

class TestXbeeRadio:
    pytestmark = pytest.mark.skipif(isBeaglebone() == False, reason="requires GPIO")
    
    def setup_method(self, method):
        from mesh.generic.xbeeRadio import XbeeRadio
        self.nodeParams = NodeParams(configFile=configFilePath)
        self.xbeeRadio = XbeeRadio([], {'uartNumBytesToRead': self.nodeParams.config.uartNumBytesToRead, 'rxBufferSize': 2000}, "P8_12")
    
    def test_modeChanges(self):
        """Test mode changes of XbeeRadio."""
        import Adafruit_BBIO.GPIO as GPIO
        assert(self.xbeeRadio.mode == RadioMode.off)
        
        # Set mode to receive
        self.changeMode(RadioMode.receive)
        assert(GPIO.input("P8_12") == 0)

        # Set mode to off
        self.changeMode(RadioMode.off)
        assert(GPIO.input("P8_12") == 1)

        # Set mode to transmit
        self.changeMode(RadioMode.transmit)
        assert(GPIO.input("P8_12") == 0)
            
        # Set mode to sleep
        self.changeMode(RadioMode.sleep)
        assert(GPIO.input("P8_12") == 1)
        

    def changeMode(self, mode):
        self.xbeeRadio.setMode(mode)
        assert(self.xbeeRadio.mode == mode)
    
        
