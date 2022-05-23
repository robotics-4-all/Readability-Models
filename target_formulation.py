import pandas as pd
import sys, os

# SEE  SourceMeterResultsHandler
WEIGHTS = {"Minor": 2,  "Major": 4, "Critical": 16}


def getViolations(pmdFile):
	
	violationsInfo = {}
	violationsInfo["violations"] = {}
	violationsInfo["generalStats"] = {}
	
	sumViolations = {}
			
	with open(pmdFile, 'r') as violFile:
		for line in violFile:
			
			# Remove the absolute path
			line = line.split('/filesForEval/')[1].strip()
			
			# Get array containing the raw information
			line = line.split(":")
			
			violID = line[1].replace(" ", "")
			filePath = line[0].split("(")[0]
			# lineInFile = int(line[0].split("(")[1].replace(")", ""))
			
			eqcount = (violationsSpecs['RuleID'] == violID).sum()
			if eqcount != 1:
				print('Warning, eqcount != 1. ', eqcount, violID)
			
			category = violationsSpecs.loc[violationsSpecs['RuleID'] == violID]["RuleType"].iloc[0]
			severity = violationsSpecs.loc[violationsSpecs['RuleID'] == violID]["Severity"].iloc[0]
			
			if category in ["Performance", "Multithreading", "Security"]:
				continue # ignore these categories for target formulation
			
			if filePath in sumViolations:
				sumViolations[filePath] += WEIGHTS[severity]
			else:
				sumViolations[filePath] = WEIGHTS[severity]
	
	return pd.Series(sumViolations)


def targetFormulation(pmdFile):
	
	sumViolations = getViolations(pmdFile)
	
	metricsFile = pmdFile[0:-7] + 'File.csv'
	metrics = pd.read_csv(metricsFile)
	metrics.index = [ abspath.split('/filesForEval/')[1] for abspath in metrics.LongName ]
	
	target_score = sumViolations / metrics.LLOC
	target_score = target_score.fillna(0) # if sumViolations does not include a file (should have score 0) but division would result in NA
	
	target_score.name = 'issel_target'
	target_score.index.name = 'filename'
	
	# the smaller the better
	return target_score

def main():
	print(__file__, os.path.dirname(__file__))
	
	global violationsSpecs
	violationsSpecs = pd.read_csv(os.path.dirname(__file__) + '/ViolationsSpecifications.csv', sep=';')
	# MUST USE SourceMeter 8.2, NOT 9, because the specs.csv was written for 8.2
	
	METRICS_DIR = os.environ['METRICS_DIR']
	
	pmdFileBefor = sys.argv[1]
	pmdFileAfter = sys.argv[2]
	commit = sys.argv[3]
	commit = commit[0:10]
	
	#try:
	targetBefor = targetFormulation(pmdFileBefor)
	targetBefor.to_csv(METRICS_DIR + '/' + commit + '_target_befor.csv')
	
	print('saved target for before ' + commit)
	#except:
	#	pass
	
	#try:
	targetAfter = targetFormulation(pmdFileAfter)
	targetAfter.to_csv(METRICS_DIR + '/' + commit + '_target_after.csv')
		
	print('saved target for after ' + commit)
	#except:
	#	pass
	print('Goodbye')

if __name__ == '__main__':
	main()

