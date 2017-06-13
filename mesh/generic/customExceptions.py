import serial

class NoSerialConnection(serial.SerialException):
    """Exception to raise if trying to read/write to invalid serial connection."""

class NoSocket(serial.SerialException):
    """Exception to raise if trying to read/write to invalid socket connection."""

class NoCommandHeader(Exception):
    """Exception to raise if required commmand header missing."""

class InvalidCmdCounter(Exception):
    """Exception to raise if attempt made to set command counter outside of allowable range."""

class NoCommandHeaderDefined(Exception):
    """Exception to raise if command does not define a header."""

class InvalidTDMASlotNumber(Exception):
    """Exception to raise if TDMA slot number is invalid."""
