from copy import deepcopy
from mesh.generic.nodeState import LinkStatus

def findShortestPaths(numNodes, meshGraph, startNode):
    ## Find shortest path to all other nodes using Dijkstra's algorithm
    
    # Initialize arrays
    pathArray = [[i+1,100,[-1]] for i in range(numNodes)]
    #visited = [startNode-1]
    visited = []
    pathArray[startNode-1][1] = 0 # path to self is zero
    unvisited = [i for i in range(numNodes)]
    #unvisited.remove(startNode-1) # start node has been visited
        
    # Start search
    currentNode = startNode-1
    pathArray[currentNode][2] = [startNode]
    while (unvisited): # continue until all nodes visited
        nextNode = -1
        nextLength = 100
        for node in range(len(meshGraph[currentNode])):
            mapEntry = [1 if (link == LinkStatus.GoodLink) else 0 for link in meshGraph[currentNode]] # filter out stale or no links

            if (mapEntry[node] > 0): # link exists to this node
                # Shorter path to this node
                if (mapEntry[node] + pathArray[currentNode][1] < pathArray[node][1]):
                    pathArray[node][1] = mapEntry[node] + pathArray[currentNode][1] # store shorter path to this node
                    pathArray[node][2][0] = currentNode + 1 # store previous node
    
        # Visit next closest unvisited node
        visited.append(currentNode)
        unvisited.remove(currentNode)
        
        if len(unvisited) == 0: # all nodes visited so break out of loop
            break
            
        nextNode = unvisited[0]
        for node in unvisited:
            if (pathArray[node][1] < pathArray[nextNode][1]): # closer node
                nextNode = node
                
        currentNode = nextNode
    
    # Populate paths to all nodes
    pathMap = []
    for node in range(numNodes):
        currentNode = node + 1
        currentPath = [currentNode] # start path
        if (pathArray[node][2] != [-1]): # path information available
            paths = buildPaths(currentNode, startNode, currentPath, pathArray)
        else:
            paths = []
        #print("Shortest paths to node " + str(node+1) + ": ", paths)
        pathMap.append(paths)
    return pathMap
    
 
        
       
  
def buildPaths(currentNode, startNode, currentPath, pathArray):        
    outPaths = []
    paths = []
    for node in pathArray[currentNode-1][2]: # Check for path branches
        if (currentNode != node): # path continues
            newPath = deepcopy(currentPath)
            newPath.insert(0,node)
            paths.append(newPath)
    
    if (len(paths) == 0): # no path found # TODO: Is this needed
        return [currentPath]
    
    # Iterate through path branches
    for path in paths: 
        if (path[0] != startNode): # continue path
            newPaths = buildPaths(path[0], startNode, path, pathArray)
            for newPath in newPaths: # Add determined paths to output
                outPaths.append(newPath)
        else: # path ended
            outPaths.append(path)
    
    
    return outPaths
                
nodeArchitecture =[[0, 1, 0, 0, 0, 1], # circle
                   [1, 0, 1, 0, 0, 0],
                   [0, 1, 0, 1, 0, 0],
                   [0, 0, 1, 0, 1, 0],
                   [0, 0, 0, 1, 0, 1],
                   [1, 0, 0, 0, 1, 0]]

# nodeArchitecture =[[0, 0, 0, 1, 0, 0], # single diamond
                   # [0, 0, 1, 1, 1, 0],
                   # [0, 1, 0, 1, 0, 0],
                   # [1, 1, 1, 0, 0, 0],
                   # [0, 1, 0, 0, 0, 1],
                   # [0, 0, 0, 0, 1, 0]]
                   
# Double diamond
# nodeArchitecture =[[0, 1, 1, 0, 0, 0, 0],
                   # [1, 0, 0, 1, 0, 0, 1],
                   # [1, 0, 0, 1, 0, 0, 0],
                   # [0, 1, 1, 0, 1, 1, 0],
                   # [0, 0, 0, 1, 0, 0, 1],
                   # [0, 0, 0, 1, 0, 0, 1],
                   # [0, 1, 0, 0, 1, 1, 0]]
                   
# Tight grid
# nodeArchitecture = [[0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0],
                    # [1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0],
                    # [1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1],
                    # [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
                    # [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0],
                    # [0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
                    # [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
                    # [0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                    # [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0],
                    # [0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0],
                    # [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                    # [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0]]
                   
# Find shortest paths to each other node
allPaths = [[]*len(nodeArchitecture)] * len(nodeArchitecture)
for node in range(len(nodeArchitecture)):
    startNode = node + 1
    paths = findShortestPaths(len(nodeArchitecture), nodeArchitecture, startNode)
#    print(paths)
    allPaths[node] = paths    
#paths = findShortestPaths(len(nodeArchitecture), nodeArchitecture, 12)
    
# Test relay logic
sourceId = 4
destId = 6

relay = False

for node in range(len(nodeArchitecture)):
    currentNodeId = node + 1
    if currentNodeId == sourceId or currentNodeId == destId:
        continue
    lenPathToSource = len(allPaths[currentNodeId-1][sourceId-1][0])-1
    lenPathToDest = len(allPaths[currentNodeId-1][destId-1][0])-1
    lenSourceToDest = len(allPaths[sourceId-1][destId-1][0])-1
    #print(allPaths[sourceId-1][destId-1])
    #print(lenPathToSource, lenPathToDest, lenSourceToDest)
    if (lenSourceToDest >= (lenPathToDest + lenPathToSource)):
        relay = True


# for path in allPaths[sourceId-1][destId-1]:
    # if (currentNodeId in path or len(path) <): # sending node is on the path to the destination
        # relay = True
        # break

    #print("Current node, relay: ", currentNodeId, relay)

    relay = False



