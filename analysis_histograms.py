
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import numpy as np


# TODO byfiles or bycommits?

df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread = joblib.load('Zdump_aftbefdif_readabilnonread')


models = ['bw_score', 'posnett_score', 'dorn_score', 'scalabrino_score', 'issel_readab']
#metrics_for_histograms = ['BW Avg blank lines', 'CC', 'CLLC', 'NLE', 'issel_r_cmplx', 'BW Max Identifiers Length', 'Dorn Visual X Numbers', 'NA', 'Dorn DFT Operators', 'NLA', 'NS', 'TNLA', 'BW Avg Assignment', 'TNA', 'Dorn DFT Conditionals', 'New Semantic Text Coherence Standard', 'Posnett volume']
#metrics_for_histograms = ['BW Avg Assignment', 'BW Avg blank lines', 'BW Avg commas', 'BW Max Identifiers Length', 'Dorn DFT Numbers', 'Dorn DFT Operators', 'Dorn DFT Spaces', 'Dorn Visual X Comments', 'Dorn Visual X Identifiers', 'Dorn Visual X Keywords', 'Dorn Visual X Operators', 'Dorn Visual X Strings', 'issel_r_cmplx', 'NA', 'NL', 'NLA', 'NLE', 'TNA']
metrics_for_histograms = ['BW Avg Assignment', 'BW Avg loops', 'LCOM5', 'New Commented words AVG', 'New Commented words MAX', 'New Synonym commented words AVG', 'NLE', 'NLM', 'NM', 'PUA', 'TNPA']


for model in models:
	
	## Q1a
	a = df_after_readabil[model]
	b = df_befor_readabil[model]
	
	plt.clf() # clear current figure
	plt.hist([a, b], range=(0,1), bins=20, label=['after readability commits','before readability commits'], density=True, histtype='step')
	plt.legend()
	plt.title('Histogram for {} (Q1a)'.format(model))
	#plt.show()
	plt.savefig('histograms/q1a_{}.png'.format(model))
	
	## Q2
	readabil = df_diffs_readabil[model]
	nonread  = df_diffs_nonread[model]
	
	plt.clf() # clear current figure
	plt.hist([readabil, nonread], range=(-0.15, 0.15), bins=20, label=['readability commits','non-readability commits'], density=True, histtype='step')
	plt.legend()
	plt.title('Histogram for {} (Q2)'.format(model))
	#plt.show()
	plt.savefig('histograms/q2_{}.png'.format(model))


for model in metrics_for_histograms: # the difference is that the range is not necessarily (0,1)
	
	## Q1a
	a = df_after_readabil[model]
	b = df_befor_readabil[model]
	
	plt.clf() # clear current figure
	interval = np.nanpercentile([*a, *b], [5, 95])
	# nanpercentile() ignores NaN values. [*a, *b] merges the 2 arrays. We don't need a 2d array here
	
	plt.hist([a, b], range=interval, bins=20, label=['after readability commits','before readability commits'], density=True, histtype='step')
	plt.legend() # sometimes may be better: loc='upper left'
	plt.title('Histogram for {} (Q1a)'.format(model))
	#plt.show()
	safename = model.replace('/','-') # replace slashes
	plt.savefig('histograms/q1a_{}.png'.format(safename))
	
	## Q2
	readabil = df_diffs_readabil[model]
	nonread  = df_diffs_nonread[model]
	
	plt.clf() # clear current figure
	interval = np.nanpercentile([*readabil, *nonread], [5, 95])
	plt.hist([readabil, nonread], range=interval, bins=20, label=['readability commits','non-readability commits'], density=True, histtype='step')
	plt.legend()
	plt.title('Histogram for {} (Q2)'.format(model))
	#plt.show()
	plt.savefig('histograms/q2_{}.png'.format(safename))

