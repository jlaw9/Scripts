__author__ = 'matt'

import os
import sys
from glob import glob

matches = []
for root, dirnames, filenames in os.walk(sys.argv[1]):
    matches += glob(root+"/results_QC.json")

for match in matches:
    if "QC/results" in match:
        print match