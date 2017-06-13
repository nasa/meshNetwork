import subprocess, os

def isBeaglebone():
    # Check if running on Windows (therefore not a BBB)
    if os.name == 'nt': # Windows
        return False
    # Check if running on beaglebone
    proc = subprocess.Popen(['lscpu'], stdout=subprocess.PIPE)
    output = proc.stdout.read().decode('utf-8').split('\n')
    for line in output: # Look for cpu architecture
        if "Architecture" in line:
            cpuType = line.split()[-1]
            if 'arm' in cpuType.lower(): # is a BBB
                return True
            else:
                return False
