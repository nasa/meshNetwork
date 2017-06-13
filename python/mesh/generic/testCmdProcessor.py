from switch import switch
from mesh.generic.deserialize import deserialize
from mesh.generic.cmds import TestCmds
from mesh.generic.cmdProcessor import checkCmdCounter

# Processor method
def processMsg(self, cmdId, msg, args):
        nodeStatus = args['nodeStatus'] 
        comm = args['comm']
        
        if len(msg) > 0:
            # Parse command header
            header = deserialize(msg, cmdId, 'header')
            if header != None:
                # Check for command counter
                cmdStatus = checkCmdCounter(self, header, msg, comm)
                if cmdStatus == False: # old command counter
                    return
            
            # Parse message contents
            try: 
                msgContents = deserialize(msg, cmdId, 'body')       
                if msgContents == None:
                    return
            except KeyError:
                print("Invalid command ID.")
                return
            
            # Process message by command id
            for case in switch(cmdId):
                if case(TestCmds['SendDataBlock']):
                    if header['sourceId'] == 0: # message from GCS (node 0)
                        if msgContents['destId'] == self.nodeParams.config.nodeId: # command is for this node
                            print("Send Block Data command received")
                            comm.sendDataBlock(b'1234567890'*100) # start block transfer process
                    break

# Test command processor
TestCmdProcessor = {'cmdList': TestCmds, 'msgProcessor': processMsg}
