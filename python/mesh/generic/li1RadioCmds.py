
# Commands with payload
Li1RadioPayloadCmds = {'ReceivedData': 0x2004}

# All commands
Li1RadioCmds = Li1RadioPayloadCmds.copy()
Li1RadioCmds.update({'Transmit': 0x1003, 'NoOp': 0x1001})
