#!/bin/bash

export SCRIPTS_DIR
export METRICS_DIR
# As inherithed

JAVA11DIR='/mnt/scratch_b/users/a/anestisv/diplom/java11/usr/lib/jvm/java-11-openjdk-11.0.13.0.8-1.el7_9.x86_64/bin/'


if [ -z "$1" -o ! -f "$1" ] ; then # Check the first argument
	echo "Error: argument not given or file not exists!"
	echo "Usage: $0 commits_list_file"
	exit 1
fi

commits_file="$1"

echo "calc_metrics_repo called with $1"


if [ ! -d "$METRICS_DIR" ] ; then
	mkdir -p "$METRICS_DIR"
fi
# TODO if exists? Should we move it?
#Or maybe no need because all files get overwritten

function runSMA () {

	common_path=$(python3 -c \
		"import sys,os.path; print(os.path.commonpath(sys.argv[1:]))" "${files_changed[@]}")
	# Doing -projectBaseDir=. makes it extremely slow at step DirectoryBasedAnalysisTask
	# and it may even run out of ram...
	
	if [ -z "$common_path" ] ; then # If it's empty, no common subpath
		common_path="."
	fi
	
	echo -n "Running SourceMeter for $short_hash - $1 ... "
	
	# Instead of update-java-alternatives,
	# This is if we are not root and cannot change java alternatives
	
	env PATH="$JAVA11DIR" "$SCRIPTS_DIR/sma-9/SourceMeterJava" -resultsDir=/tmp/SMAresults \
		-projectName=$1 -projectBaseDir=$common_path \
		-runFB=false -runPMD=false -runAndroidHunter=false -runMetricHunter=false \
		-runVulnerabilityHunter=false -runFaultHunter=false -runRTEHunter=false \
		-runDCF=true -runMET=true "${files_changed[@]}" # > /dev/null
	# We just want it to calc metrics and duplication check: runMET and runDCF
	
	sma_return=$? # The return code would be lost by the echo
	if [[ $sma_return == 0 ]] ; then
		echo " ok"
	else
		echo " sth went wrong"
	fi
	return "$sma_return"
}


function loop_files_calc_metr () {

	# use the result of SourceMeter for (before/after) this commit
	cp "$METRICS_DIR/${short_hash}_smaCl_${1}.csv" "$METRICS_DIR/curr_sma_class.csv"
	cp "$METRICS_DIR/${short_hash}_smaMe_${1}.csv" "$METRICS_DIR/curr_sma_methd.csv"
	
	# Run Scalabrino once for all files: faster.
	# 10 calls of 1 files : 21 seconds. 1 call of 10 files : 3 seconds. 7x speedup
	java -jar "$SCRIPTS_DIR/models/rsm.jar" "${files_changed[@]}" |
		tail --lines=+3 > scalabrino_tmp.txt
	# tail discards the first 2 lines.
	# The jar needs readability.classifier in the current path (pwd). Is symlinked in calc_metrics_repo.sh
	# The output file will not stay, it will be written over, no problem. It is used just below.
	
	for file in "${files_changed[@]}" ; do
		# Calculate various metrics for file before/after commit. Store results
		
		python3 "$SCRIPTS_DIR/calc_metrics_file.py" $file >> "$METRICS_DIR/${short_hash}_${1}.csv"
		# one line per file. Filename can be the first field
	done
}


if [ ! -f readability.classifier ] ; then
	ln -s "$SCRIPTS_DIR/models/readability.classifier" .
	# Symbolic link. Needed for Scalabrino's jar. Don't make if it exists
fi

#-----------------
#for each commit: (from x eg.50 readability commits, and 2*x random other commits for comparison)



# SourceMeter needs Java v1.11
# No need for 2 loops! Since we don't change Java versions with update, just git-checkout once!
for commit in $(cat "$commits_file"); do

	short_hash=$(echo $commit | cut -c1-10)
	
	git checkout -f $commit # -f = force, overwrite files. TODO maybe do --no-overlay. Also check if there is option to hide detached head msg
	
	# find list of files changed and num of lines changed
	git diff --numstat --diff-filter=M HEAD^ | cut -f3 |
		grep '\.java$' > "$METRICS_DIR/${short_hash}_files.txt"
	
	# We only want files which exist before and after the commit. So no added/deleted.
	# The option --diff-filter=M keeps only modified files.
	# The 3rd column has the filenames. Only include .java files
	
	readarray -t files_changed < "$METRICS_DIR/${short_hash}_files.txt"
	# use a bash indexed array, so that we can send each file as exactly one argument to java, python, etc
	
	num_files="${#files_changed[@]}"
	if [ $num_files -eq 0 ] ; then # If no files changed, don't run anything
		echo "Commit $short_hash has no files to check"
		continue
	fi
	if [ $num_files -gt 80 ] ; then # Way too many. Could be irrelevant. Will be slow. Skip
		echo "Commit $short_hash has too many files to check ($num_files)"
		continue
	fi
	
	# setup CSV files and their headers
	python3 "$SCRIPTS_DIR/calc_metrics_file.py" --setup > "$METRICS_DIR/${short_hash}_after.csv"
	cp "$METRICS_DIR/${short_hash}_after.csv" "$METRICS_DIR/${short_hash}_befor.csv"
	
	
	runSMA after # run SourceMeter with minimal options
	# Since they depend on the changed files, they should probably NOT run in parallel
	
	sma_returncode=$?
	
	# keep only -Class.csv. * is for the timestamp
	mv $SMA_RES_DIR/after/java/*/after-Class.csv "$METRICS_DIR/${short_hash}_smaCl_after.csv"
	mv $SMA_RES_DIR/after/java/*/after-Method.csv "$METRICS_DIR/${short_hash}_smaMe_after.csv"
	
	loop_files_calc_metr after
	
	#--------------------
	git checkout -f HEAD^ # Go to before commit
	
	
	if [[ $sma_returncode == 0 ]] ; then # Only run SMA for befor if the previous run was successful (0)
		runSMA befor
		
		mv $SMA_RES_DIR/befor/java/*/befor-Class.csv "$METRICS_DIR/${short_hash}_smaCl_befor.csv"
		mv $SMA_RES_DIR/befor/java/*/befor-Method.csv "$METRICS_DIR/${short_hash}_smaMe_befor.csv"
	fi
	
	loop_files_calc_metr befor
	
done

rm -rf /tmp/SMAresults/

