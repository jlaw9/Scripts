__author__ = 'matt'

import os
import sys
import json
from glob import glob

matches = []
for root, dirnames, filenames in os.walk(sys.argv[1]):
    matches += glob(root+"/results_QC.json")

for match in matches:
    if "QC/results" in match:
        results_file = json.load(open(match,'r'))
        print match, results_file['QC_comparisons'].keys()