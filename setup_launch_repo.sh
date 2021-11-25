#!/usr/bin/bash

#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=32G
#SBATCH --exclusive # Necessary to start multiple steps with srun, and run parallel
#TODO find best slurm options

# maybe these paths & consts should be defined outside, as "env"
# Also, ensure that the directories exist
export SCRIPTS_DIR=$(readlink -f "$0" | xargs --null dirname) # location of current script
# xargs --null ensures that spaces are not considered arg seperator
# TODO METRICS_DIR="$(dirname $SCRIPTS_DIR)/metrics" # later we add /$repo_name
METRICS_DIR="$SCRIPTS_DIR/metrics" # later we add /$repo_name
readarray -t KEYWORDS < "$SCRIPTS_DIR/keywords_for_commits.txt"
# -t discards trailing newlines. Important for git log --grep

echo "Curr dir = $(pwd)"

# Store the repo to be analysed in this folder. This can be in RAM (like tmpfs) for faster
if [ -z "$FILES_DIR" ] ; then
	rundir_avail=$(df --output=avail "$XDG_RUNTIME_DIR/" | tail -n1)
	tmpdir_avail=$(df --output=avail /tmp/ | tail -n1)
	
	if [ $rundir_avail -gt 3000000 -a -w "$XDG_RUNTIME_DIR/" ] ; then # min 3 GB free, and writable
		FILES_DIR="$XDG_RUNTIME_DIR/readabl_dipl"
	elif [ $tmpdir_avail -gt 3000000 -a -w /tmp/ ] ; then
		FILES_DIR=/tmp/readabl_dipl
	else
		FILES_DIR="$SCRIPTS_DIR"
	fi
	
	echo "Using FILES_DIR = $FILES_DIR"
	echo "If you want a different one, set the env variable FILES_DIR"
fi

if [ ! -d "$FILES_DIR" ] ; then
	mkdir -p "$FILES_DIR"
fi

module load gcc/9.2 python/3.7 # for hpc


# Handler for sigint, sigterm. To kill any children.
function exit_handler () {
	echo 'Received exit signal'
	for child_pid in "${children[@]}" ; do
		kill -kill -$child_pid # - before the pid, so that we also kill their subprocesses
	done
	
	mv "$FILES_DIR/$repo_name-01" "$FILES_DIR/$repo_name"
	exit 0
}
children=()
trap exit_handler INT
trap exit_handler TERM


if [ -z "$1" -o "$1" == "--help" -o "$1" == "-h" ] ; then
	echo "Usage: $0 ghuser/ghrepo [parallel=4]"
	echo "No argument for the repository given. Exiting"
	exit 1
fi

repo_full=$1
repo_name=$(echo $1 | cut -d '/' -f2) # get the part after the slash. Eg: elastic/elasticsearch
export METRICS_DIR="$METRICS_DIR/$repo_name"

parallel="${2:-4}"
# In how many parts to split the commits. Is the 2nd argument. Default = 4.

[ "$parallel" -eq "$parallel" -a "$parallel" -gt 0 ] 2> /dev/null # Check if it is a positive int
if [[ $? != 0 ]] ; then
	echo "Error: The 2nd argument (parallel) must be a positive integer. Exiting"
	exit 1
fi


if [ -d "$FILES_DIR/$repo_name" ] ; then # if the directory already exists
	echo "Warning: the directory $FILES_DIR/$repo_name already exists. Continuing with it.."
	
elif [ -d "$repo_name" ] ; then
	echo "The directory $repo_name already exists. Copying it to FILES_DIR.."
	cp -r "$repo_name" "$FILES_DIR/$repo_name"
	
else # Clone it grom github
	echo "Cloning from github..."
	git clone "https://github.com/${repo_full}.git" "$FILES_DIR/$repo_name"
	
	if [[ $? != 0 ]] ; then
		echo 'Encountered problem at git clone. Exiting..';
		exit 1
	fi
fi

cd "$FILES_DIR/$repo_name"


## find radability commits

rm -f readability_commits_repeated.txt # Because we will append to it.

git checkout -f master # we may be detached, not at the main branch.

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

cat readability_commits_unique.txt nonread_commits.txt | cut -c1-10 | sort > all_commits.txt # just keep 10 chars of the hash

if [ ! -z "$EXCLUDE_COMMITS" ] ; then
	if [ ! -f "$EXCLUDE_COMMITS" ] ; then
		echo "Error: file EXCLUDE_COMMITS does not exist ($EXCLUDE_COMMITS)"
		exit 1
	fi
	
	sort "$EXCLUDE_COMMITS" | comm -13 - all_commits.txt > commits_filtered.txt
	mv commits_filtered.txt all_commits.txt
fi

num_all_commits=$(wc --lines < all_commits.txt)


## Handle the parallelizing

commits_per_node=$(( num_all_commits / parallel + 1 ))

if [ $commits_per_node -lt 5 ] ; then # Don't use <. This compares lexicographically
	echo "Warning: Would be <5 commits per node. Not worth to parallelize"
	
	parallel=1
fi

split --numeric-suffixes=1 --suffix-length=2 --number=r/$parallel all_commits.txt commits
# split to $parallel files commits01, commits02... "commits" is the prefix
# "r/" = do not break lines and use round-robin. "-" is to read from stdin


# Make copies of the folder and move the commits lists

cd .. # now we are at $FILES_DIR
for i in $(seq 2 "$parallel" | xargs printf "%02d ") ; do # 02 03 04 ...
	
	if [ "$i" = '00' ] ; then # if seq is empty, printf without args would print 00. Don't want that
		break
	fi
	
	cp -r "$repo_name" "$repo_name-$i"
	mv "$repo_name/commits$i" "$repo_name-$i/"
done
mv "$repo_name" "$repo_name-01"

echo 'ready to launch calc_metrics_repo. Proceed?'
read
if [ "$REPLY" = 'n' -o "$REPLY" = 'no' ] ; then
	exit 0
fi

date -Iseconds

# Call calc_metrics_repo
for i in $(seq "$parallel" | xargs printf "%02d ") ; do
	cd "$repo_name-$i"

	echo "starting $i"
	
	"$SCRIPTS_DIR/calc_metrics_repo.sh" "commits$i" & #TODO this is basic
	# srun --ntasks=1 "$SCRIPTS_DIR/calc_metrics_repo.sh" "commits$i" &
	echo "($i) pid: $!"
	children+=($!) # add pid to list of children in case of sigterm
	
	cd ..
done

wait # for all started processes

echo "all done"
date -Iseconds

