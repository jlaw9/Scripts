#!/usr/bin/env python

import webbrowser
import time

est_samples = ["E0033", "E0036", "E0037", "E0062", "E0064", "E0065", "E0067", "E0069", "E0074", "E0091", "E0092", "E0094", "E0133", "E0177", "E0178", "E0179", "E0180", "E0181", "E0182", "E0183", "E0184", "E0185", "E0191", "E0192", "E0194"]

for sample in est_samples:
	webbrowser.open("https://console.aws.amazon.com/s3/home?region=us-west-2#&bucket=childhooddiseases&prefix=Einstein/%s"%sample)
	time.sleep(2)
