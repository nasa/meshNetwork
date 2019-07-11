from enum import IntEnum

class NodeState(object):
    """The NodeState is a container class for storing the state and status data from other nodes in the formation.
    
    Attributes:
        id: Node id of the node whose status is stored in this instance
        present: Boolean flag showing whether this node is currently present in the formation.  Defaults to false and is set true upon first communication received from the node.
        updating: Boolean flag showing whether this node is currently reporting current state data.
        flightMode: Current flight computer mode of this node.
        formationMode: Current formation mode reported by this node.
        state: Current state data of this node.
        timestamp: Timestamp of the current state data.
        numMsgsReceived: Cumulative total number of messages received from this node.
        lastStateUpdateTime: Time that last state update was received.
        lastMsgRcvdTime: Time that last message was received.
        status: Status byte for storing status information about the node.
    """



    def __init__(self, nodeId):
        self.id = nodeId
        self.present = False
        self.updating = False
        self.timeOffset = 127
        self.lastMsgRcvdTime = 0.0
        self.lastStateUpdateTime = 0.0
        self.status = 0
        self.restartConfirmed = False
        
class LinkStatus(IntEnum):
    """Enumeration of mesh link status.

    Attributes:
        NoLink: No direct communication with this node ever.
        Present: Previous direct communication with this node.
        GoodLink: Currently good link to this node.
        BadLink: Currently no link to this node.
    """
    NoLink = 0
    IndirectLink = 2 
    GoodLink = 1
    BadLink = 3

