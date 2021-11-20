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

	# Doing -projectBaseDir=. makes it extremely slow at step DirectoryBasedAnalysisTask
	# and it may even run out of ram... Copy only needed files to seperate dir
	mkdir -p filesForEval
	rm -rf filesForEval/* # remove all old files
	
	cp --parents -t filesForEval/ "${files_changed[@]}" # keep the dir structure
	
	#rm -rf "$SMA_RES_DIR/$1" # No need, because we mv Class.csv and Method.csv, so they won;t exist
	
	echo -n "Running SourceMeter for $short_hash - $1 ... "
	
	# SourceMeter needs Java v1.11
	# Instead of update-java-alternatives, we set the PATH for java v11 (because we are not root)
	# Also chdir, so that it only runs for the changed files
	cd filesForEval # hpc doesn't support env --chdir
	env PATH="$JAVA11DIR" "$SCRIPTS_DIR/sma-9/SourceMeterJava" -resultsDir=$SMA_RES_DIR \
		-projectName=$1 -projectBaseDir=. -maximumThreads=10 \
		-runFB=false -runPMD=false -runAndroidHunter=false -runMetricHunter=false \
		-runVulnerabilityHunter=false -runFaultHunter=false -runRTEHunter=false \
		-runDCF=true -runMET=true "${files_changed[@]}" # > /dev/null
	# We just want it to calc metrics and duplication check: runMET and runDCF
	cd ..
	
	sma_return=$? # The return code would be lost by the echo
	if [[ $sma_return == 0 ]] ; then
		echo " ok"
	else
		echo " sth went wrong"
	fi
	return "$sma_return"
}


function files_calc_metr () {

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
	
	# Calculate various metrics for file before/after commit. Store results
	python3 "$SCRIPTS_DIR/calc_metrics_file.py" "${files_changed[@]}" > "$METRICS_DIR/${short_hash}_${1}.csv"
	# one line per file. Filename is the first field, column names in the first row
}


if [ ! -f readability.classifier ] ; then
	ln -s "$SCRIPTS_DIR/models/readability.classifier" .
	# Symbolic link. Needed for Scalabrino's jar. Don't make if it exists
fi

# Because of parallel running, they would try to write to the same folder, samw timestamp
SMA_RES_DIR=$(mktemp --tmpdir -d SMAresults.XXX)
echo "SMA results dir = $SMA_RES_DIR (for $1)"

#-----------------
#for each commit: (from x eg.50 readability commits, and 2*x random other commits for comparison)


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
	
	
	runSMA after # run SourceMeter with minimal options
	# Since they depend on the changed files, they should probably NOT run in parallel
	
	sma_returncode=$?
	
	# keep only -Class.csv. * is for the timestamp
	mv $SMA_RES_DIR/after/java/*/after-Class.csv "$METRICS_DIR/${short_hash}_smaCl_after.csv"
	mv $SMA_RES_DIR/after/java/*/after-Method.csv "$METRICS_DIR/${short_hash}_smaMe_after.csv"
	
	files_calc_metr after
	
	#--------------------
	git checkout -f HEAD^ # Go to before commit
	
	
	if [[ $sma_returncode == 0 ]] ; then # Only run SMA for befor if the previous run was successful (0)
		runSMA befor
		
		mv $SMA_RES_DIR/befor/java/*/befor-Class.csv "$METRICS_DIR/${short_hash}_smaCl_befor.csv"
		mv $SMA_RES_DIR/befor/java/*/befor-Method.csv "$METRICS_DIR/${short_hash}_smaMe_befor.csv"
	fi
	
	files_calc_metr befor
	
done

rm -rf "$SMA_RES_DIR"
rm -rf filesForEval

