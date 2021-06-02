


SCRIPTS_DIR=..... #TODO
METRICS_DIR=..... #TODO

# TODO cd to project's git directory. First clone it.


# find radability commits

for keyword in $keywords ; do

	git log --all --grep="$keyword" --pretty=oneline >> readability_commits_repeated.txt
	# all means search commits from all branches
done

sort -u readability_commits_repeated.txt > readability_commits_unique.txt
# keep only uniques

cut --fields=1 --delimiter=' ' readability_commits_unique.txt
# keep only first column (commit hash)

echo "Found $(wc --lines < readability_commits_unique.txt) readability commits!"

# TODO maybe find some random non-readability commits

#-----------------
#for each commit: (maybe select x eg.400 readability commits, and 4*x random other commits for comparison)

for commit in $(cat readability_commits_unique.txt nonread_commits.txt)

	short_hash=$(echo $commit | cut -c10)
	
	# setup CSV files and their headers
	SCRIPTS_DIR/calc_metrics_file.py --setup > $RESULTS_DIR/${short_hash}_after.csv
	cp $RESULTS_DIR/${short_hash}_after.csv $RESULTS_DIR/${short_hash}_befor.csv
	
	# checkout to after commit
	git checkout $commit
	
	# find list of files changed and num of lines changed
	git diff --numstat HEAD^ > numstat.txt
	
	files_changed=$(cut -f3 numstat.txt) # the 3rd column has the filenames
	
	for file in $files_changed ; do
	
		# Calculate various metrics for file after commit. Store results
		
		$SCRIPTS_DIR/calc_metrics_file.py $file >> $RESULTS_DIR/${short_hash}_after.csv
		
		# one line per file. Filename can be the first field
	done
	
	
	git checkout HEAD^ # to before commit
	
	for file in $files_changed ; do
		# Calculate various metrics for file before commit. Store results
		
		$SCRIPTS_DIR/calc_metrics_file.py $file >> $RESULTS_DIR/${short_hash}_befor.csv
	done
	
	
	#TODO in a python script:
	for each metric:
		find out whether it:
		  - showed no significant change in all files
		  - increased or unchanged in all files (by how much?)
		  - decreased or unchanged in all files (how much?)
		  - increased in some files, decreased in others. (Can we determine which is greater? Increase or decrease? How to choose? Num of lines changed per file? Total SLOC per file? For now maybe just categorise in these 4, and don''t determine which is greater)
	
	done

done

