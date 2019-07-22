import socket
from mesh.generic.radio import Radio
from mesh.generic.customExceptions import NoSocket

class UDPRadio(Radio):

    def __init__(self, config):
        Radio.__init__(self, [], config)	

        # Read port
        self.sockRead = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockRead.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sockRead.bind((config['ipAddr'], config['readPort']))
        self.sockRead.setblocking(0) # non-blocking to prevent hanging thread

        # Write port
        self.sockWrite = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockWrite.setblocking(0)
        self.sockWriteIp = config['ipAddr']
        self.sockWritePort = config['writePort']
        
    def readBytes(self, bufferFlag):
        """Reads raw bytes from udp connection"""
        if not self.sockRead:
            raise NoSocket("No read socket connection available")
            return 0
        
        # Read from socket
        newBytes = []
        try:
            readAttempts = 0
            newBytes = bytearray()
            while readAttempts < 10: # Check for multiple messages
                newData, source = self.sockRead.recvfrom(self.uartNumBytesToRead)
                newBytes = newBytes + newData
                readAttempts = readAttempts + 1
                
        except Exception as e:
            pass
            #print("UDP socket read error.")

        # Process rx bytes
        if newBytes:
            self.processRxBytes(newBytes, bufferFlag)
            return len(newBytes)
        else:
            return 0
        

    def sendBytes(self, msgBytes):
        """Send bytes over udp connection."""
        if not self.sockWrite:
            raise NoSocket("No write socket connection available")
            return 0 
        
        try:
            self.sockWrite.sendto(msgBytes, (self.sockWriteIp, self.sockWritePort))
            return len(msgBytes)
        except Exception as e:
            return 0
            #print(e)
            #print("UDP socket write error.")
