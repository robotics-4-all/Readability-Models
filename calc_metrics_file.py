#!/usr/bin/python3

import re, subprocess, sys, os
from math import fsum, inf
import numpy as np
import pandas as pd
from models.issel import aggregation_functions as issel

try:
	SCRIPTS_DIR = os.environ['SCRIPTS_DIR']
except KeyError:
	SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
try:
	METRICS_DIR = os.environ['METRICS_DIR']
except KeyError:
	METRICS_DIR = SCRIPTS_DIR + '/metrics'
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

# TODO maybe we don't need all these
CSV_FIELDS = ['filename', 'bw_score', 'posnett_score', 'dorn_score', 'scalabrino_score', \
	'issel_readab', 'issel_r_cmplx', 'issel_r_cpl', 'issel_r_doc'] + Scalabr_metrics + SMA_metrics


if len(sys.argv) < 2 :
	print("Needs >=1 argument. Usage: calc_metrics_file.py filename...", file=sys.stderr)
	sys.exit(1)


filenames = sys.argv[1:]


### Scalabrino many metrics, Posnett, and Dorn
def many_metrics_rms(filename):

	raw = subprocess.check_output(['java', '-cp', RSMJAR,
		'it.unimol.readability.metric.runnable.ExtractMetrics', filename],
		stderr=subprocess.DEVNULL, encoding="utf-8") # stderr > /dev/null

	#comma_metrics = re.sub(r"^.+: (.{3,})\n", "\\1,", raw, 0, re.MULTILINE)

	regex_res = re.findall(r"^(.+): (.{3,})$", raw, re.MULTILINE)
	# The above is a list of tuples with strings. Make it a dict (for now with strings)
	
	file_metrics = dict(regex_res) # the values are still strings
	file_metrics['filename'] = filename
	
	if len(file_metrics) != 111: # 1 was the filename
		print("Warning! There were not 110 metrics from" + filename, file=sys.stderr)
	
	return file_metrics


def setup_df_many():
	
	list_of_dicts = []
	
	for filename in filenames:
	
		if not os.path.isfile(filename):
			print("Error. File {} does not exist".format(filename), file=sys.stderr)
			sys.exit(1)
		
		file_metrics = many_metrics_rms(filename)
		list_of_dicts.append(file_metrics)
	
	metrics = pd.DataFrame(list_of_dicts).set_index('filename')
	
	return metrics.astype(float).convert_dtypes()
	# Convert all strings to floats. Then, when possible, convert floats to ints


def sigmoid(x):
	
	if np.ndim(x) > 0:
		x[-x > 700] = -inf
	elif -x > 700:
		x = -inf # To prevent overflow error in exp()
	
	return 1/(1 + np.exp(-x))


# POSNETT
def posnett(metrics):
	tmp = 8.87 - 1.5*metrics['Posnett entropy'] - \
		0.033*metrics['Posnett volume'] + 0.4*metrics['Posnett lines']
	
	tmp.name = 'posnett_score'
	return sigmoid(tmp)


# TODO DORN MODEL

def dorn_metrics(metrics):

	metrics['Dorn long lines'] = np.zeros(len(metrics))
	
	for filename in metrics.index: # the index column is the filename
		
		try:
			file = open(filename, 'r')
			for line in file:
				
				line_wspaces = re.sub(r'\t', '    ', line) # replace tabs with 4 spaces
				
				if (len(line_wspaces)-1) > 113: # 113 = Q3 + 1.5 * (Q3 - Q1) from Dorn java dataset
					metrics['Dorn long lines'][filename] += 1
		except:
			metrics['Dorn long lines'][filename] = None
		finally:
			file.close()
	
	metrics['Dorn long lines'] /= metrics['Posnett lines'].values # element-wise division. To get percent
	# Do we want percent or absolute num of long lines? TODO
	
	keywords = metrics['BW Avg keywords'] # this is keywords per line
	# Or maybe.. TODO
	#keywords = metrics['BW Avg keywords'] * metrics['Posnett lines']
	
	lines_per_identifier = 1 / metrics['BW Avg number of identifiers']
	
	tmp = -0.0388 * metrics['Dorn DFT Spaces'] - 0.0349 * metrics['Dorn long lines'] - \
		0.0114 * lines_per_identifier + 0.004 * keywords + 1.4 # + 0.0065 * 'DFT of syntax' ? TODO
	# Best value for the constant is found to be 1.4 from Dorn's snippets and scores
	
	tmp.name = 'dorn_score'
	return sigmoid(tmp)


