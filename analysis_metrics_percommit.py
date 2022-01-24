
import pandas as pd
import joblib
import common_for_analysis


def loadFindMeansOfCommit(commit):
	try:
		aft, bfr, dif = common_for_analysis.loadFilesOfCommit(commit)
	except TypeError: # if the function did not return anything, it will try to unpack None to 3 variables
		return
	
	aft = aft.mean(numeric_only=True).dropna()
	bfr = bfr.mean(numeric_only=True).dropna()
	dif = dif.mean(numeric_only=True).dropna()
	
	aft.name = commit # this will be the index in the df
	bfr.name = commit
	dif.name = commit
	
	return aft, bfr, dif


def read_from_csvs():
	with open('all_true_readabil_commits.txt', 'r') as reader:
		readab_commits = [ line[0:10] for line in reader ]

	# load nonread_commits
	with open('all_nonread_commits.txt', 'r') as reader:
		nonread_commits = [ line[0:10] for line in reader ]


	df_after_readabil = [] # MUST NOT do a = b = c = [], because they will refer to the same!!
	df_befor_readabil = []
	df_diffs_readabil = []

	for commit in readab_commits:
		
		aftbfrdif = loadFindMeansOfCommit(commit)
		
		if aftbfrdif is not None:
			df_after_readabil.append(aftbfrdif[0])
			df_befor_readabil.append(aftbfrdif[1])
			df_diffs_readabil.append(aftbfrdif[2])
	
	df_after_readabil = pd.DataFrame(df_after_readabil) # Same as pd.concat(df_after_readabil, axis=1).T , but cleaner
	df_befor_readabil = pd.DataFrame(df_befor_readabil)
	df_diffs_readabil = pd.DataFrame(df_diffs_readabil)
	# HERE IT IS NOT THE SAME TO DO diffs = after - before , because some metrics may be N/A for before or after
	# Example: before:(1.1,2.1,3), After:(1.0,2.0,NA)
	# Then Mean of diffs = 0.1 = correct. BUT Diff of means = 0.6 !!
	
	print('ok step 1 readability commits')

	# do the same with nonread commits
	df_after_nonread = []
	df_befor_nonread = []
	df_diffs_nonread = []
	for commit in nonread_commits:
		
		aftbfrdif = loadFindMeansOfCommit(commit)
		
		if aftbfrdif is not None:
			df_after_nonread.append(aftbfrdif[0])
			df_befor_nonread.append(aftbfrdif[1])
			df_diffs_nonread.append(aftbfrdif[2])

	df_after_nonread = pd.DataFrame(df_after_nonread)
	df_befor_nonread = pd.DataFrame(df_befor_nonread)
	df_diffs_nonread = pd.DataFrame(df_diffs_nonread)
	print('ok step 1 nonread commits')
	
	return df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread



try:
	df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread = joblib.load('Zdump_aftbefdif_readabilnonread')
	print('loaded from dump')
except:
	df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread = read_from_csvs()
	joblib.dump((df_after_readabil,df_befor_readabil,df_diffs_readabil,
		df_after_nonread,df_befor_nonread,df_diffs_nonread), 'Zdump_aftbefdif_readabilnonread')
	print('read the csv files and saved to a dump file')



# D the analysis

# Cohen's and Cliff's delta between df_after_nonread, df_befor_nonread
# Also for df_after_readabil, df_befor_readabil
# Q1
common_for_analysis.runQ1('percommit', df_after_readabil,
	df_befor_readabil, df_after_nonread, df_befor_nonread)

# Q2
# between readability and non-readabil commits: df_diffs_readabil, df_diffs_nonread
common_for_analysis.runQ2('percommit', df_diffs_readabil, df_diffs_nonread)

print("analysis per-commit finished")

