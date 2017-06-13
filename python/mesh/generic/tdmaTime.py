import subprocess, time, sys, threading
import logging, logging.handlers
import mesh.generic.gpio as GPIO

#try: # This library only available on BBB
#    import Adafruit_BBIO.GPIO as GPIO
#except ImportError:
#    pass

def getTimeOffset(offsetType='standard'):
    if offsetType == 'pps':
        # Parse ntpq -p command
        try:
            proc = subprocess.Popen(['ntpq', '-p'], stdout=subprocess.PIPE)
            output = proc.stdout.read().decode('utf-8').split('\n')
        except:
            return None
        
        offset = None
        for line in output:
            if "PPS" in line:
                ppsStatus = line.split()
                if ppsStatus[4].isdigit(): # last update value is only digits so is seconds
                    if int(ppsStatus[4]) < 32: # last update less than 2 poll cycles old
                        offset = abs(float(ppsStatus[8]))
                elif ppsStatus[4] == '-': # could be 0 or no response - check if good reach
                    if ppsStatus[6].isdigit() and int(ppsStatus[6]) > 177: # no more than 1 missed in last 8 polls
                        offset = abs(float(ppsStatus[8]))
                break

        return offset

    elif offsetType == 'standard':
        # Parse ntpq -crv command
        proc = subprocess.Popen(['ntpq', '-crv'], stdout=subprocess.PIPE)
        output = proc.stdout.read()
    
        ntpStatus = str(output).replace(' ', '').split(',') # remove whitespace and split string
        serverSynched = False
        offset = None
        for entry in ntpStatus:
            if entry == 'sync_pps': # PPS sync
                serverSynched = True
            elif serverSynched and entry[0:6] == 'offset': # time offset 
                offset = abs(float(entry[7:]))
                #print("Offset:", str(offset))
        return serverSynched, offset

    return None

class OffsetChecker(object):
    def __init__(self, initBound, useLEDs = False):
        self.initSyncBound = initBound
        self.gpsdActive = True
        self.useLEDs = useLEDs

        # Set up logging to syslog
        formatter = logging.Formatter('%(module)s: [%(levelname)s] %(message)s')
        self.sysLogger = logging.getLogger(__name__)
        self.sysLogger.setLevel(logging.DEBUG)
        syslogHandler = logging.handlers.SysLogHandler(address='/dev/log')
        syslogHandler.setFormatter(formatter)
        self.sysLogger.addHandler(syslogHandler)

        # Set up LEDs
        if (self.useLEDs):
            GPIO.setup("P8_15", "out")
            GPIO.output("P8_15", "low")
            GPIO.setup("P8_16", "out")
            GPIO.output("P8_16", "low")
            GPIO.setup("P8_17", "out")
            GPIO.output("P8_17", "low")
            GPIO.setup("P8_18", "out")
            GPIO.output("P8_18", "low")

        # Time sync variables
        self.timeSyncTime = 0.0 

    def checkOffset(self):
        # Time sync started
        if (self.useLEDs):
            GPIO.output("P8_15", "high")

        # Check time offset
        serverSynched, offset = getTimeOffset()

        timeSynched = False
        if serverSynched and offset: # offset returned
            self.sysLogger.info('Time sync running. Current offset- ' + str(offset))
            
        
        # Update LEDs
        if serverSynched:
            if self.gpsdActive == True: # PPS sync - disabled gpsd
                #subprocess.call(["sudo", "killall", "-9", "gpsd"])
                #self.gpsdActive = False
                pass
        
            self.sysLogger.info('PPS sync acquired')
            if (self.useLEDs):
                GPIO.output("P8_16", "high") 
        else:
            self.sysLogger.info('Waiting for time server to synch to pps')
            if (self.useLEDs):
                GPIO.output("P8_16", "low")  
        if offset:
            if offset < self.initSyncBound*5:
                if (self.useLEDs):
                    GPIO.output("P8_17", "high")
            else:
                if (self.useLEDs):
                    GPIO.output("P8_17", "low")  
            if offset < self.initSyncBound:
                if self.timeSyncTime != 0.0:
                    if time.time() - self.timeSyncTime > 120: # time synched for 2 minutes
                        timeSynched = True
                        if (self.useLEDs):
                            GPIO.output("P8_18", "high")         
                else: # store time of time synch achieved
                    self.timeSyncTime = time.time()  
            else:
                self.timeSyncTime = 0.0;
                if (self.useLEDs):
                    GPIO.output("P8_18", "low")  

        return timeSynched

class SyncPulseMonitorThread(threading.Thread):
    def __init__(self, ppsPin, timerUpdate):
        threading.Thread.__init__(self)    

        # Setup PPS GPIO pin
        self.ppsPin = ppsPin
        GPIO.setup(ppsPin, "in")
        self.stopThread = False
        self.timerUpdate = timerUpdate
    
    def run(self):
        while self.stopThread == False:
            # Trigger on PPS pin
            GPIO.wait_for_edge(self.ppsPin, "rising")
            self.timerUpdate()
        

