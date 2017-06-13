from mesh.generic.nodeTools import isBeaglebone
from mesh.generic.tdmaTime import getTimeOffset
import pytest
from numbers import Real

class TestTDMATime:
    pytestmark = pytest.mark.skipif(isBeaglebone() == False, reason="requires configured formation node")
    
    def setup_method(self, method):
        pass        
    
    def test_getTimeOffset(self):
        """Test getTimeOffset method."""

        # Test pps offset
        offset = getTimeOffset('pps')
        assert(offset == None or (isinstance(offset, Real) and offset > 0))

        # Test standard offset
        retValue = getTimeOffset('standard')
        assert(isinstance(retValue, tuple))
        assert(isinstance(retValue[0], bool))
        assert(retValue[1] == None or (isinstance(retValue[1], Real) and retValue[1] > 0))
        
