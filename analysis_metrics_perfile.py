
import pandas as pd
import joblib
import common_for_analysis


def read_from_csvs():
	with open('all_true_readabil_commits.txt', 'r') as reader:
		readab_commits = [ line[0:10] for line in reader ]

	# load nonread_commits
	with open('all_nonread_commits.txt', 'r') as reader:
		nonread_commits = [ line[0:10] for line in reader ]


	df_after_readabil = [] # MUST NOT do a = b = c = [], because they will refer to the same!!
	df_befor_readabil = []

	for commit in readab_commits:
		
		aftbfrdif = common_for_analysis.loadFilesOfCommit(commit)
		
		if aftbfrdif is not None:
			df_after_readabil.append(aftbfrdif[0])
			df_befor_readabil.append(aftbfrdif[1])
	
	df_after_readabil = pd.concat(df_after_readabil, axis=0, ignore_index=True)
	df_befor_readabil = pd.concat(df_befor_readabil, axis=0, ignore_index=True)
	
	df_diffs_readabil = df_after_readabil - df_befor_readabil #this is the same as
	#df_diffs_readabil = pd.concat(df_diffs_readabil, axis=0, ignore_index=True)
	
	print('ok step 1 readability commits')

	# do the same with nonread commits
	df_after_nonread = []
	df_befor_nonread = []
	
	for commit in nonread_commits:
		
		aftbfrdif = common_for_analysis.loadFilesOfCommit(commit)
		
		if aftbfrdif is not None:
			df_after_nonread.append(aftbfrdif[0])
			df_befor_nonread.append(aftbfrdif[1])

	df_after_nonread = pd.concat(df_after_nonread, axis=0, ignore_index=True)
	df_befor_nonread = pd.concat(df_befor_nonread, axis=0, ignore_index=True)
	df_diffs_nonread = df_after_nonread - df_befor_nonread
	print('ok step 1 nonread commits')
	
	return df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread



try:
	df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread = joblib.load('Zdump_byfiles_aftbefdif_readabilnonread')
	print('loaded from dump')
except:
	df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread = read_from_csvs()
	joblib.dump((df_after_readabil,df_befor_readabil,df_diffs_readabil,
		df_after_nonread,df_befor_nonread,df_diffs_nonread), 'Zdump_byfiles_aftbefdif_readabilnonread')
	print('read the csv files and saved to a dump file')



# D the analysis

# Cohen's and Cliff's delta between df_after_nonread, df_befor_nonread
# Also for df_after_readabil, df_befor_readabil
# Q1
common_for_analysis.runQ1('perfile', df_after_readabil,
	df_befor_readabil, df_after_nonread, df_befor_nonread)

# Q2
# between readability and non-readabil commits: df_diffs_readabil, df_diffs_nonread
common_for_analysis.runQ2('perfile', df_diffs_readabil, df_diffs_nonread)

print("analysis finished per-file")

