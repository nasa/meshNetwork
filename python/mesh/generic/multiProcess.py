
        
def getNewBytes(conn):
    """Checks a pipe connection for new messages."""
    # Check for new messages
    readAttempts = 0
    receivedData = bytearray()
    while readAttempts < 100:
        dataAvailable = conn.poll(0)
        if dataAvailable:
            receivedData += conn.recv_bytes()
        else:
            break
        readAttempts += 1

    return receivedData

def getNewMsgs(conn):
    """Checks a pipe connection for new messages."""
    # Check for new messages
    readAttempts = 0
    receivedData = []
    while readAttempts < 100:
        dataAvailable = conn.poll(0)
        if dataAvailable:
            receivedData.append(conn.recv())
        else:
            break
        readAttempts += 1

    return receivedData
