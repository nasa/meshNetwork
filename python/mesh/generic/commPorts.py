import os
import itertools
from natsort import natsorted

def getCommPorts(commPrefix):
    commPorts = []
    if os.name == 'nt': # windows
        import winreg

        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        except WindowsError:
            raise IterationError

        ports = []
        for i in itertools.count():
            try:
                ports.append(winreg.EnumValue(key, i)[1])
            except EnvironmentError:
                break
        
        for port in ports:
            if commPrefix in port:
                commPorts.append(port)

    #   for i in range(10):
         #          try:
          #                 s = serial.Serial(i)
           #                    s.close()
            #                   commPorts.append('COM' + str(i + 1))
             #           except serial.SerialException:
              #                 pass
    elif os.name == 'posix': # unix
        import glob
        commPorts = glob.glob("/dev/" + commPrefix + "*")
        #commPorts = glob.glob("/dev/ttyUSB*")
    
    return natsorted(commPorts) 
