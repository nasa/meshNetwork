
class NodeExecutive(object):
    """Generic node executive controller to subtype for specific vehicle types.

    The node executive is responsible for communicating over all serial links (flight computer and mesh networks), processing messages received over those links, and running the node control logic to perform the desired formation behavior.  This class has the generic framework for the node executive, but each specific platform type should derive their own executive type from this class.

    Attributes:
        nodeConfig: Node configuration information.
        nodeController: Node controller instance for this node.
        nodeComm: Array of node communication instances for each mesh network.
        FCComm: Node communication instance for serial link to flight computer.
        FCLogFile: File for logging flight computer data.
    """

    def __init__(self, nodeParams, nodeController, nodeComm, FCComm, fcLogFile):
        self.nodeParams = nodeParams
        
        self.nodeController = nodeController
    
        # Initialize node and flight computer communication variables
        self.nodeComm = nodeComm
        self.FCComm = FCComm

        self.FCLogFile = fcLogFile

    def executeNodeSoftware(self):
        """This function executes all node software in the proper sequence."""
        # Process data from flight computer
        self.processFCMsg()     
        
        # Check mesh serial connections for new messages
        for comm in self.nodeComm:
            self.processNodeMsg(comm)   
    
        # Run node control algorithms           
        self.nodeController.controlNode()

        # Send commands to flight computer
        self.sendFCCmds()

        # Send out node status update to other formation nodes
        self.sendNodeCmds()
    
    def processFCMsg(self): # Process message from flight computer
        """Processes messages received from the vehicle's flight computer."""
        if self.FCComm:
            self.FCComm.readMsgs()

    def processNodeMsg(self, comm): # Process messages from other nodes
        """Processes messages received from other nodes over the mesh networks."""
        comm.readMsgs()

    def sendFCCmds(self): # Send required commands to flight computer
        """Sends messages and commands to the vehicle's flight computer."""
        pass

    def sendNodeCmds(self): # Send command/data messages to other nodes
        """Sends messages and commands to the other formation nodes."""
        pass


