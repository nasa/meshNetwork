import globalCfg
if (globalCfg.platform == "bbb"):
    import Adafruit_BBIO.GPIO as GPIO

# GPIO wrapper
def setup(pin, direction):
    if (globalCfg.platform == "bbb"):
        if (direction == "in"):
            GPIO.setup(pin, GPIO.IN)
        elif (direction == "out"):
            GPIO.setup(pin, GPIO.OUT)
        else: # invalid direction provided
            return -1
        
        return 0
    else:
        return -1
def output(pin, value):
    if (globalCfg.platform == "bbb"):
        if (value == "low"):
            GPIO.output(pin, GPIO.LOW)
        elif (value == "high"):
            GPIO.output(pin, GPIO.HIGH)    
        else: # invalid value
            return -1
        
        return 0
    else:
        return -1

def input(pin):
    if (globalCfg.platform == "bbb"):
        return GPIO.input(pin)
    else:
        return -1

def wait_for_edge(pin, edgeType):
    if (globalCfg.platform == "bbb"):
        if (edgeType == "rising"):
            GPIO.wait_for_edge(self.ppsPin, GPIO.RISING)
        elif (edgeType == "falling"):
            GPIO.wait_for_edge(self.ppsPin, GPIO.FALLING)
        elif (edgeType == "both"):
            GPIO.wait_for_edge(self.ppsPin, GPIO.BOTH)
        else: # invalid edge type
            return -1

        return 0

    else:
        return -1
