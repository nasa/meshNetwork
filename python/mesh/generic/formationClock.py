from mesh.generic.nodeTools import isBeaglebone
from mesh.generic.tdmaTime import getTimeOffset, SyncPulseMonitorThread
from threading import Lock
import time

class FormationClock:
    """The formation clock is used to provide a command time reference among the formation nodes.  The clock provides the time with respect to a reference time established upon initialization.


    Attributes:
        time: Current clock time with respect to reference time.
        referenceTime: Reference time used by clock to compute clock time upon request. 
    """
        
    def __init__(self, referenceTime=[], ppsPin=None):
        if referenceTime: # Initialize time from some reference time
            self.referenced = True
            self.referenceTime = referenceTime
        else:
            self.referenced = False
    
        if ppsPin and isBeaglebone(): # monitor PPS signal 
            self.tdmaTimerStart = time.time()
            self.timerLock = Lock()
            self.monitorThread = SyncPulseMonitorThread(ppsPin, self.resetTDMATimer)
            self.monitorThread.setDaemon(True) # set as daemon so it will terminate when main program ends
            self.monitorThread.start()

    def getTime(self):
        if self.referenced:
            return (time.time() - self.referenceTime)
        else:
            return time.time()

    def resetTDMATimer(self):
        if (self.timerLock.acquire(blocking=False)): # get lock before updating
            # Reset tdma timer start
            self.tdmaTimerStart = time.time()
        self.timerLock.release() 

    def getTDMATimer(self):
        with self.timerLock: # block on reads
            return time.time() - self.tdmaTimerStart

    def getOffset(self):
        return getTimeOffset('pps')
