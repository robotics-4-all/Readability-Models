import joblib
import pandas as pd

MEANS = {'BW Avg Assignment': 0.128519, 'BW Avg blank lines': 0.125372, 'BW Avg commas': 0.205622,
'BW Avg conditionals': 0.034176, 'BW Avg indentation length': 7.298117, 'BW Avg loops': 0.012005,
'BW Avg parenthesis': 0.746898, 'BW Avg spaces': 9.177091, 'BW Max keywords': 4.089042,
'CC': 0.105365, 'CLC': 0.090072, 'CLLC': 0.098914, 'Dorn Visual X Numbers': 102.433089,
'issel_r_cmplx': 0.548847, 'NA': 9.087606, 'NL': 2.198478, 'NLA': 8.485710,
'NLE': 1.933506, 'NS': 1.169467, 'TNA': 12.494040}

STDEVS = {'BW Avg Assignment': 0.067894, 'BW Avg blank lines': 0.042262, 'BW Avg commas': 0.192064,
'BW Avg conditionals': 0.034777, 'BW Avg indentation length': 3.453235, 'BW Avg loops': 0.014968,
'BW Avg parenthesis': 0.275048, 'BW Avg spaces': 3.604274, 'BW Max keywords': 1.298508,
'CC': 0.184580, 'CLC': 0.156427, 'CLLC': 0.171025, 'Dorn Visual X Numbers': 80.881287,
'issel_r_cmplx': 0.127186, 'NA': 16.990706, 'NL': 2.360065, 'NLA': 16.772620,
'NLE': 1.653051, 'NS': 6.255707, 'TNA': 21.576552}

MEANS = pd.Series(MEANS)
STDEVS = pd.Series(STDEVS)


model_names = ['svr_linear_20', 'svr_linear_7', 'svr_rbf_20', 'svr_rbf_9']
models = {name: joblib.load(name) for name in model_names}

def apply_my_models(data):
	
	data = (data[MEANS.index].dropna() - MEANS) / STDEVS
	# Drop the rows with NaN here. Then, we can set the index at the
	# returned dataframe, because model.predict() does not keep indexes
	# But only drop NaNs from the interested columns (MEANS.index), not any.
	
	predicted = pd.DataFrame()
	
	for modl_name in models:
		
		input_data = data[models[modl_name].feature_names_in_]
		
		predicted[modl_name] = models[modl_name].predict(input_data)
	
	predicted = predicted.set_index(data.index) # Weirdly needs to be in seperate line from return
	return predicted


df_after_readabil,df_befor_readabil,df_diffs_readabil,df_after_nonread,df_befor_nonread,df_diffs_nonread = joblib.load('Zdump_withtarg_byfiles_aftbefdif_readabilnonread')

dfs_with_models = [i.join(apply_my_models(i)) for i in [df_after_readabil, df_befor_readabil, df_after_nonread, df_befor_nonread] ]

# add the diffs = aft-bfr
dfs_with_models.insert(2, dfs_with_models[0] - dfs_with_models[1])
dfs_with_models.append(dfs_with_models[3] - dfs_with_models[4])

joblib.dump(tuple(dfs_with_models), 'Zdump_withmodl_byfiles_aftbefdif_readabilnonread')
