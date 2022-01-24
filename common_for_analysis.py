
import pandas as pd
import scipy.stats

import sys
sys.path.append('/home/anestis/git/Readability-Models') # to import cliffs_delta
from cliffs_delta import cliffs_delta
# https://github.com/neilernst/cliffsDelta


def cohens_delta(df1, df2):
	s1 = df1.std() ** 2
	s2 = df2.std() ** 2
	n1 = len(df1) - 1
	n2 = len(df2) - 1
	s = ((n1*s1 + n2*s2) / (n1 + n2)) ** 0.5
	
	return (df1.mean(numeric_only=True) - df2.mean(numeric_only=True)) / s

def loadFilesOfCommit(commit):
	try:
		aft = pd.read_csv(commit + '_after.csv')
		bfr = pd.read_csv(commit + '_befor.csv')
	except OSError:
		print("commit {} does not have a csv file".format(commit))
		return
	except pd.errors.EmptyDataError:
		print("commit {} has an empty csv file".format(commit))
		return
	
	aft = aft.set_index('filename').select_dtypes('number')
	bfr = bfr.set_index('filename').select_dtypes('number')
	dif = aft - bfr
	
	return aft, bfr, dif


## Q1
# Cohen's and Cliff's delta between df_after_nonread, df_befor_nonread
# Also for df_after_readabil, df_befor_readabil
def runQ1(perwhat, df_after_readabil, df_befor_readabil, df_after_nonread, df_befor_nonread):

	q1a_cliff = {}
	q1b_cliff = {}
	q1a_ttest = {}
	q1b_ttest = {}
	q1a_wilcoxon = {}
	q1b_wilcoxon = {}
	q1a_cohen = cohens_delta(df_after_readabil, df_befor_readabil)
	q1b_cohen = cohens_delta(df_after_nonread, df_befor_nonread)

	for metric in df_after_readabil.columns:

		q1a_cliff[metric] = cliffs_delta(df_after_readabil[metric], df_befor_readabil[metric])[0]
		q1b_cliff[metric] = cliffs_delta(df_after_nonread[metric],  df_befor_nonread[metric])[0]
		# returns a tuple (delta, 'description like medium')
		
		# We must .dropna() . Otherwise we get 'RuntimeWarning: invalid value encountered in less',
		# and no t-test statistic is given for that metric
		# dropna() does not modify the original dataframe, it returns a copy with the nonempty elements
		# !! Sometimes because of dropna() they will not have the same length!
		notna_idx = df_befor_readabil[metric].notna() & df_after_readabil[metric].notna()
		q1a_ttest[metric] = scipy.stats.ttest_rel(df_after_readabil[metric][notna_idx], df_befor_readabil[metric][notna_idx])
		notna_idx = df_befor_nonread[metric].notna() & df_after_nonread[metric].notna()
		q1b_ttest[metric] = scipy.stats.ttest_rel(df_after_nonread[metric][notna_idx],  df_befor_nonread[metric][notna_idx])
		# Somethimes it throws 'RuntimeWarning: invalid value encountered'
		# This happens when the 2 arrays are identical
		
		try:
			q1a_wilcoxon[metric] = scipy.stats.wilcoxon(df_after_readabil[metric], df_befor_readabil[metric])
		except:	pass
		
		try:
			q1b_wilcoxon[metric] = scipy.stats.wilcoxon(df_after_nonread[metric],  df_befor_nonread[metric])
		except: pass # may throw ValueError: zero_method 'wilcox' and 'pratt' do not work if the x - y is zero for all elements.

	print('Q1 ok')

	results1 = pd.DataFrame({'q1a_cliff':q1a_cliff, 'q1b_cliff':q1b_cliff, 'q1a_ttest':q1a_ttest, 'q1b_ttest':q1b_ttest,
		'q1a_wilcoxon':q1a_wilcoxon, 'q1b_wilcoxon':q1b_wilcoxon, 'q1a_cohen':q1a_cohen, 'q1b_cohen':q1b_cohen})

	for metric in ['q1a_ttest', 'q1b_ttest', 'q1a_wilcoxon', 'q1b_wilcoxon']:
		results1[metric + '_stat'] = results1[metric].map(lambda x: x[0], na_action='ignore') # x[0] == x.statistic
		results1[metric + '_pval'] = results1[metric].map(lambda x: x[1], na_action='ignore') # x[1] == x.pvalue
	# unpack the statistic values into plain numeric columns

	results1.to_csv('results_Q1_{}.csv'.format(perwhat))
	print('saved results of Q1')
	return results1


## Q2
# between readability and non-readabil commits: df_diffs_readabil, df_diffs_nonread
def runQ2(perwhat, df_diffs_readabil, df_diffs_nonread):
	
	q2_cohen = cohens_delta(df_diffs_readabil, df_diffs_nonread)
	q2_cliff = {}
	q2_ttest = {}
	q2_mannwhit = {}

	for metric in df_diffs_readabil.columns:

		q2_cliff[metric] = cliffs_delta(df_diffs_readabil[metric], df_diffs_nonread[metric])[0]
		
		q2_ttest[metric] = scipy.stats.ttest_ind(df_diffs_readabil[metric].dropna(), df_diffs_nonread[metric].dropna())
		# Here .dropna() will return different lengths. But they were different already
		# There is no common commit, so doing ..&.. would return all false!
		
		try:
			q2_mannwhit[metric] = scipy.stats.mannwhitneyu(df_diffs_readabil[metric], df_diffs_nonread[metric])
		except: pass # may throw ValueError: All numbers are identical in mannwhitneyu

	print('Q2 ok')


	# Save results
	results2 = pd.DataFrame({'q2_cliff':q2_cliff, 'q2_cohen':q2_cohen,
				'q2_ttest':q2_ttest, 'q2_mannwhit':q2_mannwhit})
	# We must have cliff firsts, because it tries to determine dtypes and throws
	# AttributeError: 'dict' object has no attribute 'dtype'

	for metric in ['q2_ttest', 'q2_mannwhit']:
		results2[metric + '_stat'] = results2[metric].map(lambda x: x.statistic, na_action='ignore')
		results2[metric + '_pval'] = results2[metric].map(lambda x: x.pvalue, na_action='ignore')
	# unpack the statistic values into plain numeric columns

	results2.to_csv('results_Q2_{}.csv'.format(perwhat))
	print('saved results of Q2')
	return results2

