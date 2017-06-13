from mesh.generic.radio import Radio, RadioMode
import mesh.generic.gpio as GPIO

class XbeeRadio(Radio):
    def __init__(self, serial, config, sleepPin = []):
        Radio.__init__(self, serial, config)
        self.sleepPin = sleepPin
        # Setup sleep pin
        if self.sleepPin:
            GPIO.setup(self.sleepPin, "out")
            self.setOff() # default to off mode
        pass

    def setSleep(self):
        if self.sleepPin:
            GPIO.output(self.sleepPin, "high")
        self.mode = RadioMode.sleep

    def setOff(self):
        self.setSleep()
        self.mode = RadioMode.off

    def setReceive(self):
        self.wake()
        self.mode = RadioMode.receive

    def setTransmit(self):
        self.wake()
        self.mode = RadioMode.transmit

    def wake(self):
        if self.sleepPin:
            GPIO.output(self.sleepPin, "low")
