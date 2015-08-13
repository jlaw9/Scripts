#! /usr/bin/env python2.7
import sys
import time
from subprocess import Popen, PIPE
print sys.argv
found = False

print "SEARCHING FOR KEYWORD: ", sys.argv[2]
while not found:
	with open("nohup.out",'r') as log:
		
		for line in log:
			if sys.argv[2].upper() in line.upper():
				found = True
		time.sleep(1)


output, error = Popen("ps aux".split(" "), stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()

output = output.split("\n")
kill_count = 0
for line in output:
	if sys.argv[1] in line and sys.argv[0] not in line:
		pid = line.split()[1]
		Popen(["kill", pid])
		kill_count += 1

if kill_count == 0:
	print "The process to kill was not found."
else:
	print kill_count, "processes were killed."
