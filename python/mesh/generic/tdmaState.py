from enum import IntEnum, Enum

class TDMAMode(IntEnum):
    sleep = 0
    init = 1
    receive = 2
    transmit = 3
    failsafe = 4
    admin = 7

class TDMABlockTxStatus(Enum):
    false = 0    
    pending = 1
    confirmed = 2
    active = 3

class TDMAStatus(IntEnum):
    nominal = 1
    blockTx = 2
