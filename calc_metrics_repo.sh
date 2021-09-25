

# maybe these paths & consts should be defined outside, as "env"
# Also, ensure that the directories exist
SCRIPTS_DIR=$(pwd) #TODO
METRICS_DIR="$(pwd)/metrics" #TODO
readarray KEYWORDS < keywords_for_commits.txt


# TODO cd to project's git directory. First clone it.


# find radability commits

for keyword in "${KEYWORDS[@]}" ; do
# Must use this syntax in order to use it as an array. stackoverflow.com/a/16452606

	git log --all --grep="$keyword" --pretty=%H --regexp-ignore-case >> readability_commits_repeated.txt
	# --all means search commits from all branches
	# --pretty=%H means to only write the hashes. Otherwise need to use "cut -f1 --delimiter=' '"
done

sort -u readability_commits_repeated.txt > readability_commits_unique.txt
# keep only uniques


num_readab_commits=$(wc --lines < readability_commits_unique.txt)

echo "Found $num_readab_commits readability commits!"


# Find some random non-readability commits
# How many? 2x as many as the readability

git log --all -n200 --pretty=%H |
	shuf --head-count=$((2*num_readab_commits)) > nonread_commits_unchecked.txt

# We have to remove any possible readability commits

sort nonread_commits_unchecked.txt | comm -13 readability_commits_unique.txt - > nonread_commits.txt

# comm -13 outputs only lines which are only in file 2. '-' means stdin

#TODO rm readability_commits_repeated.txt nonread_commits_unchecked.txt


function runSMA () {
	$SCRIPTS_DIR/SourceMeterJava -resultsDir=/tmp/SMAresults -projectName=$1 -projectBaseDir=. \
		-runFB=false -runPMD=false -runAndroidHunter=false -runMetricHunter=false \
		-runVulnerabilityHunter=false -runFaultHunter=false -runRTEHunter=false \
		-runDCF=false -runMET=true $files_changed
		#TODO check if the command works
	
	# We just want it to calc metrics: runMET
	# projectBaseDir is the current, the base git dir.
	#TODO does this work? -projectBaseDir=.
}

#-----------------
#for each commit: (from x eg.50 readability commits, and 2*x random other commits for comparison)


sudo update-java-alternatives -s java-1.11.0-openjdk-amd64
# SourceMeter needs Java v1.11

for commit in $(cat readability_commits_unique.txt nonread_commits.txt); do

	short_hash=$(echo $commit | cut -c1-10)
	
	git checkout $commit
	
	# find list of files changed and num of lines changed
	git diff --numstat --diff-filter=M HEAD^ > $METRICS_DIR/${short_hash}_numstat.txt
	
	# We only want files which exist before and after the commit. So no added/deleted.
	# The option --diff-filter=M keeps only modified files.
	
	files_changed=$(cut -f3 $METRICS_DIR/${short_hash}_numstat.txt | grep '\.java$') # the 3rd column has the filenames
	# only include .java files (maybe shouldn't? TODO)
	#sed -E 's/.*\t.*\t(.*\.java)$/$1/;t;d' $METRICS_DIR/${short_hash}_numstat.txt
	#cut -f3 $METRICS_DIR/${short_hash}_numstat.txt | grep '\.java$'
	#grep --perl-regexp --only-matching '[^\t]+\.java$' $METRICS_DIR/${short_hash}_numstat.txt
	
	runSMA after & # run SourceMeter with minimal options
	# WITH " &" so that they run in parallel
	
	git checkout HEAD^ # to before commit
	
	runSMA befor
	
	wait # for the other run of SMA to finish
	
	# keep only -Class.csv. * is for the timestamp
	mv /tmp/SMAresults/after/java/*/after-Class.csv $METRICS_DIR/${short_hash}_sma_after.csv
	mv /tmp/SMAresults/befor/java/*/befor-Class.csv $METRICS_DIR/${short_hash}_sma_befor.csv
	
	rm -rf /tmp/SMAresults/
	
done


sudo update-java-alternatives -s java-1.14.0-openjdk-amd64
# The other jars need Java v1.14


for commit in $(cat readability_commits_unique.txt nonread_commits.txt); do

	short_hash=$(echo $commit | cut -c1-10)
	
	# setup CSV files and their headers
	$SCRIPTS_DIR/calc_metrics_file.py --setup > $METRICS_DIR/${short_hash}_after.csv
	cp $METRICS_DIR/${short_hash}_after.csv $METRICS_DIR/${short_hash}_befor.csv
	
	# checkout to after commit
	git checkout $commit
	
	# find list of files changed and num of lines changed. We did 'git numstat' above
	files_changed=$(cut -f3 $METRICS_DIR/${short_hash}_numstat.txt | grep '\.java$') # the 3rd column has the filenames
	# only include .java files (maybe shouldn't? TODO)
	#sed -E 's/.*\t.*\t(.*\.java)$/$1/;t;d' $METRICS_DIR/${short_hash}_numstat.txt
	#cut -f3 $METRICS_DIR/${short_hash}_numstat.txt | grep '\.java$'
	#grep --perl-regexp --only-matching '[^\t]+\.java$' $METRICS_DIR/${short_hash}_numstat.txt
	
	# use the result of SourceMeter for this commit
	cp $METRICS_DIR/${short_hash}_sma_after.csv $METRICS_DIR/curr_sma_result.csv
	
	for file in $files_changed ; do
	
		# Calculate various metrics for file after commit. Store results
		
		$SCRIPTS_DIR/metric_generation.py $file >> $METRICS_DIR/${short_hash}_after.csv
		
		# one line per file. Filename can be the first field
	done
	
	
	git checkout HEAD^ # to before commit
	
	# use the result of SourceMeter for (before) this commit
	cp $METRICS_DIR/${short_hash}_sma_befor.csv $METRICS_DIR/curr_sma_result.csv
	
	for file in $files_changed ; do
		# Calculate various metrics for file before commit. Store results
		
		$SCRIPTS_DIR/metric_generation.py $file >> $METRICS_DIR/${short_hash}_befor.csv
	done
	
	
done

