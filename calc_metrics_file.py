#!/usr/bin/python3

import re, subprocess, sys, os, csv
from math import exp, fsum


try:
	SCRIPTS_DIR = os.environ['SCRIPTS_DIR']
except KeyError:
	SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
try:
	METRICS_DIR = os.environ['METRICS_DIR']
except KeyError:
	METRICS_DIR = SCRIPTS_DIR + '/metrics' #TODO maybe current dir /metrics
RSMJAR = SCRIPTS_DIR + '/rsm.jar'

SMA_metrics = ['CC', 'CCL', 'CCO', 'CI', 'CLC', 'CLLC', 'LDC', 'LLDC', 'LCOM5', 'NL', 'NLE', 'WMC', 'CBO', 'CBOI', 'NII',
'NOI', 'RFC', 'AD', 'CD', 'CLOC', 'DLOC', 'PDA', 'PUA', 'TCD', 'TCLOC', 'DIT', 'NOA', 'NOC', 'NOD', 'NOP', 'LLOC', 'LOC',
'NA', 'NG', 'NLA', 'NLG', 'NLM', 'NLPA', 'NLPM', 'NLS', 'NM', 'NOS', 'NPA', 'NPM', 'NS', 'TLLOC', 'TLOC', 'TNA', 'TNG',
'TNLA','TNLG', 'TNLM', 'TNLPA', 'TNLPM', 'TNLS', 'TNM', 'TNOS', 'TNPA', 'TNPM', 'TNS']

Scalabr_metrics = ['New Identifiers words AVG', 'New Identifiers words MIN', 'New Abstractness words AVG', 'New Abstractness words MAX', 'New Abstractness words MIN', 'New Commented words AVG', 'New Commented words MAX', 'New Synonym commented words AVG', 'New Synonym commented words MAX', 'New Expression complexity AVG', 'New Expression complexity MAX', 'New Expression complexity MIN',
'New Method chains AVG', 'New Method chains MAX', 'New Method chains MIN', 'New Comments readability', 'New Number of senses AVG', 'New Number of senses MAX', 'New Semantic Text Coherence Standard', 'New Semantic Text Coherence Normalized', 'New Text Coherence AVG', 'New Text Coherence MIN', 'New Text Coherence MAX', 'BW Avg Assignment', 'BW Avg blank lines', 'BW Avg commas', 'BW Avg comments',
'BW Avg comparisons', 'BW Avg Identifiers Length', 'BW Avg conditionals', 'BW Avg indentation length', 'BW Avg keywords', 'BW Avg line length', 'BW Avg loops', 'BW Avg number of identifiers', 'BW Avg numbers', 'BW Avg operators', 'BW Avg parenthesis', 'BW Avg periods', 'BW Avg spaces', 'BW Max Identifiers Length', 'BW Max indentation', 'BW Max keywords', 'BW Max line length',
'BW Max number of identifiers', 'BW Max numbers', 'BW Max char', 'BW Max words', 'Posnett entropy', 'Posnett volume', 'Posnett lines', 'Dorn DFT Assignments', 'Dorn DFT Commas', 'Dorn DFT Comments', 'Dorn DFT Comparisons', 'Dorn DFT Conditionals', 'Dorn DFT Indentations', 'Dorn DFT Keywords', 'Dorn DFT LineLengths', 'Dorn DFT Loops', 'Dorn DFT Identifiers', 'Dorn DFT Numbers', 'Dorn DFT Operators',
'Dorn DFT Parenthesis', 'Dorn DFT Periods', 'Dorn DFT Spaces', 'Dorn Visual X Comments', 'Dorn Visual Y Comments', 'Dorn Visual X Identifiers', 'Dorn Visual Y Identifiers', 'Dorn Visual X Keywords', 'Dorn Visual Y Keywords', 'Dorn Visual X Numbers', 'Dorn Visual Y Numbers', 'Dorn Visual X Strings', 'Dorn Visual Y Strings', 'Dorn Visual X Literals', 'Dorn Visual Y Literals',
'Dorn Visual X Operators', 'Dorn Visual Y Operators', 'Dorn Areas Comments', 'Dorn Areas Identifiers', 'Dorn Areas Keywords', 'Dorn Areas Numbers', 'Dorn Areas Strings', 'Dorn Areas Literals', 'Dorn Areas Operators', 'Dorn Areas Identifiers/Comments', 'Dorn Areas Keywords/Comments', 'Dorn Areas Numbers/Comments', 'Dorn Areas Strings/Comments', 'Dorn Areas Literals/Comments', 'Dorn Areas Operators/Comments',
'Dorn Areas Keywords/Identifiers', 'Dorn Areas Numbers/Identifiers', 'Dorn Areas Strings/Identifiers', 'Dorn Areas Literals/Identifiers', 'Dorn Areas Operators/Identifiers', 'Dorn Areas Numbers/Keywords', 'Dorn Areas Strings/Keywords', 'Dorn Areas Literals/Keywords', 'Dorn Areas Operators/Keywords', 'Dorn Areas Strings/Numbers', 'Dorn Areas Literals/Numbers', 'Dorn Areas Operators/Numbers', 'Dorn Areas Literals/Strings', 'Dorn Areas Operators/Strings', 'Dorn Areas Operators/Literals', 'Dorn align blocks', 'Dorn align extent']

