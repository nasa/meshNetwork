from mesh.generic.radio import Radio
from mesh.generic.checksum import calc8bitFletcherChecksum, compareChecksum
from mesh.generic.li1RadioCmds import Li1RadioCmds, Li1RadioPayloadCmds
from struct import pack, unpack
from math import ceil

Li1HeaderLength = 8
Li1SyncBytes = b'He'
lenSyncBytes = len(Li1SyncBytes)
checksumLen = 2
Li1MaxPayload = 255
class Li1Radio(Radio):
    
    def __init__(self, serial, config):
        Radio.__init__(self, serial, config)
        self.cmdRxBuffer = bytearray()

    def createCommand(self, cmd):
        """Send command to Li-1 Radio."""
        self.createHeader(cmd) # header
        self.createPayload(cmd) # payload
        return cmd['msgBytes']

    def sendMsg(self, msgBytes):
        """Send messages to radio."""
        if len(msgBytes) > 0:
            numMsgs = ceil(len(msgBytes)/Li1MaxPayload) # calculate how many radio messages required
            for i in range(numMsgs):
                # Split into multiple messages
                if len(msgBytes) >= (i+1)*Li1MaxPayload: # get message end
                    msgEnd = (i+1)*Li1MaxPayload
                else:
                    msgEnd = len(msgBytes)
                payload = msgBytes[i*Li1MaxPayload:msgEnd]

                msg = self.createMsg(payload)
                self.serial.write(msg)
    
    def createMsg(self, rawMsg):
        """Create message to send to Li-1 radio."""
        # Create header
        msg = {'commandType': Li1RadioCmds['Transmit'], 'payloadSize': len(rawMsg), 'payload': rawMsg, 'msgBytes': bytearray()} # wrap message in command container
        #msg['payload'] = b'\xc0'*100
        #msg['payloadSize'] = len(msg['payload'])
        self.createCommand(msg)
        
        return msg['msgBytes']

    def createHeader(self, msg):
        """Create message header for Li-1 radio message."""
        # Create header
        #headerBytes = bytearray(Li1HeaderLength)
        headerBytes = Li1SyncBytes # sync bytes
        headerBytes += pack('>H', msg['commandType']) # command type, hex unique command ID sent as unsigned short
        headerBytes += pack('>H', msg['payloadSize']) # payload size, big endian unsigned short integer

        # Create and append checksum
        headerBytes += pack('BB', *calc8bitFletcherChecksum(headerBytes[2:]))
         
        msg['msgBytes'] += headerBytes

    def createPayload(self, msg):
        """Create payload for Li-1 message packet."""
        # Create and append payload checksum
        if 'payload' in msg:
            payloadBytes = msg['payload'] + pack('BB', *calc8bitFletcherChecksum(msg['msgBytes'][lenSyncBytes:] + msg['payload']))
            msg['msgBytes'] += payloadBytes
        else: # no payload
            return
    

    def processRxBytes(self, serBytes, bufferFlag):
        # Search received bytes for commands
        self.cmdRxBuffer += serBytes
        msgEnd = 0
        while msgEnd < len(self.cmdRxBuffer): # Continue searching until end of received bytes
            msgEnd, cmd = self.parseCommand(self.cmdRxBuffer)
            # Sort commands
            if cmd:
                print("Command rx buffer:", self.cmdRxBuffer)
                print(cmd)
                self.cmdRxBuffer = self.cmdRxBuffer[msgEnd:] # clear out parsed bytes
                # Buffer command
                self.cmdBuffer.append(cmd)

                # Check for data
                if cmd['cmdType'] == Li1RadioCmds['ReceivedData'] and cmd['payload'] != None: # Valid data message
                    # Put data in rxBuffer
                    print("Valid data message received.")
                    self.bufferRxMsg(cmd['payload'], bufferFlag)
                else:  # Other command type
                    print(cmd)
                    pass
        if len(self.cmdRxBuffer) > 1000:
            self.cmdRxBuffer = bytearray()

    def parseCmdHeader(self, cmd, serBytes):
        # Parse header
        headerBytes = serBytes[0:Li1HeaderLength] 
        cmdInfo = headerBytes[lenSyncBytes:-checksumLen]
        checksumBytes = headerBytes[-checksumLen:]
                    
        # Check header checksum
        if (compareChecksum(cmdInfo, checksumBytes)):
            #print("Header checksum matches")
            cmd['header'] = cmdInfo
            cmd['rawHeader'] = headerBytes[lenSyncBytes:]
            # Decode command type
            cmd['cmdType'] = unpack('>H', cmd['header'][0:2])[0]
            return True # header found
        else:
            print("Header checksum failed")
            return False # header not found
        

    def parseCmdPayload(self, payloadSize, serBytes, headerBytes):
        # Parse message payload (if present)
        if len(serBytes) >= (payloadSize + checksumLen): # entire message received
            msgEnd = payloadSize + checksumLen
            # Check payload checksum
            payloadBytes = serBytes[0:payloadSize]
            payloadChecksumBytes = serBytes[payloadSize:payloadSize+checksumLen]

            if (compareChecksum(headerBytes+payloadBytes, payloadChecksumBytes)):
                #print("Payload checksum matches")
                #return msgEnd, payloadBytes
                return msgEnd, self.parseAX25Msg(payloadBytes)
            else: # invalid checksum
                print("Invalid payload checksum")
                return msgEnd, None
                
        else: # incomplete command
                #print("Incomplete payload")
                return len(serBytes), None

    def parseAX25Msg(self, msgBytes):
        """Parse AX.25 formatted message."""
        # For now, just discard everything but original message payload."""        
        return msgBytes[16:-2] 

    def parseCommand(self, serBytes):
        """Search raw received bytes for commands."""
    
        cmd = {'header': None, 'payload': None}

        for i in range(len(serBytes) - (lenSyncBytes-1)):
            # Search serial bytes for sync characters
            if (serBytes[i:i+lenSyncBytes] == Li1SyncBytes): # sync bytes found
                #print("Message Found")
                msgStart = i
               
                if (len(serBytes[msgStart:]) >= Li1HeaderLength): # entire header received
                    # Parse command header
                    headerFound = self.parseCmdHeader(cmd, serBytes[msgStart:])
                else: # incomplete command
                    return len(serBytes), None

                # Update buffer position
                msgEnd = msgStart + Li1HeaderLength

                if headerFound:
                    # Check if payload present
                    if cmd['cmdType'] in Li1RadioPayloadCmds.values():
                        payloadSize = unpack('>H', cmd['header'][2:])[0]
                        if payloadSize == 0: # No payload
                            return msgEnd, cmd # header only command
                        elif payloadSize == 65535: # receive error
                            return msgEnd, cmd
                        else: # payload present
                            if len(serBytes) >= (Li1HeaderLength + payloadSize + checksumLen): # entire message received
                                payloadEnd, cmd['payload'] = self.parseCmdPayload(payloadSize, serBytes[msgStart+Li1HeaderLength:], cmd['rawHeader'])
                                msgEnd += payloadEnd # update buffer position
                                if cmd['payload']:
                                    return msgEnd, cmd
                                else:
                                    return msgEnd, None # invalid payload
                            else: # incomplete command
                                return len(serBytes), None
                        
                    else: # no payload
                        return msgEnd, cmd # header only command
            
                else: # invalid header
                    return msgEnd, None

        return len(serBytes), None

    def sendCommand(self, cmd):
        """Issue command to Li-1 radio."""
        
        # Send no-op command
        noOpCmd = {'commandType': Li1RadioCmds['NoOp'], 'payloadSize': 0, 'msgBytes': bytearray()} # wrap message in command container
        self.createHeader(noOpCmd) # header
        self.createPayload(noOpCmd) # payload
        self.serial.write(noOpCmd['msgBytes'])
