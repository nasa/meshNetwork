from mesh.generic.nodeState import LinkStatus
from mesh.generic.cmds import NodeCmds
from switch import switch

class NodeController(object):   
    """Generic node controller to subtype for specific vehicle types.

    Attributes:
        logFile: File object for logging node data.
        logTime: Time of last write to log file.
        nodeConfig: NodeConfig instance that stores configuration data for this node.
    """

    def __init__(self, nodeParams, logFile=[]):
        # Logging
        self.logFile = logFile      
    
        # Node configuration
        self.nodeParams = nodeParams
   
        # Outgoing node messages
        self.queueOut = [b''] * self.nodeParams.config.commConfig['maxNumSlots']

    def controlNode(self):
        """Function that controls node logic execution.  This functions calls the other node
        logic in the proper order for node execution."""

        # Process commmands
        self.processCommands()

        # Check status of mesh network
        self.monitorNetworkStatus()
        
        # Run unique node behavior
        self.executeNode()  

        # Log data
        self.logData()

    def executeNode(self):
        """Executes any processing logic required by this node."""

        # Update node status
        self.nodeParams.updateStatus()

        pass        

    def processFCCommands(self, FCComm):
        """Performs initial processing of incoming commands and messages from the platform's flight computer."""
        pass

    def processNodeCommands(self, comm):
        """Performs initial processing of incoming commands and messages from the mesh network."""
            
        for cmdId in list(comm.cmdQueue.keys()): # New commands to process
            cmdContents = comm.cmdQueue.pop(cmdId)
            for case in switch(cmdId):
                if case(NodeCmds['ConfigRequest']):
                    configHash = self.nodeParams.config.calculateHash()
                    if configHash == cmdContents:
                        self.nodeParams.configConfirmed = True
                    else:
                        self.nodeParams.configConfirmed = False    
                    break           
            

    def processCommands(self):
        """Performs more specific processing and implementation of commands received over the 
        mesh network."""
        pass

    def logData(self):
        """Logs pertinent node operational and state data."""
        pass

    def monitorNodeUpdates(self):
        """Monitors time since last state update from other nodes."""
        
        # Check that other nodes' states are updating
        if 'nodeStatus' not in self.nodeParams.__dict__ or 'clock' not in self.nodeParams.__dict__:
            return
        for node in self.nodeParams.nodeStatus:
            if (node.lastStateUpdateTime + self.nodeParams.config.nodeUpdateTimeout) < self.nodeParams.clock.getTime(): 
                node.updating = False
            else:
                node.updating = True 
        
    def monitorNetworkStatus(self):
        """Monitors status of other nodes to determine their current status."""

        # Check update status
        self.monitorNodeUpdates()

        # Check node links
        self.nodeParams.checkNodeLinks()
