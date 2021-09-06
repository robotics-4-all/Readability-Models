import subprocess
import re
import sys
import os
from math import exp, fsum


if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
	print("Error. File not given or not exists")
	sys.exit(1)

filename = sys.argv[1]
filename = "/home/anestis/Επιφάνεια εργασίας/tmp_diplom/testfile2.java"
#TODO remove

### Many metrics, Posnett, and Dorn

raw = subprocess.check_output(['java', '-cp', 'rsm.jar',
	'it.unimol.readability.metric.runnable.ExtractMetrics', filename]).decode("utf-8")

#comma_metrics = re.sub(r"^.+: (.{3,})\n", "\\1,", raw, 0, re.MULTILINE)

metrics = re.findall(r"^.+: (.{3,})$", raw, re.MULTILINE)
# The above is a str list. Make it a float list
metrics = list(map(float, metrics))
#metrics = array.array('f', map(float, list_metrics)) # If we wanted float array


if len(metrics) != 110:
	print("Warning! There were not 110 metrics")


# POSNETT :		  Entropy			 Halstead V			Lines
tmp = 8.87 - 1.5*metrics[48] - 0.033*metrics[49] + 0.4*metrics[50]
posnett_score = 1/(1 + exp( -tmp))


tmp = 1 # TODO DORN MODEL
dorn_score = 1/(1 + exp( -tmp))



### Buse Weimer

command = "sed '0~8 s/$/\\n###/g' '{0}' | java -jar BW_readability.jar".format(filename)
raw = subprocess.check_output(command, shell=True).decode("utf-8")

snippet_scores_str = raw.split('\n\n')[1:-1]

# First, make them all floats. then add them and divide by the count
# to get the average BW score of all the snippets
bw_score = fsum(map(float, snippet_scores_str)) / len(snippet_scores_str)



### Scalabrino

raw = subprocess.check_output(['java', '-jar', 'rsm.jar', filename]).decode("utf-8")
# TODO maybe quite faster to give all the files together ??

scalabrino_score = float( raw.split('\t')[-1] )
# Gets the part after the last tab, and converts to float



### Final stuff. Append to csv

metrics.insert(0, filename) # After that, the indexes of the metrics
# have changed. Caution with any operations with metrics below
metrics.append(bw_score)
metrics.append(posnett_score)
metrics.append(dorn_score)
metrics.append(scalabrino_score)

csv_line = ','.join(map(str, metrics))

#TODO write it in a file named by the commit?


print(metrics)
print(csv_line)