def makeFilepathRelative(df):
	
	curr_dir = os.getcwd() + '/'
	nskip = len(curr_dir)
	new_index = []
	
	for idxEl in df.index:
		if idxEl.startswith(curr_dir):
			new_index.append(idxEl[nskip:]) # skip the first chars
		else:
			new_index.append(idxEl)
			print("warning: dataframe idex does not start with curr_dir", file=sys.stderr)
	df.index = new_index
	return df
	

### Source Meter Analyser
# we dont call SMA here. We read its resulting file.
# Which file? ./curr_sma_class.csv
def sma_parse():
	
	if not os.path.isfile('curr_sma_class.csv'):
		print("curr_sma_class.csv does not exist", file=sys.stderr)
		return
	
	class_sma = pd.read_csv('curr_sma_class.csv')
	
	# We want the 'main' (not secondary) class of each file
	# The one that doesn't contain $ like UpdateHelper$Result
	secondary_classes = class_sma['Name'].str.contains('\$') # This is a bool array
	class_sma = class_sma.drop(class_sma.index[secondary_classes])
	
	return makeFilepathRelative(class_sma.set_index('Path', verify_integrity=True))

# If it does not exist because for example SMA could not run),
# no problem. Those metric will be left empty


### Buse Weimer

def buse_weimer(filename):
	command = "sed '0~8 s/$/\\n###/g' '{0}' | java -jar '{1}/models/BW_readability.jar'".format(filename, SCRIPTS_DIR)
	raw = subprocess.check_output(command, shell=True, encoding="utf-8")

	snippet_scores_str = raw.split('\n\n')[1:-1]

	# First, make them all floats. then add them and divide by the count
	# to get the average BW score of all the snippets
	return fsum(map(float, snippet_scores_str)) / len(snippet_scores_str)



### Scalabrino
def scalabrino():

	if not os.path.isfile('scalabrino_tmp.txt'):
		print("Error. scalabrino_tmp.txt does not exist", file=sys.stderr)
		return
	
	scal_df = pd.read_csv('scalabrino_tmp.txt', sep='\t', \
		index_col=0, names=['filename', 'scalabrino_score'])
		
	return scal_df


### Issel model
def issel_model():

	if not os.path.isfile('curr_sma_methd.csv'):
		print("curr_sma_methd.csv does not exist", file=sys.stderr)
		return
	
	methods_sma = pd.read_csv('curr_sma_methd.csv')
	
	df_methods_readabil = issel.prediction_per_cluster(methods_sma)
	# should contain at least [filename, LOC, readab, r_cmplx, r_cpl, r_doc]
	
	# Aggregate, from methods -> Files. Group by filename (Path), and take mean
	#simple_avg = df_methods_readabil.drop(columns='LOC').groupby('Path').agg('mean')
	
	# Weighted avg with LOC per method
	for col in ['readab', 'r_cmplx', 'r_cpl', 'r_doc']:
		df_methods_readabil[col] *= df_methods_readabil.LOC.values
	
	weighted_avg = df_methods_readabil.groupby('Path').agg('sum')
	
	for col in ['readab', 'r_cmplx', 'r_cpl', 'r_doc']:
		weighted_avg[col] /= weighted_avg.LOC.values
	
	weighted_avg = weighted_avg.drop(columns='LOC').add_prefix('issel_') # adds prefix to column names
	return makeFilepathRelative(weighted_avg);
	
	#return simple_avg


### Main function
def main():
	
	metrics = setup_df_many() # metrics from Scalabrino jar
	
	bw_list = []
	for filename in filenames:
		try:
			bw_score = buse_weimer(filename)
		except:
			bw_score = None
		bw_list.append(bw_score)
	bw_score = pd.Series(bw_list, index=filenames, dtype=float, name='bw_score')
	
	posnett_score = posnett(metrics)
	dorn_score = dorn_metrics(metrics)
	scalabrino_score = scalabrino()
	
	issel_metrics = issel_model()
	if isinstance(issel_metrics, pd.DataFrame): # if not null
		metrics = metrics.join(issel_metrics)
	
	sma_by_class = sma_parse()
	if isinstance(sma_by_class, pd.DataFrame): # if not null
		metrics = metrics.join(sma_by_class)
	
	
	metrics = pd.concat([metrics, bw_score, posnett_score, dorn_score, scalabrino_score], axis=1)
	# The columns names are set in the functions
	
	metrics.index.name = 'filename'
	
	# Write csv to STDOUT. Will be redirected to a file named by the commit
	metrics.to_csv(sys.stdout)
	#TODO here KeyError: "['filename'] not in index
	# Maybe remove the columns=CSV_FIELDS

if __name__ == '__main__':
	main()

