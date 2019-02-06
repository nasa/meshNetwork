from mesh.generic.timeLib import getTimeOffset
import time

class FormationClock:
    """The formation clock is used to provide a command time reference among the formation nodes.  The clock provides the time with respect to a reference time established upon initialization.


    Attributes:
        time: Current clock time with respect to reference time.
        referenceTime: Reference time used by clock to compute clock time upon request. 
    """
        
    def __init__(self, referenceTime=[], timeSource=None):
        self.timeSource = None

        if referenceTime: # Initialize time from some reference time
            self.referenced = True
            self.referenceTime = referenceTime
        else:
            self.referenced = False

    def getTime(self):
        if self.referenced:
            return (time.time() - self.referenceTime)
        else:
            return time.time()

    def getOffset(self):
        return getTimeOffset(self.timeSource)
