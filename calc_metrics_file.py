#!/usr/bin/python3

import re, subprocess, sys, os
from math import exp, fsum


if len(sys.argv) < 2 :
	print("Needs one argument. Usage: calc_metrics_file.py filename | --setup", file=sys.stderr)
	sys.exit(1)

if sys.argv[1] == "--setup" :
	print("file,many_metrics_TODO,bw,posnett,dorn,scalabrino") # TODO put the actual metrics
	sys.exit(0)


filename = sys.argv[1]
filename = "/home/anestis/Επιφάνεια εργασίας/tmp_diplom/testfile2.java"
#TODO remove

if not os.path.isfile(filename):
	print("Error. File does not exist", file=sys.stderr)
	sys.exit(1)


### Many metrics, Posnett, and Dorn

raw = subprocess.check_output(['java', '-cp', 'rsm.jar',
	'it.unimol.readability.metric.runnable.ExtractMetrics', filename]).decode("utf-8")

#comma_metrics = re.sub(r"^.+: (.{3,})\n", "\\1,", raw, 0, re.MULTILINE)

regex_res = re.findall(r"^(.+): (.{3,})$", raw, re.MULTILINE)
# The above is a list of tuples with strings. Make it a dict with floats
metrics = {'filename' : filename}
for line in regex_res: # line is a tuple [metric_name, value]
	metrics[line[0]] = float(line[1])


if len(metrics) != 111: # 1 was the filename
	print("Warning! There were not 110 metrics")


# POSNETT
tmp = 8.87 - 1.5*metrics['Posnett entropy'] - 0.033*metrics['Posnett volume'] + 0.4*metrics['Posnett lines']
posnett_score = 1/(1 + exp( -tmp))


tmp = 1 # TODO DORN MODEL
dorn_score = 1/(1 + exp( -tmp))


### Source Meter Analyser
# we dont call SMA here. We read its resulting file.
# Which file? $METRICS_DIR/curr_sma_result.csv

wanted_metrics = ['CC', 'CCL', 'CCO', 'CI', 'CLC', 'CLLC', 'LDC', 'LLDC', 'LCOM5', 'NL', 'NLE', 'WMC', 'CBO', 'CBOI', 'NII', 'NOI', 'RFC', 'AD', 'CD', 'CLOC', 'DLOC', 'PDA', 'PUA', 'TCD', 'TCLOC', 'DIT', 'NOA', 'NOC', 'NOD', 'NOP', 'LLOC', 'LOC', 'NA', 'NG', 'NLA', 'NLG', 'NLM', 'NLPA', 'NLPM', 'NLS', 'NM', 'NOS', 'NPA', 'NPM', 'NS', 'TLLOC', 'TLOC', 'TNA', 'TNG', 'TNLA', 'TNLG', 'TNLM', 'TNLPA', 'TNLPM', 'TNLS', 'TNM', 'TNOS', 'TNPA', 'TNPM', 'TNS', 'WarningBlocker', 'WarningCritical', 'WarningInfo', 'WarningMajor', 'WarningMinor', 'Best Practice Rules', 'Clone Metric Rules', 'Code Style Rules', 'Cohesion Metric Rules', 'Complexity Metric Rules', 'Coupling Metric Rules', 'Design Rules', 'Documentation Metric Rules', 'Documentation Rules', 'Error Prone Rules', 'Inheritance Metric Rules', 'Multithreading Rules', 'Performance Rules', 'Runtime Rules', 'Security Rules', 'Size Metric Rules']
# TODO maybe not the last ones? on;y the 2-4 letters?

with open(os.environ['METRICS_DIR'] + '/curr_sma_result.csv', 'r') as reader:
	
	csv_sma = csv.DictReader(reader)
	
	for row in csv_sma:
		if row['Path'].endswith(filename) and not ('$' in row['Name']):
			# We want the 'main' (not secondary) class of each file
			# The one that doesn't contain $ like UpdateHelper$Result
			
			# add row[...] to metrics
			for m in wanted_metrics:
				metrics[m] = row[m]
			
			break # Stop the search for the main class of the file


### Buse Weimer

# Split to snippets of 8 lines, then give them to BuseWeimer jar
command = "sed '0~8 s/$/\\n###/g' '{0}' | java -jar BW_readability.jar".format(filename)
raw = subprocess.check_output(command, shell=True).decode("utf-8")

snippet_scores_str = raw.split('\n\n')[1:-1]

# First, make them all floats. then add them and divide by the count
# to get the average BW score of all the snippets
bw_score = fsum(map(float, snippet_scores_str)) / len(snippet_scores_str)



### Scalabrino

raw = subprocess.check_output(['java', '-jar', 'rsm.jar', filename]).decode("utf-8")
# TODO maybe quite faster to give all the files together ??

scalabrino_score = float( raw.split('\t')[-1] )
# Gets the part after the last tab, and converts to float



### Final stuff. Append to csv

metrics['bw_score'] = bw_score
metrics['posnett_score'] = posnett_score
metrics['dorn_score'] = dorn_score
metrics['scalabrino_score'] = scalabrino_score

#csv_line = ','.join(map(str, metrics))

# Use a csv.DictWriter and write to STDOUT. Will be redirected to a file named by the commit
# TODO define list with the order of fieldnames
csv_writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
writer.writerow(metrics)


