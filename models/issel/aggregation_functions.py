import joblib, os
import numpy as np
import pandas as pd

try:
	SCRIPTS_DIR = os.environ['SCRIPTS_DIR']
except KeyError:
	SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ISSEL_DIR = SCRIPTS_DIR + '/models/issel/'


def aggregation(complexity, coupling, documentation):

    # Weighted average - Complexity contains 5 metrics, Coupling 2 metrics and Documentation 3 metrics
    # return [0.5*cmplx+0.2*cpl+0.3*doc for (cmplx, cpl, doc) in zip(complexity, coupling, documentation)]

    # Same weighted average - Cutoff at 0 and 1
    # return [np.min([np.max([0.5*cmplx+0.2*cpl+0.3*doc, 0.0]), 1.0]) for (cmplx, cpl, doc) in zip(complexity, coupling, documentation)]
    #return [min(max(0.5*cmplx+0.2*cpl+0.3*doc, 0.0), 1.0) for (cmplx, cpl, doc) in zip(complexity, coupling, documentation)] # don't use np
    # or maybe TODO
    return np.clip(0.5*complexity + 0.2*coupling + 0.3*documentation, 0.0, 1.0)

    # Simple mean
    # return [np.mean([cmplx, cpl, doc]) for (cmplx, cpl, doc) in zip(complexity, coupling, documentation)]

# Function to normalize predictions for the histograms (with or without offset)
def normalize_values(pred_test, offset=0):
    minval = np.quantile(pred_test, 0.01)
    maxval = np.quantile(pred_test, 0.99)

    norm_pred_test = [((val - minval)/(maxval - minval))+offset for val in pred_test]

    return np.clip(norm_pred_test, 0.0, 1.0)


def prediction(cluster, df):

    cmplx_model=joblib.load(ISSEL_DIR + "SVR_" + cluster + "_complexity.pkz")
    cpl_model = joblib.load(ISSEL_DIR + "SVR_" + cluster + "_coupling.pkz")
    doc_model = joblib.load(ISSEL_DIR + "SVR_" + cluster + "_documentation.pkz")

    #target = df["Readability"]
    Xtest = df # df.drop(["Readability"], axis=1)

    cmplx_cols = Xtest[["HPV", "MI", "NL", "McCC", "HDIF"]] # Complexity metrics
    cpl_cols = Xtest[["NII", "NOI"]] # Coupling metrics
    doc_cols = Xtest[["CD", "DLOC", "CLOC"]] # Documentation metrics

    # TODO maybe remove the column names, because the model complains
    # that it was trained without them. "SVR was fitted without feature names"
    pred_cmplx = cmplx_model.predict(cmplx_cols)
    pred_cpl = cpl_model.predict(cpl_cols)
    pred_doc = doc_model.predict(doc_cols)

    #pred_cmplx = normalize_values(pred_cmplx)
    #pred_cpl = normalize_values(pred_cpl)
    #pred_doc = normalize_values(pred_doc)

    pred = aggregation(pred_cmplx, pred_cpl, pred_doc)

    out_df = pd.DataFrame({'readab': pred, 'r_cmplx': pred_cmplx, 'r_cpl': pred_cpl, \
        'r_doc': pred_doc, 'LOC': df.LOC}, index=df.index)

    #pred = normalize_values(pred)
    return out_df


# Function to predict all methods of a dataframe, regardless of the cluster they belong to
def prediction_per_cluster(df):

    small_methods = df[(df["LLOC"] < 11)]
    medium_methods = df[(df["LLOC"] >= 11) & (df["LLOC"] < 52)]
    large_methods = df[(df["LLOC"] >= 52)]


    df_list = [] #pd.DataFrame([], columns=['readab', 'r_cmplx', 'r_cpl', 'r_doc', 'LOC'])

    if len(small_methods) > 0:
        small_pred = prediction('small', small_methods)
        df_list.append(small_pred)

    if len(medium_methods) > 0:
        medium_pred = prediction('medium', medium_methods)
        df_list.append(medium_pred)

    if len(large_methods) > 0:
        large_pred = prediction('large', large_methods)
        df_list.append(large_pred)

    out_df = pd.concat(df_list)
    out_df['Path'] = df.Path
    return out_df

