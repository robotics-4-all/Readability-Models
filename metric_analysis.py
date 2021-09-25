
# This is a work in progress

import csv

"""

for each commit

	for each metric:
		find out whether it:
		  - showed no significant change in all files
		  - increased or unchanged in all files (by how much?)
		  - decreased or unchanged in all files (how much?)
		  - increased in some files, decreased in others. (Can we determine which is greater? Increase or decrease? How to choose? Num of lines changed per file? Total SLOC per file? For now maybe just categorise in these 4, and don''t determine which is greater)




for each metric:
	
a) either:

	determine if it increases in most readability commits, or decreases, or is unchanged, or changes both ways
	(Then ask, is this expected?)
	
	determine the same for non-readability commits.
	(Then ask, is this expected?)

	Does it changes in the same way?
"""

def ensure_same_order(a, b, key_name):
	
	try:
		for i in range(len(metrics_befor)):
			if a[i][key_name] != b[i][key_name]:
				raise Exception('Not sorted', i}

		return True

	except Exception:
		a.sort(key=lambda item: item[key_name])
		b.sort(key=lambda item: item[key_name])
		#TODO check that the original lists will be sorted too.



#readab_commits = read readability_commits_unique.txt

with open('readability_commits_unique.txt', 'r') as reader:
	readab_commits = [ line[0:40] for line in reader ]

# load nonread_commits
with open('nonread_commits.txt', 'r') as reader:
	nonread_commits = [ line[0:40] for line in reader ]

# TODO load metrics. Must be the same as in csv headers


metrics_statistics = {}


for commit in readab_commits:
	
	short_hash = commit[0:10]
	
	with open(short_hash + '_befor.csv', 'r') as reader:
	
		csv_befor = csv.DictReader(reader)
		metrics_befor = list(csv_befor) # [ row for row in csv_befor]
	
	with open(short_hash + '_after.csv', 'r') as reader:
	
		csv_after = csv.DictReader(reader)
		metrics_after = list(csv_after) # [ row for row in csv_after]
	
	
	ensure_same_order(metrics_befor, metrics_after, 'file')
	# TODO check if files in same order. Could we correct the order?
	
	commit_delta_metr_mean = {}
	commit_delta_metr_weighted = {}
	commit_delta_metr_variance = {}
	
	for metric in metrics:
	
		simple_sum = 0
		weight_sum = 0
		tot_lines = 0 # or tot_delta_lines
		sum_squares = 0 # to find the variance of the difference
		
		# for file in files_changed
		for i in range(len(metrics_befor)):
			
			diffs[metric][i] = metrics_after[i][metric] - metrics_befor[i][metric]
			rel_dif[metric][i] = diffs[metric][i] / (metrics_after[i][metric] + metrics_befor[i][metric]) * 2
			
			simple_sum += diffs[metric][i] # or rel_dif ?
			weight_sum += diffs[metric][i] * tot_lines[ metrics_befor[i]['file'] ]
			# TODO find tot_lines or delta_lines, for all files for one commit
			tot_lines += tot_lines[ metrics_befor[i]['file'] ]
			sum_squares += diffs[metric][i] ** 2
		
		sum_squares /= len(metrics_befor)
		
		commit_delta_metr_mean[metric] = simple_sum / len(metrics_befor)
		commit_delta_metr_weighted[metric] = weight_sum / tot_lines
		commit_delta_metr_variance[metric] = sum_squares - commit_delta_metr_mean[metric] ** 2
		# Var(x) = E(X^2) - E(X)^2

	# TODO store in a table for all commits



