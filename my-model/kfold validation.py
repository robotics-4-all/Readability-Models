
from sklearn.model_selection import cross_validate
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from sklearn.feature_selection import RFECV
#from sklearn import datasets
from sklearn import svm
from datetime import datetime
from statistics import median
import pandas as pd
import joblib


model_features = ['BW Avg Assignment', 'BW Avg blank lines', 'BW Avg commas', 'BW Avg conditionals',
	'BW Avg indentation length','BW Avg loops', 'BW Avg parenthesis', 'BW Avg spaces', 'BW Max keywords',
	'CC', 'CLC', 'CLLC', 'Dorn Visual X Numbers', 'issel_r_cmplx', 'NA', 'NL', 'NLA', 'NLE', 'NS', 'TNA']

#model_features = ['BW Avg Assignment', 'BW Avg blank lines', 'BW Avg indentation length',
#	'BW Avg parenthesis', 'Dorn Visual X Numbers', 'issel_r_cmplx', 'NL']

df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread = joblib.load('Zdump_withtarg_byfiles_aftbefdif_readabilnonread')
print('Loaded file', flush=True)


all_file_metrics = pd.concat([df_after_readabil,df_befor_readabil, df_after_nonread,df_befor_nonread], ignore_index=True)

all_file_metrics = all_file_metrics[[*model_features, 'issel_target']].dropna()
# Choose only rows which do not have NA

# Maybe scaling?
print('Means: ', all_file_metrics[model_features].mean())
print('St dev: ', all_file_metrics[model_features].std())
#for metric in model_features:
#	all_file_metrics[model_features] = (all_file_metrics[model_features] - all_file_metrics[model_features].mean()) / all_file_metrics[model_features].std()
all_file_metrics[model_features] = (all_file_metrics[model_features] - all_file_metrics[model_features].mean()) / all_file_metrics[model_features].std()
# subtract mean before dividing
print('Normalized all model features')
# Print, so that we can do that again to apply the model
print(all_file_metrics[model_features])


### Recursive Feature Elimination
train_set, test_set = train_test_split(all_file_metrics, train_size=0.75) # For the RFE. randomly.
#svr = svm.SVR(kernel='linear')
# if kernel is not linear, it is impossible to rank the features' importance. Then RFE cannot work


all_scores = []

print(datetime.today().isoformat())
while len(model_features) > 4:
	
	score_without = {}
	
	print('Now have %d features, which one is the best to eliminate now?..' % len(model_features))
	
	for f in model_features:
		features_without_f = model_features.copy()
		features_without_f.remove(f)
		
		svr = svm.SVR(kernel='poly', cache_size=24000, shrinking=False, max_iter=2000000)#, verbose=True)
		# max_iter is necessary, otherwise it sometimes gets stuck
		#svr.fit(train_set[features_without_f], train_set.issel_target)
		
		#score_without[f] = svr.score(train_set[features_without_f], train_set.issel_target)
		
		#alternatively
		#scores = cross_val_score(svr, train_set[features_without_f], train_set.issel_target, cv=KFold(5, shuffle=True), verbose=1, n_jobs=8)
		scores = cross_validate(svr, train_set[features_without_f], train_set.issel_target, return_train_score=True,
		    scoring=['r2', 'neg_mean_squared_error', 'explained_variance'], cv=KFold(5, shuffle=True), verbose=1, n_jobs=8)
		
		score_without[f] = median(scores['test_neg_mean_squared_error'])
		print(features_without_f, score_without[f], scores)
		
		scores['median_mse'] = score_without[f]
		scores['features'] = features_without_f
		all_scores.append(scores)
	
	worse_feature = max(score_without, key=score_without.get) # argMAX we want the best resulting score
	model_features.remove(worse_feature)
	print('Eliminated feature ', worse_feature)


all_scores = pd.DataFrame(all_scores)
all_scores['num_features'] = all_scores['features'].apply(len)

few_features = all_scores[all_scores.num_features <= 10][['median_mse', 'features', 'num_features']]
print(few_features.sort_values('median_mse', ascending=False))

joblib.dump(all_scores, 'all_scores_poly2')
print(datetime.today().isoformat())

