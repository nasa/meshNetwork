import pytest
from mesh.generic.dijkstra import findShortestPaths

class TestTDMAComm:
    def setup_method(self, method):
        pass

    def test_findShortestPaths(self):
        """Test Dijkstra path algorithm with different mesh graphs."""
        
        ## Diamond pattern
        startNode = 3
        numNodes = 7
        meshGraph = [[0, 1, 1, 0, 0, 0, 0],
                     [1, 0, 0, 1, 0 ,0, 0],
                     [1, 0, 0, 1, 0, 0, 0],
                     [0, 1, 1, 0, 1, 1, 0],
                     [0, 0, 0, 1, 0, 0, 1],
                     [0, 0, 0, 1, 0, 0, 1],
                     [0, 0, 0, 0, 1, 1, 0]]
        truthPaths = [[[startNode, 1]], [[startNode, 1, 2], [startNode, 4, 2]], [[startNode]], [[startNode, 4]], [[startNode, 4, 5]], [[startNode, 4, 6]], [[startNode, 4, 5, 7], [startNode, 4, 6, 7]]]
        paths = findShortestPaths(numNodes, meshGraph, startNode)
        
        # Verify output
        for node in range(numNodes):
            if (len(truthPaths[node]) == 1):
                assert(paths[node] == truthPaths[node])
            else: # multiple path options
                pathFound = False
                for path in truthPaths[node]: 
                    if (path in paths[node]):
                        pathFound = True
                assert(pathFound == True) # one of the possible paths should have been found   

        ## Circular pattern
        startNode = 3
        numNodes = 6
        meshGraph = [[0, 1, 0, 0, 0, 1],
                     [1, 0, 1, 0, 0 ,0],
                     [0, 1, 0, 1, 0, 0],
                     [0, 0, 1, 0, 1, 0],
                     [0, 0, 0, 1, 0, 1],
                     [0, 0, 0, 0, 1, 0]]
        truthPaths = [[[startNode, 2, 1]], [[startNode, 2]], [[startNode]], [[startNode, 4]], [[startNode, 4, 5]], [[startNode, 4, 5, 6], [startNode, 2, 1, 6]]]
        paths = findShortestPaths(numNodes, meshGraph, startNode)
        
        # Verify output
        for node in range(numNodes):
            if (len(truthPaths[node]) == 1):
                assert(paths[node] == truthPaths[node])
            else: # multiple path options
                pathFound = False
                for path in truthPaths[node]: 
                    if (path in paths[node]):
                        pathFound = True
                assert(pathFound == True) # one of the possible paths should have been found   

        ## Tree pattern
        startNode = 5
        numNodes = 15
        meshGraph = [[0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
                     [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                     [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
                     [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
                     [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]]

        truthPaths = [[[startNode, 2, 1]], [[startNode, 2]], [[startNode, 2, 1, 3]], [[startNode, 2, 4]], [[startNode]], [[startNode, 2, 1, 3, 6]], [[startNode, 2, 1, 3, 7]], [[startNode, 2, 4, 8]], [[startNode, 2, 4, 9]], [[startNode, 10]], [[startNode, 11]], [[startNode, 2, 1, 3, 6, 12]], [[startNode, 2, 1, 3, 6, 13]], [[startNode, 2, 1, 3, 7, 14]], [[startNode, 2, 1, 3, 7, 15]]]
        paths = findShortestPaths(numNodes, meshGraph, startNode)

        # Verify output
        for node in range(numNodes):
            assert(paths[node] == truthPaths[node])

        ## Star pattern
        startNode = 6
        numNodes = 7
        meshGraph = [[0, 1, 1, 1, 1, 1, 1],
                     [1, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 0, 0],
                     [1, 0, 0, 0, 0, 0, 0]]

        truthPaths = [[[startNode, 1]], [[startNode, 1, 2]], [[startNode, 1, 3]], [[startNode, 1, 4]], [[startNode, 1, 5]], [[startNode]], [[startNode, 1, 7]]]
        paths = findShortestPaths(numNodes, meshGraph, startNode)
   
        # Verify output
        for node in range(numNodes):
            assert(paths[node] == truthPaths[node])
        
        ## Tight grid pattern
        startNode = 11
        numNodes = 12
        meshGraph = [[0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0],
                     [1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0],
                     [1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
                     [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
                     [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0],
                     [0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
                     [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
                     [0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                     [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
                     [0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0],
                     [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                     [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0]]
        
        paths = findShortestPaths(numNodes, meshGraph, startNode)
        shortestPathLengths = [2, 2, 1, 3, 2, 3, 1, 2, 3, 4, 0, 1]        

        # Verify output
        for node in range(numNodes):
            assert(len(paths[node][0]) == shortestPathLengths[node] + 1) # verify path lengths
       
    def test_noPathInformation(self):
        """Test that an empty path is provided if path information is not available."""
        
        startNode = 7
        numNodes = 7
        meshGraph = [[0, 1, 1, 0, 0, 0, 0],
                     [1, 0, 0, 1, 0 ,0, 0],
                     [1, 0, 0, 1, 0, 0, 0],
                     [0, 1, 1, 0, 1, 1, 0],
                     [0, 0, 0, 1, 0, 0, 1],
                     [0, 0, 0, 1, 0, 0, 1],
                     [0, 0, 0, 0, 0, 0, 0]]
        paths = findShortestPaths(numNodes, meshGraph, startNode)
        
        # Verify output
        for node in range(numNodes):
            if (node+1 != startNode):
                assert(paths[node] == [])
            else:
                assert(paths[node] == [[startNode]])
