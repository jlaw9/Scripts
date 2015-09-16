#! /usr/bin/env python2.7

import sys

sample = sys.argv[1]

samples = []
with open("pnet.samples",'r') as input:
	for line in input:
		line = line.strip().split()
		if sample in line:
			if line[-1] == "RUNNING":
				line[-1] = "FINISHED"
		samples.append(line)

with open("pnet.samples","w") as output:
	for line in samples:
		output.write("\t".join(line)+"\n")
	
