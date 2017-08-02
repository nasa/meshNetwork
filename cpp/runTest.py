from subprocess import Popen, call
import time
import argparse

parser = argparse.ArgumentParser(description="Run unit tests")
parser.add_argument('-f', '--filter', action='store', default="*", help="Filter tests to run")
args = parser.parse_args()
print(args)
argValues = vars(args)

# Open virtual serial port
serP = Popen(["sudo", "socat", "pty,link=/dev/ttyV2,raw", "pty,link=/dev/ttyV3,raw"], shell=False)
time.sleep(0.5)

# Execute unit tests
testFilter = argValues['filter']
call(["sudo", "./run_test", "--gtest_filter=" + testFilter])

serP.terminate()
