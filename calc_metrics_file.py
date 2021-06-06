#!/usr/bin/python3

import sys, random

''' At the moment, this file simulates the calculation
	of metrics, and outputs a line of a csv file '''


if len(sys.argv) != 2:
	print("Needs one argument. Usage: calc_metrics_file.py filename | --setup", file=sys.stderr)
	sys.exit(1)


if sys.argv[1] == "--setup" :
	print("file,metric_a,metric_b") # TODO put the actual metrics
	sys.exit(0)


file = sys.argv[1]

print(f'{file},{random.randrange(1000)},555') # TODO put the actual metrics


