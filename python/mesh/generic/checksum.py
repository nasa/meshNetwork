from struct import unpack

def calc8bitFletcherChecksum(msgBytes):
    """Calculate 8-bit Fletcher checksum for Li-1 radio packets.

    Args:
        msgBytes: Raw message bytes to calculate checksum of.
    """
    ck_A = 0
    ck_B = 0
    for msgByte in msgBytes:
        ck_A += int(msgByte)
        ck_B += ck_A

    return [ck_A & 0xFF, ck_B & 0xFF]

def compareChecksum(msgBytes, checksumBytes):
    """Compute and compare Li-1 message checksum.

    Args:
        msgBytes: Raw message bytes.
        checksumBytes: Checksum to compare against.
    Returns:
        A boolean of whether checksum matched or not.
"""

    checksum = calc8bitFletcherChecksum(msgBytes)
    msgChecksum = list(unpack('BB', checksumBytes))

    if checksum == msgChecksum:
        return True # check sum matches
    else:
        return False
