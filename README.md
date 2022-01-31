# Readability-Models
GitHub repository for thesis "Αξιολόγηση Μοντέλων Αναγνωσιμότητας Έργων Λογισμικού και Εξαγωγή Χρήσιμων Χαρακτηριστικών"

## How to run the software

### Metric generation
Prerequisites:
* A GNU/Linux type system, with utilities such as cat, cut, grep, ln, rm, etc.
* Git >= 1.8.3
* Bash >= 4.2
* Java 11, which should be at the directory `JAVA11DIR` from calc\_metrics\_repo.sh
* Java 1.8, which should be the default for the command `java`
* Python >= 3.7, with the libraries numpy, pandas, and joblib
* SourceMeter Analyzer 9.2 for Linux

The script setup\_launch\_repo.sh finds the reabability commits and some non-readability commits of a repo, and calculates the values of metrics and readability models on the changed files.
To execute the script, run
```
./setup_launch_repo.sh repo_owner/repo_name [parallel]
```
`repo_owner/repo_name` is the name of the repository in GitHub
`parallel` is an optional argument for the number of parallel instances of calc\_metrics\_repo.sh to launch (default=4)

Some key directories (folders):
* `SCRIPTS_DIR`: Where setup\_launch\_repo.sh is located
* `METRICS_DIR`: Contains the output: the csv files with all the metrics. Is at `SCRIPTS_DIR/metrics/repo_name`
* `FILES_DIR`: Contains the code of the repository to be examined. If not provided, it is chosen automatically.

### Metric analysis
Prerequisites:
* Python >= 3.7, with the libraries numpy, pandas, joblib, scipy.stats, and [cliffs_delta](https://github.com/neilernst/cliffsDelta)

Before running the analysis, the current working directory (say `SCRIPTS_DIR/metrics/all`) must contain:
* the csv files for all the desired commits, before and after
* a file called `all_true_readabil_commits.txt` with the hashes of all the true readability commits, seperated by newline
* a file called `all_nonread_commits.txt` with the hashes of all the non-readability commits, seperated by newline

To execute the scripts, run
```
python3 analysis_metrics_percommit.py
python3 analysis_metrics_perfile.py
```

The scripts will generate 4 output files: results\_Q1\_percommit.csv, results\_Q1\_perfile.csv, results\_Q2\_percommit.csv, and results\_Q2\_perfile.csv .

## Copyright
Some rights reserved, Anestis Varsamidis, 2021-2022

Thw code is licensed under the GNU GPL version 3. This does not cover the external material which is located in models/

