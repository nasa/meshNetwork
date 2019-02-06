from mesh.generic.formationClock import FormationClock
import time

class TestFormationClock:
    

    def setup_method(self, method):
        
        # Create FormationClock instance

        if method.__name__ == "test_referenceClock":
            self.clock = FormationClock(time.time())
        else:
            self.clock = FormationClock()
            
    def test_nonreferenceClock(self):
        """Test non-referenced clock functionality."""
        startTime = time.time()
        clockTime = self.clock.getTime()
        endTime = time.time()
        assert(clockTime >= startTime and clockTime <= endTime) # Check that returned time is correct
    
    def test_referenceClock(self):
        """Test referenced clock functionality."""
        assert(self.clock.getTime() <= time.time() - self.clock.referenceTime)

    def test_getOffset(self):
        """Test time offset functionality."""
        offset = self.clock.getOffset()
        assert(offset == None)
        
