#!/usr/bin/bash

repo_name=$(basename "$1") # after the last /


#export SCRIPTS_DIR="/mnt/scratch_b/users/a/anestisv/diplom"
export SCRIPTS_DIR="/mnt/Files/tHMMY/Diploma/Readability-Models"
export METRICS_DIR="$SCRIPTS_DIR/targets/$repo_name"

FILES_DIR="$XDG_RUNTIME_DIR/readabl_dipl"

#commits_list_folder="/mnt/scratch_b/users/a/anestisv/diplom/list-of-commits/$repo_name"
commits_list_folder="/home/anestis/diploma_tmp/list-of-commits/$repo_name"

mkdir -p "$METRICS_DIR" "$FILES_DIR"

if [ -d "$FILES_DIR/$repo_name" ] ; then
    echo "$FILES_DIR/$repo_name aldready exists. Using that."
else
	echo "Cloning from github..."
	git clone "https://github.com/${1}.git" "$FILES_DIR/$repo_name"
	if [[ $? != 0 ]] ; then
		echo 'Encountered problem at git clone. Exiting..';
		exit 1
	fi
fi
cd "$FILES_DIR/$repo_name"

date -Iseconds
echo "Number of commits:"
wc -l "$commits_list_folder/q0_readab_com_messages.txt" "$commits_list_folder/nonread_nonempty.txt"

#module load gcc/9.2 python/3.7 # for hpc

SMA_RES_DIR=$(mktemp --tmpdir -d SMAresults.XXX)
echo "SMA results dir = $SMA_RES_DIR (for $1)"

read -p "Press enter to proceed" -t 30

function runSMA () {

	# Doing -projectBaseDir=. makes it extremely slow at step DirectoryBasedAnalysisTask
	# and it may even run out of ram... Copy only needed files to seperate dir
	mkdir -p filesForEval
	rm -rf filesForEval/* # remove all old files
	
	cp --parents -t filesForEval/ "${files_changed[@]}" # keep the dir structure
	
	rm -rf "$SMA_RES_DIR/$1" # We must rm, because we don't mv PMD.txt
	
	echo -n "Running SourceMeter for $commit - $1 ... "
	
	# SourceMeter needs Java v1.11
	# Instead of update-java-alternatives, we set the PATH for java v11 (because we are not root)
	# Also chdir, so that it only runs for the changed files
	cd filesForEval # hpc doesn't support env --chdir
	#env PATH="$JAVA11DIR" 
	"$SCRIPTS_DIR/sma-8.2/SourceMeterJava" -resultsDir=$SMA_RES_DIR \
		-projectName=$1 -projectBaseDir=. -maximumThreads=10 \
		-runFB=false -runDCF=false -runAndroidHunter=false -runMetricHunter=false \
		-runVulnerabilityHunter=false -runFaultHunter=false -runRTEHunter=false \
		-runPMD=true -runMET=true "${files_changed[@]}" > /dev/null
	# We just want it to calc PMD violations
	# Must be SMA v8.2
	
	sma_return=$? # The return code would be lost
	cd ..
	
	if [[ $sma_return == 0 ]] ; then
		echo " ok"
	else
		echo " sth went wrong"
	fi
	return "$sma_return"
}


for commit in $(cat "$commits_list_folder/q0_readab_com_messages.txt" "$commits_list_folder/nonread_nonempty.txt"); do
	
	git checkout -f $commit # -f = force, overwrite files. TODO maybe do --no-overlay. Also check if there is option to hide detached head msg
	
	# find list of files changed and num of lines changed
	git diff --numstat --diff-filter=M HEAD^ | cut -f3 |
		grep '\.java$' > "files_changed.txt"
	
	# We only want files which exist before and after the commit. So no added/deleted.
	# The option --diff-filter=M keeps only modified files.
	# The 3rd column has the filenames. Only include .java files
	
	readarray -t files_changed < "files_changed.txt"
	# use a bash indexed array, so that we can send each file as exactly one argument to java, python, etc
	
	num_files="${#files_changed[@]}"
	if [ $num_files -eq 0 ] ; then # If no files changed, don't run anything
		echo "Commit $commit has no files to check"
		continue
	fi
	if [ $num_files -gt 80 ] ; then # Way too many. Could be irrelevant. Will be slow. Skip
		echo "Commit $commit has too many files to check ($num_files)"
		continue
	fi
	
	
	runSMA after # run SourceMeter with minimal options
	# Since they depend on the changed files, they should probably NOT run in parallel
	sma_returncode=$?
	
	git checkout -f HEAD^ # Go to before commit
	
	if [[ $sma_returncode == 0 ]] ; then # Only run SMA for befor if the previous run was successful (0)
		runSMA befor
		
		python3 "$SCRIPTS_DIR/target_formulation.py" $SMA_RES_DIR/befor/java/*/befor-PMD.txt $SMA_RES_DIR/after/java/*/after-PMD.txt $commit
	fi
done


date -Iseconds
echo "Finished with repo $1 !"
read -p "Press enter to proceed" -t 60
cd ..
rm -rfv "$FILES_DIR/$repo_name" "$SMA_RES_DIR"

