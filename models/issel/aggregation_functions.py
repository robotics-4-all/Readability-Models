import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

def aggregation(complexity, coupling, documentation):

    # Weighted average - Complexity contains 5 metrics, Coupling 2 metrics and Documentation 3 metrics
    # return [0.5*cmplx+0.2*cpl+0.3*doc for (cmplx, cpl, doc) in zip(complexity, coupling, documentation)]

    # Same weighted average - Cutoff at 0 and 1
    return [np.min([np.max([0.5*cmplx+0.2*cpl+0.3*doc, 0.0]), 1.0]) for (cmplx, cpl, doc) in zip(complexity, coupling, documentation)]

    # Simple mean
    # return [np.mean([cmplx, cpl, doc]) for (cmplx, cpl, doc) in zip(complexity, coupling, documentation)]

# Function to normalize predictions for the histograms (with or without offset)
def normalize_values(pred_train, pred_test, offset=0):
    minval = np.quantile(pred_train, 0.01)
    maxval = np.quantile(pred_train, 0.99)
    vals2 = [((val - minval)/(maxval - minval))+offset  for val in pred_train]
    for i in range(0, len(vals2)):
        if(vals2[i] > 1):
            vals2[i] = 1
        if(vals2[i] < 0):
            vals2[i] = 0
    norm_pred_train = vals2

    vals3 = [((val - minval)/(maxval - minval))+offset for val in pred_test]
    for i in range(0, len(vals3)):
        if(vals3[i] > 1):
            vals3[i] = 1
        if(vals3[i] < 0):
            vals3[i] = 0
    norm_pred_test = vals3

    return norm_pred_train, norm_pred_test

def prediction(cluster, df):

    cmplx_model = joblib.load("SVR_" + cluster + "_complexity.pkz")
    cpl_model = joblib.load("SVR_" + cluster + "_coupling.pkz")
    doc_model = joblib.load("SVR_" + cluster + "_documentation.pkz")

    target = df["Readability"]
    columns = df.drop(["Readability"], axis=1)

    # Split to training and testing set
    Xtrain, Xtest, ytrain, ytest = train_test_split(columns, target, test_size=0.25, random_state=5)

    cmplx_cols_train = Xtrain[["HPV", "MI", "NL", "McCC", "HDIF"]] # Complexity metrics
    cmplx_cols_test = Xtest[["HPV", "MI", "NL", "McCC", "HDIF"]] # Complexity metrics
    cpl_cols_train = Xtrain[["NII", "NOI"]] # Coupling metrics
    cpl_cols_test = Xtest[["NII", "NOI"]] # Coupling metrics
    doc_cols_train = Xtrain[["CD", "DLOC", "CLOC"]] # Documentation metrics
    doc_cols_test = Xtest[["CD", "DLOC", "CLOC"]] # Documentation metrics

    pred_cmplx_train = cmplx_model.predict(cmplx_cols_train)
    pred_cmplx_test = cmplx_model.predict(cmplx_cols_test)
    pred_cpl_train = cpl_model.predict(cpl_cols_train)
    pred_cpl_test = cpl_model.predict(cpl_cols_test)
    pred_doc_train = doc_model.predict(doc_cols_train)
    pred_doc_test = doc_model.predict(doc_cols_test)

    pred_cmplx_train, pred_cmplx_test = normalize_values(pred_cmplx_train, pred_cmplx_test)
    pred_cpl_train, pred_cpl_test = normalize_values(pred_cpl_train, pred_cpl_test)
    pred_doc_train, pred_doc_test = normalize_values(pred_doc_train, pred_doc_test)

    pred_train = aggregation(pred_cmplx_train, pred_cpl_train, pred_doc_train)
    pred_test = aggregation(pred_cmplx_test, pred_cpl_test, pred_doc_test)

    pred_train, pred_test = normalize_values(pred_train, pred_test)

    return pred_train, ytrain, pred_test, ytest

