import math
from switch import switch

class Navigation(object):
    """Maintains current state data for the formation node.
    
    This is the generic class for maintaining the current state data for a formation node.
    A derived class should be implemented for data and behavior for specific node types.

    Attributes:
        state: The current state vector for this vehicle.
        timestamp: The timestamp for the stored state vector.   
""" 

    def __init__(self):
        self.state = []  
        self.timestamp = 1 

    def update(self, state=[], time=[]):
        """Processes and stores state updates."""   

        # Update current position
        if state:
            self.state = state

        # Update timestamp
        if time:
            self.timestamp = time
    

def convertLatLonAlt(inputData, conversion='int', precision=[10000000, 100]):
    """Converts latitude, longitude, and altitude for transmission over serial and back."""
    
    if conversion == 'int':
        lat = int(inputData[0]*precision[0])
        lon = int(inputData[1]*precision[0])
        alt = int(inputData[2]*precision[1])
    elif conversion == 'float':
        lat = inputData[0]/float(precision[0])
        lon = inputData[1]/float(precision[0])
        alt = inputData[2]/float(precision[1])
    else:
        return None

    return [lat, lon, alt]


