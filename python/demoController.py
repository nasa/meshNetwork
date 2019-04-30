from mesh.generic.nodeController import NodeController

class DemoController(NodeController):   
    """Demo node controller."""

    def executeNode(self):
        """Executes any processing logic required by this node."""

        # Update node status
        self.nodeParams.updateStatus()

        # Send dummy outgoing broadcast message
        self.queueOut[0] = b'12345'
