

# maybe these paths & consts should be defined outside, as "env"
# Also, ensure that the directories exist
export SCRIPTS_DIR=$(readlink -f "$0" | xargs --null dirname) # location of current script
# xargs --null ensures that spaces are not considered arg seperator
export METRICS_DIR="$SCRIPTS_DIR/metrics" #TODO
readarray -t KEYWORDS < keywords_for_commits.txt
# -t discards trailing newlines. Important for git log --grep


# TODO cd to project's git directory. First clone it.


# find radability commits

for keyword in "${KEYWORDS[@]}" ; do
# Must use this syntax in order to use it as an array. stackoverflow.com/a/16452606

	git log --grep="$keyword" --pretty=%H --regexp-ignore-case >> readability_commits_repeated.txt
	# --pretty=%H means to only write the hashes. Otherwise need to use "cut -f1 --delimiter=' '"
	# --all would search commits from all branches. Don't use --all, because some commits exist multiple times
	
done

sort -u readability_commits_repeated.txt > readability_commits_unique.txt
# keep only uniques


num_readab_commits=$(wc --lines < readability_commits_unique.txt)

echo "Found $num_readab_commits readability commits!"


# Find some random non-readability commits
# How many? 2x as many as the readability

git log -n200 --pretty=%H |
	shuf --head-count=$((2*num_readab_commits)) > nonread_commits_unchecked.txt

# We have to remove any possible readability commits

sort nonread_commits_unchecked.txt | comm -13 readability_commits_unique.txt - > nonread_commits.txt

# comm -13 outputs only lines which are only in file 2. '-' means stdin

#TODO rm readability_commits_repeated.txt nonread_commits_unchecked.txt


function runSMA () {

	common_path=$(python3 -c "import sys,os.path; print(os.path.commonpath(sys.argv[1:]))" $files_changed )
	# Doing -projectBaseDir=. makes it extremely slow at step DirectoryBasedAnalysisTask
	# and it may even run out of ram...
	
	if [ -z "$common_path" ] ; then # If it's empty, no common subpath
		common_path="."
	fi
	
	echo -n "Running SourceMeter for $short_hash - $1 ... "
	
	$SCRIPTS_DIR/SourceMeterJava -resultsDir=/tmp/SMAresults -projectName=$1 -projectBaseDir=$common_path \
		-runFB=false -runPMD=false -runAndroidHunter=false -runMetricHunter=false \
		-runVulnerabilityHunter=false -runFaultHunter=false -runRTEHunter=false \
		-runDCF=false -runMET=true $files_changed > /dev/null
	# We just want it to calc metrics: runMET
	
	sma_return=$? # The return code would be lost by the echo
	if [[ $sma_return == 0 ]] ; then
		echo " ok"
	else
		echo " sth went wrong"
	fi
	return "$sma_return"
}

#-----------------
#for each commit: (from x eg.50 readability commits, and 2*x random other commits for comparison)


sudo update-java-alternatives -s java-1.11.0-openjdk-amd64 2> /dev/null
# the redirection 2> is for "error: no alternatives for xyz"
# SourceMeter needs Java v1.11

for commit in $(cat readability_commits_unique.txt nonread_commits.txt); do

	short_hash=$(echo $commit | cut -c1-10)
	
	git checkout -q $commit # Quiet. Do not print stdout
	
	# find list of files changed and num of lines changed
	git diff --numstat --diff-filter=M HEAD^ | cut -f3 | grep '\.java$' > $METRICS_DIR/${short_hash}_files.txt
	
	# We only want files which exist before and after the commit. So no added/deleted.
	# The option --diff-filter=M keeps only modified files.
	# The 3rd column has the filenames. Only include .java files (maybe shouldn't? TODO)
	
	files_changed=$(cat $METRICS_DIR/${short_hash}_files.txt)
	
	if [ -z "$files_changed" ] ; then # If no files changed, don't run anything
		continue
	fi
	
	runSMA after # run SourceMeter with minimal options
	# Since they depend on the changed files, they should probably NOT run in parallel
	
	if [[ $? != 0 ]] ; then # If SMA had a problem (nonzero return code) and did not produce output
		rm -rf /tmp/SMAresults/
		continue # don't run SMA again for before commit
	fi
	
	git checkout -q HEAD^ # Go to before commit
	
	runSMA befor
	
	
	# keep only -Class.csv. * is for the timestamp
	mv /tmp/SMAresults/after/java/*/after-Class.csv $METRICS_DIR/${short_hash}_sma_after.csv
	mv /tmp/SMAresults/befor/java/*/befor-Class.csv $METRICS_DIR/${short_hash}_sma_befor.csv
	
	rm -rf /tmp/SMAresults/
	
done


sudo update-java-alternatives -s java-1.14.0-openjdk-amd64 2> /dev/null
# The other jars need Java v1.14


function loop_files_calc_metr () {

	# use the result of SourceMeter for (before/after) this commit
	cp $METRICS_DIR/${short_hash}_sma_${1}.csv $METRICS_DIR/curr_sma_result.csv
	
	#TODO maybe here call rsm.jar for all changed files
	
	for file in $files_changed ; do
		# Calculate various metrics for file before/after commit. Store results
		
		$SCRIPTS_DIR/metric_generation.py $file >> $METRICS_DIR/${short_hash}_${1}.csv
		# one line per file. Filename can be the first field
	done
}


ln -s $SCRIPTS_DIR/scalabrino/readability.classifier . #TODO move it to just $SCRIPTS_DIR/readability.classifier
# Symbolic link. Needed for Scalabrino's jar

for commit in $(cat readability_commits_unique.txt nonread_commits.txt); do

	short_hash=$(echo $commit | cut -c1-10)
	
	# setup CSV files and their headers
	$SCRIPTS_DIR/calc_metrics_file.py --setup > $METRICS_DIR/${short_hash}_after.csv
	cp $METRICS_DIR/${short_hash}_after.csv $METRICS_DIR/${short_hash}_befor.csv
	
	# find list of files changed and num of lines changed. We did this above
	files_changed=$(cat $METRICS_DIR/${short_hash}_files.txt)
	
	if [ -z "$files_changed" ] ; then # If no files changed, don't run anything
		echo "Commit $short_hash has no files to check"
		continue # before checkout to commit, which can take time
	fi
	
	echo -n "Checking $short_hash ... " # no trailing newline
	
	# checkout to after commit
	git checkout -q $commit # Quiet. Do not print stdout
	
	loop_files_calc_metr after
	
	
	git checkout -q HEAD^ # Go to before commit
	
	loop_files_calc_metr befor
	
	echo " ok" # for this commit
done

