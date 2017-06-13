from mesh.generic.commPorts import getCommPorts
import os
class TestCommPorts:
    
    def setup_method(self, method):
        pass

    def test_getCommPorts(self):
        """Test getCommPorts functionality on the appropriate os type."""
        if os.name == 'posix': # unix system
            testPrefix = 'tty'
            testValue = '/dev/' + testPrefix
        elif os.name == 'nt': # windows system
            testPrefix == 'COM'
            testValue = testPrefix

        # Get serial ports
        commPorts = getCommPorts(testPrefix)
        print(commPorts)    
        if commPorts:
            for port in commPorts:
                assert(port[0:len(testValue)] == testValue)
