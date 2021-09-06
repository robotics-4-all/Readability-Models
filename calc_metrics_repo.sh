

# maybe these paths & consts should be defined outside, as "env"
# Also, ensure that the directories exist
SCRIPTS_DIR=$(pwd) #TODO
METRICS_DIR="$(pwd)/metrics" #TODO
KEYWORDS="readability readable" # TODO $(cat keywords.txt)


# TODO cd to project's git directory. First clone it.


# find radability commits

for keyword in $KEYWORDS ; do

	git log --all --grep="$keyword" --pretty=oneline --regexp-ignore-case >> readability_commits_repeated.txt
	# all means search commits from all branches
done

sort -u readability_commits_repeated.txt > readability_commits_unique.txt
# keep only uniques

#cut --fields=1 --delimiter=' ' readability_commits_unique.txt
# keep only first column (commit hash)

num_readab_commits=$(wc --lines < readability_commits_unique.txt)

echo "Found $num_readab_commits readability commits!"


# Find some random non-readability commits
# How many? 2x as many as the readability

git log --all -n200 --pretty=oneline |
	shuf --head-count=$((2*num_readab_commits)) > nonread_commits_unchecked.txt

# We have to remove any possible readability commits

sort nonread_commits_unchecked.txt | comm -13 readability_commits_unique.txt - > nonread_commits.txt

# comm -13 outputs only lines which are only in file 2. '-' means stdin

#TODO rm readability_commits_repeated.txt nonread_commits_unchecked.txt


#-----------------
#for each commit: (maybe select x eg.400 readability commits, and 4*x random other commits for comparison)

for commit in $(cut -f1 --delimiter=' ' readability_commits_unique.txt) $(cat nonread_commits.txt); do

	short_hash=$(echo $commit | cut -c1-10)
	
	# setup CSV files and their headers
	$SCRIPTS_DIR/calc_metrics_file.py --setup > $METRICS_DIR/${short_hash}_after.csv
	cp $METRICS_DIR/${short_hash}_after.csv $METRICS_DIR/${short_hash}_befor.csv
	
	# checkout to after commit
	git checkout $commit
	
	# find list of files changed and num of lines changed
	git diff --numstat --diff-filter=MR HEAD^ > $METRICS_DIR/${short_hash}_numstat.txt
	
	# We only want filees which exist before and after the commit. So no added/deleted.
	# The option --diff-filter=MR keeps only modified and renamed files.
	
	# TODO what if a line is renamed, like:
	# 17      2       calc_metrics_for_repo.sh => calc_metrics_repo.sh
	
	files_changed=$(cut -f3 $METRICS_DIR/${short_hash}_numstat.txt | grep '\.java$') # the 3rd column has the filenames
	# only include .java files (maybe shouldn't? TODO)
	#sed -E 's/.*\t.*\t(.*\.java)$/$1/;t;d' $METRICS_DIR/${short_hash}_numstat.txt
	#cut -f3 $METRICS_DIR/${short_hash}_numstat.txt | grep '\.java$'
	#grep --perl-regexp --only-matching '[^\t]+\.java$' $METRICS_DIR/${short_hash}_numstat.txt
	
	for file in $files_changed ; do
	
		# Calculate various metrics for file after commit. Store results
		
		$SCRIPTS_DIR/metric_generation.py $file >> $METRICS_DIR/${short_hash}_after.csv
		
		# one line per file. Filename can be the first field
	done
	
	
	git checkout HEAD^ # to before commit
	
	for file in $files_changed ; do
		# Calculate various metrics for file before commit. Store results
		
		$SCRIPTS_DIR/metric_generation.py $file >> $METRICS_DIR/${short_hash}_befor.csv
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

