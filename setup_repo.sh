
#TODO add slurm options

# maybe these paths & consts should be defined outside, as "env"
# Also, ensure that the directories exist
export SCRIPTS_DIR=$(readlink -f "$0" | xargs --null dirname) # location of current script
# xargs --null ensures that spaces are not considered arg seperator
# TODO METRICS_DIR="$(dirname $SCRIPTS_DIR)/metrics" # later we add /$repo_name
METRICS_DIR="$SCRIPTS_DIR)/metrics" # later we add /$repo_name
readarray -t KEYWORDS < keywords_for_commits.txt
# -t discards trailing newlines. Important for git log --grep



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



if [ -d "$repo_name" ] ; then # if the directory already exists
	echo "Warning: the directory $repo_name already exists. Continuing with it.."
	
else # Clone it grom github
	
	git clone "https://github.com/${repo_full}.git" > /dev/null
	
	if [[ $? != 0 ]] ; then
		echo 'Encountered problem at git clone. Exiting..';
		exit 1
	fi
fi

cd "$repo_name"


## find radability commits

rm -f readability_commits_repeated.txt # Because we will append to it.

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

num_nonread_commits=$(wc --lines < nonread_commits.txt)

#TODO rm readability_commits_repeated.txt nonread_commits_unchecked.txt


## Handle the parallelizing

commits_per_node=$(( (num_readab_commits + num_nonread_commits) / parallel + 1 ))

if [[ $commits_per_node < 5 ]] ; then
	echo "Warning: Would be <5 commits per node. Not worth to parallelize"
	
	parallel=1
	commits_per_node=$(( num_readab_commits + num_nonread_commits ))
fi

cat calc_metrics_repo.sh nonread_commits.txt |
	split --numeric-suffixes=1 --suffix-length=2 --number=r/$parallel - commits
# split to $parallel files commits01, commits02... "commits" is the prefix
# "r/" = do not break lines and use round-robin. "-" is to read from stdin


# Make copies of the folder and move the commits lists

cd ..
for i in $(seq 2 "$parallel" | xargs printf "%02d ") ; do # 02 03 04 ...
	cp -r "$repo_name" "$repo_name-$i"
	mv "commits$i" "$repo_name-$i/"
done
mv "$repo_name" "$repo_name-01"
mv commits01 "$repo_name-01/"


# Call calc_metrics_repo
for i in $(seq "$parallel" | xargs printf "%02d ") ; do
	cd "$repo_name-$i"
	
	"$SCRIPTS_DIR/calc_metrics_repo.sh" "commits$i" & #TODO this is basic
	# srun --ntasks=1 "$SCRIPTS_DIR/calc_metrics_repo.sh" "commits$i" &
	
	cd ..
done