CSV_FIELDS = ['filename', 'bw_score', 'posnett_score', 'dorn_score', 'scalabrino_score'] + Scalabr_metrics + SMA_metrics


if len(sys.argv) < 2 :
	print("Needs one argument. Usage: calc_metrics_file.py filename | --setup", file=sys.stderr)
	sys.exit(1)

if sys.argv[1] == "--setup" :
	csv_writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELDS)
	csv_writer.writeheader()
	sys.exit(0)


filename = sys.argv[1]
if filename == '-':
	filename = "/home/anestis/Επιφάνεια εργασίας/tmp_diplom/testfile2.java"
#TODO remove

if not os.path.isfile(filename):
	print("Error. File does not exist", file=sys.stderr)
	sys.exit(1)


### Many metrics, Posnett, and Dorn

raw = subprocess.check_output(['java', '-cp', RSMJAR,
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
try:
	reader = open(METRICS_DIR + '/curr_sma_result.csv', 'r')
	
	csv_sma = csv.DictReader(reader)
	
	for row in csv_sma:
		if row['Path'].endswith(filename) and not ('$' in row['Name']):
			# We want the 'main' (not secondary) class of each file
			# The one that doesn't contain $ like UpdateHelper$Result
			
			# add row[...] to metrics
			for m in SMA_metrics:
				metrics[m] = row[m]
			
			break # Stop the search for the main class of the file
	
	reader.close()
	del reader, csv_sma
	
except OSError:
	print('curr_sma_result.csv does not exist', file=sys.stderr)
# If it does not exist because for example SMA could not run),
# no problem. Those metric will be left empty


### Buse Weimer

command = "sed '0~8 s/$/\\n###/g' '{0}' | java -jar {1}/BW_readability.jar".format(filename, SCRIPTS_DIR)
raw = subprocess.check_output(command, shell=True).decode("utf-8")

snippet_scores_str = raw.split('\n\n')[1:-1]

# First, make them all floats. then add them and divide by the count
# to get the average BW score of all the snippets
bw_score = fsum(map(float, snippet_scores_str)) / len(snippet_scores_str)



### Scalabrino
with open(METRICS_DIR + "/scalabrino_tmp.txt","r") as file:
	for line in file:

		if line.split('\t')[0] == filename:

			scalabrino_score = float( line.split('\t')[-1] )
			# Gets the part after the last tab, and converts to float
			
			break
	else: # If it was not found
		scalabrino_score = -1


### Final stuff. Append to csv

metrics['bw_score'] = bw_score
metrics['posnett_score'] = posnett_score
metrics['dorn_score'] = dorn_score
metrics['scalabrino_score'] = scalabrino_score

# Use a csv.DictWriter and write to STDOUT. Will be redirected to a file named by the commit
csv_writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELDS)
csv_writer.writerow(metrics)

