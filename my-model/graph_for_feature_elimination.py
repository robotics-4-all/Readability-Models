import joblib, sys
import pandas as pd
import matplotlib.pyplot as plt

print(sys.argv)
#allsc = joblib.load('all_scores_rbf2_goodnorm')
allsc = joblib.load(sys.argv[1])

some = allsc[['test_neg_mean_squared_error','median_mse','features','num_features']]

best_for_each_num = some.loc[ some.groupby('num_features').median_mse.idxmin() ]


x = []
for i in best_for_each_num.num_features:
	x = [*x, i,i,i,i,i]

y = []
for i in best_for_each_num.test_neg_mean_squared_error:
	y = [*y, *i]

plt.scatter(x,y, label='Mean square error')
plt.plot(best_for_each_num.num_features.values, best_for_each_num.median_mse.values, color='red', label='median MSE')

plt.legend()
plt.xlabel('number of features')

plt.savefig('fig_elimin_' + sys.argv[1] + '.png')

