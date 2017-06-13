from mesh.generic.navigation import convertLatLonAlt, Navigation

class TestNavigation:
    
    def setup_method(self, method):
        self.navigation = Navigation()
    
    def test_update(self):
        """Test update method of Navigation class."""
        ## Set state using update method and confirm change
        state = [123.456, 999.888, 100.200]
        time = 505.3
        
        # Pre-update check
        assert(self.navigation.state != state)
        assert(self.navigation.timestamp != time)

        self.navigation.update(state, time)

        # Post-update check
        assert(self.navigation.state == state)
        assert(self.navigation.timestamp == time)
        

    def test_convertLatLonAlt(self):
        """Test conversion of latitude, longitude, and and altitude."""
        lla = [34.987654321, -85.123456789, 20.5678]
        precision = [10000, 10000, 10]
        
        # Test default conversion to int
        convertedLLA = convertLatLonAlt(lla)
        self.checkConvertedLLA(convertedLLA, lla, 'int')        

        # Test default conversion to float
        floatLLA = convertLatLonAlt(convertedLLA, 'float')
        self.checkConvertedLLA(floatLLA, convertedLLA, 'float')     
        
        # Test conversion with provided precision
        convertedLLA = convertLatLonAlt(lla, precision=precision)
        self.checkConvertedLLA(convertedLLA, lla, 'int', precision)     
        floatLLA = convertLatLonAlt(convertedLLA, 'float', precision)
        self.checkConvertedLLA(floatLLA, convertedLLA, 'float', precision)      
        
    def checkConvertedLLA(self, convertedLLA, truthLLA, conversion, precision=[10000000,100]):
        for i in range(len(truthLLA)):
            if i < 2:
                prec = precision[0]
            else:
                prec = precision[1]
            if conversion == 'int':
                assert(convertedLLA[i] == int(truthLLA[i]*prec))
            else: # float
                assert(convertedLLA[i] == truthLLA[i]/float(prec))
    
