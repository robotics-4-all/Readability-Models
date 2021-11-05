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


if [ ! -d "$METRICS_DIR" ] ; then
	mkdir -p "$METRICS_DIR"
fi

function runSMA () {

	common_path=$(python3 -c "import sys,os.path; print(os.path.commonpath(sys.argv[1:]))" $files_changed )
	# Doing -projectBaseDir=. makes it extremely slow at step DirectoryBasedAnalysisTask
	# and it may even run out of ram...
	
	if [ -z "$common_path" ] ; then # If it's empty, no common subpath
		common_path="."
	fi
	
	echo -n "Running SourceMeter for $short_hash - $1 ... "
	
	#TODO mhpws na kanoyme anti gia update-java-alternatives, etsi: ?
	#env PATH="$JAVA11_DIR" "$SCRIPTS_DIR/SourceMeterJava" -resultsDir=.....
	# me JAVA11_DIR="/usr/lib/jvm/java-11-openjdk-amd64/bin"
	# This is if we are not root and cannot change java alternatives
	
	env PATH="$JAVA11DIR" "$SCRIPTS_DIR/sma-9/SourceMeterJava" -resultsDir=/tmp/SMAresults \
		-projectName=$1 -projectBaseDir=$common_path \
		-runFB=false -runPMD=false -runAndroidHunter=false -runMetricHunter=false \
		-runVulnerabilityHunter=false -runFaultHunter=false -runRTEHunter=false \
		-runDCF=true -runMET=true $files_changed > /dev/null
	# We just want it to calc metrics and duplication check: runMET and runDCF
	
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


#sudo update-java-alternatives -s java-1.11.0-openjdk-amd64 2> /dev/null
# the redirection 2> is for "error: no alternatives for xyz"
# SourceMeter needs Java v1.11

for commit in $(cat "$commits_file"); do

	short_hash=$(echo $commit | cut -c1-10)
	
	git checkout -f $commit # -f = force, overwrite files.
	
	# find list of files changed and num of lines changed
	git diff --numstat --diff-filter=M HEAD^ | cut -f3 |
		grep '\.java$' > "$METRICS_DIR/${short_hash}_files.txt"
	
	# We only want files which exist before and after the commit. So no added/deleted.
	# The option --diff-filter=M keeps only modified files.
	# The 3rd column has the filenames. Only include .java files
	
	files_changed=$(cat "$METRICS_DIR/${short_hash}_files.txt")
	
	if [ -z "$files_changed" ] ; then # If no files changed, don't run anything
		continue
	fi
	
	runSMA after # run SourceMeter with minimal options
	# Since they depend on the changed files, they should probably NOT run in parallel
	
	if [[ $? != 0 ]] ; then # If SMA had a problem (nonzero return code) and did not produce output
		rm -rf /tmp/SMAresults/
		continue # don't run SMA again for before commit
	fi
	
	git checkout -f HEAD^ # Go to before commit
	
	runSMA befor
	
	
	# keep only -Class.csv. * is for the timestamp
	mv /tmp/SMAresults/after/java/*/after-Class.csv "$METRICS_DIR/${short_hash}_sma_after.csv"
	mv /tmp/SMAresults/befor/java/*/befor-Class.csv "$METRICS_DIR/${short_hash}_sma_befor.csv"
	
	rm -rf /tmp/SMAresults/
	
done


#sudo update-java-alternatives -s java-1.14.0-openjdk-amd64 2> /dev/null
# The other jars need Java v1.14 or v.1.8 ?!


function loop_files_calc_metr () {

	# use the result of SourceMeter for (before/after) this commit
	cp "$METRICS_DIR/${short_hash}_sma_${1}.csv" "$METRICS_DIR/curr_sma_result.csv"
	
	# Run Scalabrino once for all files: faster.
	# 10 calls of 1 files : 21 seconds. 1 call of 10 files : 3 seconds. 7x speedup
	java -jar "$SCRIPTS_DIR/models/rsm.jar" $files_changed |
		tail --lines=+3 > scalabrino_tmp.txt
	# tail discards the first 2 lines.
	# The jar needs readability.classifier in the current path (pwd). Is symlinked in calc_metrics_repo.sh
	# The output file will not stay, it will be written over, no problem. It is used just below.
	
	for file in $files_changed ; do
		# Calculate various metrics for file before/after commit. Store results
		
		python3 "$SCRIPTS_DIR/calc_metrics_file.py" $file >> "$METRICS_DIR/${short_hash}_${1}.csv"
		# one line per file. Filename can be the first field
	done
}


if [ ! -f readability.classifier ] ; then
	ln -s "$SCRIPTS_DIR/models/readability.classifier" .
	# Symbolic link. Needed for Scalabrino's jar. Don't make if it exists
fi

# TODO MERGE THE LOOPS! Since we don't change Java versions with update, just git-checkout once!
for commit in $(cat "$commits_file"); do

	short_hash=$(echo $commit | cut -c1-10)
	
	# setup CSV files and their headers
	python3 "$SCRIPTS_DIR/calc_metrics_file.py" --setup > "$METRICS_DIR/${short_hash}_after.csv"
	cp "$METRICS_DIR/${short_hash}_after.csv" "$METRICS_DIR/${short_hash}_befor.csv"
	
	# find list of files changed and num of lines changed. We did this above
	files_changed=$(cat "$METRICS_DIR/${short_hash}_files.txt")
	
	if [ -z "$files_changed" ] ; then # If no files changed, don't run anything
		echo "Commit $short_hash has no files to check"
		continue # before checkout to commit, which can take time
	fi
	
	echo -n "Checking $short_hash ... " # no trailing newline
	
	# checkout to after commit
	git checkout -f $commit
	
	loop_files_calc_metr after
	
	
	git checkout -f HEAD^ # Go to before commit
	
	loop_files_calc_metr befor
	
	echo " ok" # for this commit
done

