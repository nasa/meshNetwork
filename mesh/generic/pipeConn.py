from mesh.generic.multiProcess import getNewBytes
import time

class PipeConn(object):
    """Wrapper class to make pipe connection act like serial link."""
    def __init__(self, conn):
        self.conn = conn
    
    def read(self, numBytesToRead):
        """Reads from pipe connection."""
        serMsgs = getNewBytes(self.conn)
        
        return serMsgs      

    def write(self, msg):
        """Writes to pipe connection."""
        if msg:
            self.conn.send(msg)
