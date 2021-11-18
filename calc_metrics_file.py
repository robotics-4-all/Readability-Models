#!/usr/bin/python3

import re, subprocess, sys, os, csv
from math import exp, fsum, inf


try:
	SCRIPTS_DIR = os.environ['SCRIPTS_DIR']
except KeyError:
	SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
try:
	METRICS_DIR = os.environ['METRICS_DIR']
except KeyError:
	METRICS_DIR = SCRIPTS_DIR + '/metrics' #TODO maybe current dir /metrics
RSMJAR = SCRIPTS_DIR + '/models/rsm.jar'

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

CSV_FIELDS = ['filename', 'bw_score', 'posnett_score', 'dorn_score', 'scalabrino_score', \
	'issel_readab', 'issel_r_cmplx', 'issel_r_cpl', 'issel_r_doc'] + Scalabr_metrics + SMA_metrics


if len(sys.argv) < 2 :
	print("Needs one argument. Usage: calc_metrics_file.py filename | --setup", file=sys.stderr)
	sys.exit(1)

if sys.argv[1] == "--setup" :
	csv_writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELDS)
	csv_writer.writeheader()
	sys.exit(0)


filename = sys.argv[1]
if not os.path.isfile(filename):
	print("Error. File does not exist", file=sys.stderr)
	sys.exit(1)


### Many metrics, Posnett, and Dorn

raw = subprocess.check_output(['java', '-cp', RSMJAR,
	'it.unimol.readability.metric.runnable.ExtractMetrics', filename],
	stderr=subprocess.DEVNULL, encoding="utf-8") # stderr > /dev/null

#comma_metrics = re.sub(r"^.+: (.{3,})\n", "\\1,", raw, 0, re.MULTILINE)

regex_res = re.findall(r"^(.+): (.{3,})$", raw, re.MULTILINE)
# The above is a list of tuples with strings. Make it a dict with floats
metrics = {'filename' : filename}
for line in regex_res: # line is a tuple [metric_name, value]
	metrics[line[0]] = float(line[1])


if len(metrics) != 111: # 1 was the filename
	print("Warning! There were not 110 metrics")


def sigmoid(x):
	if -x > 700:
		x = -inf # To prevent overflow error in exp()
	return 1/(1 + exp(-x))

# POSNETT
tmp = 8.87 - 1.5*metrics['Posnett entropy'] - 0.033*metrics['Posnett volume'] + 0.4*metrics['Posnett lines']
posnett_score = sigmoid(tmp)


# TODO DORN MODEL

def dorn_metrics(filename):

	file = open(filename, 'r')
	long_lines = 0

	for line in file:
		
		line_wspaces = re.sub(r'\t', '    ', line) # replace tabs with 4 spaces
		
		if (len(line_wspaces) - 1) > 113: # 113 = Q3 + 1.5 * (Q3 - Q1) from Dorn java dataset
			long_lines += 1
	
	long_lines_percent = long_lines / metrics['Posnett lines']
	# Do we want percent or absolout num of long lines? TODO
	
	keywords = metrics['BW Avg keywords'] # this is keywords per line
	# Or maybe.. TODO
	keywords = metrics['BW Avg keywords'] * metrics['Posnett lines']
	
	lines_per_identifier = 1 / metrics['BW Avg number of identifiers']
	
	tmp = -0.0388 * metrics['Dorn DFT Spaces'] - 0.0349 * long_lines_percent - \
		0.0114 * lines_per_identifier + 0.004 * keywords # + 0.0065 * 'DFT of syntax' ?? + C ? TODO
		
	return sigmoid(tmp)

dorn_score = dorn_metrics(filename)


### Source Meter Analyser
# we dont call SMA here. We read its resulting file.
# Which file? $METRICS_DIR/curr_sma_class.csv
try:
	reader = open(METRICS_DIR + '/curr_sma_class.csv', 'r')
	
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
	print('curr_sma_class.csv does not exist', file=sys.stderr)
# If it does not exist because for example SMA could not run),
# no problem. Those metric will be left empty


### Buse Weimer

command = "sed '0~8 s/$/\\n###/g' '{0}' | java -jar {1}/models/BW_readability.jar".format(filename, SCRIPTS_DIR)
raw = subprocess.check_output(command, shell=True, encoding="utf-8")

snippet_scores_str = raw.split('\n\n')[1:-1]

# First, make them all floats. then add them and divide by the count
# to get the average BW score of all the snippets
bw_score = fsum(map(float, snippet_scores_str)) / len(snippet_scores_str)



### Scalabrino
try:
	file = open("scalabrino_tmp.txt","r")
	for line in file:

		if line.split('\t')[0] == filename:

			scalabrino_score = float( line.split('\t')[-1] )
			# Gets the part after the last tab, and converts to float
			
			break
	else: # If it was not found
		scalabrino_score = -1
	
	file.close()
	del file
	
except OSError:
	print('scalabrino_tmp.txt does not exist', file=sys.stderr)
	scalabrino_score = -1

### Issel model

def issel_model():

	if not os.path.isfile(METRICS_DIR + '/curr_sma_methd.csv'):
		print("curr_sma_methd.csv does not exist", file=sys.stderr)
		return
	
	methods_sma = pd.read_csv(METRICS_DIR + '/curr_sma_methd.csv')
	
	df_methods_readabil = prediction_per_cluster(methods_sma)
	# should contain at least [filename, LOC, readab, r_cmplx, r_cpl, r_doc]
	
	# Aggregate, from methods -> Files. Group by filename (Path), and take mean
	simple_avg = df_methods_readabil.drop(columns='LOC').groupby('Path').agg('mean')
	
	# Weighted avg with LOC per method
	df_methods_readabil[['readab', 'r_cmplx', 'r_cpl', 'r_doc']] *= df_methods_readabil.LOC # TODO the * doesn work
	weighted_avg = df_methods_readabil.groupby('Path').agg('sum')
	weighted_avg[['readab', 'r_cmplx', 'r_cpl', 'r_doc']] /= weighted_avg.LOC
	weighted_avg = weighted_avg.drop(columns='LOC')
	
	#for attr in ['readab', 'r_cmplx', 'r_cpl', 'r_doc']:
	#	metrics['issel_'+attr] = weighted_avg.loc[filename][attr]
	#weighted_avg.columns = ['issel_'+colname for colname in weighted_avg.columns]
	return simple_avg


### Final stuff. Append to csv

metrics['bw_score'] = bw_score
metrics['posnett_score'] = posnett_score
metrics['dorn_score'] = dorn_score
metrics['scalabrino_score'] = scalabrino_score

# Use a csv.DictWriter and write to STDOUT. Will be redirected to a file named by the commit
csv_writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELDS)
csv_writer.writerow(metrics)

