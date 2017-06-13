from enum import IntEnum

class CmdStatus(IntEnum):
    accepted = 0
    rejected = -1
    invalid = 1
    notAllowed = 2
    staleTarget = 3

