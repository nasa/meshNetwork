import subprocess, time, sys, threading

def getTimeOffset(offsetType='standard'):
    if offsetType == None: # no offset calculation
        return 0.0 # default to no offset
    elif offsetType == 'ntp-pps':
        # Parse ntpq -p command
        try:
            proc = subprocess.Popen(['ntpq', '-p'], stdout=subprocess.PIPE)
            output = proc.stdout.read().decode('utf-8').split('\n')
        except:
            return None
        
        offset = None
        for line in output:
            if "PPS" in line:
                ppsStatus = line.split()
                if ppsStatus[4].isdigit(): # last update value is only digits so is seconds
                    if int(ppsStatus[4]) < 32: # last update less than 2 poll cycles old
                        offset = abs(float(ppsStatus[8]))
                elif ppsStatus[4] == '-': # could be 0 or no response - check if good reach
                    if ppsStatus[6].isdigit() and int(ppsStatus[6]) > 177: # no more than 1 missed in last 8 polls
                        offset = abs(float(ppsStatus[8]))
                break

        return offset

    elif offsetType == 'ntp':
        # Parse ntpq -crv command
        proc = subprocess.Popen(['ntpq', '-crv'], stdout=subprocess.PIPE)
        output = proc.stdout.read()
    
        ntpStatus = str(output).replace(' ', '').split(',') # remove whitespace and split string
        serverSynched = False
        offset = None
        for entry in ntpStatus:
            if entry == 'sync_pps': # PPS sync
                serverSynched = True
            elif serverSynched and entry[0:6] == 'offset': # time offset 
                offset = abs(float(entry[7:]))
                #print("Offset:", str(offset))
        return serverSynched, offset

    return None