# Function to predict all methods of a dataframe, regardless of the cluster they belong to
def prediction_per_cluster(df):

    small_methods = df[(df["LLOC"] < 11)]
    medium_methods = df[(df["LLOC"] >= 11) & (df["LLOC"] < 52)]
    large_methods = df[(df["LLOC"] >= 52)]

    # violations_keys = df.columns.to_list()
    # keys_to_remove = ["HDIF", "HPV", "MI", "McCC", "NL", "NII", "NOI", "CD", "CLOC", "DLOC", "LLOC", "LOC", "Project"]
    # for key in keys_to_remove:
    #     violations_keys.remove(key)

    pred_small = []
    small = pd.DataFrame()
    pred_medium = []
    medium = pd.DataFrame()
    pred_large = []
    large = pd.DataFrame()

    if (len(small_methods.index) > 0):
        cmplx_model = joblib.load("SVR_small_complexity.pkz")
        cpl_model = joblib.load("SVR_small_coupling.pkz")
        doc_model = joblib.load("SVR_small_documentation.pkz")
        X_cmplx = small_methods[["HPV", "MI", "NL", "McCC", "HDIF"]]
        X_cpl = small_methods[["NII", "NOI"]]
        X_doc = small_methods[["CD", "DLOC", "CLOC"]]

        pred_cmplx = cmplx_model.predict(X_cmplx)
        pred_cpl = cpl_model.predict(X_cpl)
        pred_doc = doc_model.predict(X_doc)

        pred_small = aggregation(pred_cmplx, pred_cpl, pred_doc)
        # small = pd.concat([small, small_methods["Project"]], axis = 1)
        # small = pd.concat([small, X_cmplx], axis = 1)
        # small = pd.concat([small, X_cpl], axis = 1)
        # small = pd.concat([small, X_doc], axis = 1)
        # small = pd.concat([small, small_methods["LLOC"]], axis = 1)
        # small["Complexity_score"] = pred_cmplx
        # small["Coupling_score"] = pred_cpl
        # small["Documentation_score"] = pred_doc
        # small["Readability"] = pred_small
        # small = pd.concat([small, small_methods[violations_keys]], axis = 1)

    # small_methods["Readability"] = pred_small

    if (len(medium_methods.index) > 0):
        cmplx_model = joblib.load("SVR_medium_complexity.pkz")
        cpl_model = joblib.load("SVR_medium_coupling.pkz")
        doc_model = joblib.load("SVR_medium_documentation.pkz")
        X_cmplx = medium_methods[["HPV", "MI", "NL", "McCC", "HDIF"]]
        X_cpl = medium_methods[["NII", "NOI"]]
        X_doc = medium_methods[["CD", "DLOC", "CLOC"]]

        pred_cmplx = cmplx_model.predict(X_cmplx)
        pred_cpl = cpl_model.predict(X_cpl)
        pred_doc = doc_model.predict(X_doc)

        pred_medium = aggregation(pred_cmplx, pred_cpl, pred_doc)
        # medium = pd.concat([medium, medium_methods["Project"]], axis = 1)
        # medium = pd.concat([medium, X_cmplx], axis = 1)
        # medium = pd.concat([medium, X_cpl], axis = 1)
        # medium = pd.concat([medium, X_doc], axis = 1)
        # medium = pd.concat([medium, medium_methods["LLOC"]], axis = 1)
        # medium["Complexity_score"] = pred_cmplx
        # medium["Coupling_score"] = pred_cpl
        # medium["Documentation_score"] = pred_doc
        # medium["Readability"] = pred_medium
        # medium = pd.concat([medium, medium_methods[violations_keys]], axis = 1)

    # medium_methods["Readability"] = pred_medium

    if (len(large_methods.index) > 0):
        cmplx_model = joblib.load("SVR_large_complexity.pkz")
        cpl_model = joblib.load("SVR_large_coupling.pkz")
        doc_model = joblib.load("SVR_large_documentation.pkz")
        X_cmplx = large_methods[["HPV", "MI", "NL", "McCC", "HDIF"]]
        X_cpl = large_methods[["NII", "NOI"]]
        X_doc = large_methods[["CD", "DLOC", "CLOC"]]

        pred_cmplx = cmplx_model.predict(X_cmplx)
        pred_cpl = cpl_model.predict(X_cpl)
        pred_doc = doc_model.predict(X_doc)

        pred_large = aggregation(pred_cmplx, pred_cpl, pred_doc)
        # large = pd.concat([large, large_methods["Project"]], axis = 1)
        # large = pd.concat([large, X_cmplx], axis = 1)
        # large = pd.concat([large, X_cpl], axis = 1)
        # large = pd.concat([large, X_doc], axis = 1)
        # large = pd.concat([large, large_methods["LLOC"]], axis = 1)
        # large["Complexity_score"] = pred_cmplx
        # large["Coupling_score"] = pred_cpl
        # large["Documentation_score"] = pred_doc
        # large["Readability"] = pred_large
        # large = pd.concat([large, large_methods[violations_keys]], axis = 1)

    # large_methods["Readability"] = pred_large

    return small, medium, large
    # return small_methods
