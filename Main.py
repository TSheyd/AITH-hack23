import pandas as pd
import numpy as np

import xgboost as xgb
from sklearn.utils import resample

from skopt import BayesSearchCV

from scipy.stats import mannwhitneyu
from statsmodels.stats import multitest

import sys
import os

sys.path.append(os.getcwd())

import PyRauLCF

def RauLCF(data, cond_col):
    '''
    Function that applies Rau low counts filtering.
    Requirements:
    - PyRauLCF.py script and neccessary support files

    Arguments:
    - data: a dataframe with counts/pseudocounts of genes expressions and a condition column
    - cond_col: a name of the condition column

    Returns:
    - A dataframe with excluded genes with expression lower than threshold for every sample
    '''
    matrix = data.drop(columns=[cond_col]).to_numpy(dtype='float32')
    vector = data[cond_col].apply(lambda x: str(x)).to_list()

    # Running filter
    threshold = PyRauLCF.FindOptimalThreshold(matrix, vector, 1, 200, 25)

    print("The threshould from RauLCF is " + str(threshold))

    # Removing all genes below threshold
    filtered_data = data.loc[:, (data.max(axis=0) > threshold)]

    filtered_data[cond_col] = data[cond_col]

    print("Number of removed genes: " + str(len(data.columns) - len(filtered_data.columns)))

    return filtered_data


def get_features_stability(data, clf, cond_col, rand_state):
    '''
    Function that runs model on the stratified random subsamples, retrieving the feature importances.
    Arguments:
    - data: a dataframe with counts/pseudocounts of genes expressions and a condition column
    - clf: a model
    - cond_col: a name of the condition column
    - rand_state: random state

    Returns:
    - A dataframe with genes importances
    '''
    sample = resample(data, n_samples=int(data.shape[0] * 0.8), stratify=data[cond_col], random_state=rand_state)
    
    clf = clf.fit(sample.drop(columns=[cond_col]), sample[cond_col].astype('int'))
    
    feature_importance = pd.DataFrame(clf.feature_importances_, sample.iloc[:, :-1].columns)
    feature_importance.rename(columns={0: "Importance"}, inplace=True)
    
    return (feature_importance)


def run_xgb(data, cond_col, top_importance, n_obs):
    '''
    Function that optimizes the hyperparameters for XGB using Bayesian search, then running on a
    subsamples and providing a feature importances.
    Requirements:
    - get_features_stability() function

    Arguments:
    - data: a dataframe with counts/pseudocounts of genes expressions and a condition column
    - cond_col: a name of the condition column
    - top_importance: the number of most important genes to keep from each iteration
    - n_obs: required minimal number of occurrences of a gene in the top list across all iterations

    Returns:
    - A dataframe with important genes
    '''
    XGBclf = BayesSearchCV(
        xgb.XGBClassifier(objective="multi:softmax", num_class="2", random_state=500),
        {
            'n_estimators': (5, 500),
            'max_depth': (2, 500),
            'max_leaves': (2, 4),
            'learning_rate': (0.0001, 0.9),
            'booster': ("gbtree", "gblinear", "dart"),
            'reg_alpha': (0.0001, 1)
        },
        cv=2,
        n_jobs=24,
        random_state=500
    )
    XGBclf.fit(data.drop(columns=[cond_col]), data[cond_col].astype('int_'))
    best_params_xgb = XGBclf.best_params_

    print(best_params_xgb)

    XGBclf_best = xgb.XGBClassifier(n_estimators=best_params_xgb['n_estimators'],
                                    max_depth=best_params_xgb['max_depth'],
                                    max_leaves=best_params_xgb['max_leaves'],
                                    learning_rate=best_params_xgb['learning_rate'],
                                    booster=best_params_xgb['booster'],
                                    reg_alpha=best_params_xgb['reg_alpha'],
                                    objective="multi:softmax",
                                    num_class="4",
                                    random_state=500)

    # Obtaining feature importance for different data subsets
    for i in range(100):
        importance = get_features_stability(data, XGBclf_best, cond_col, i).abs().mean(axis=1).sort_values(
            ascending=False)
        if i == 0:
            stability_xgb = importance.iloc[:top_importance]
        else:
            stability_xgb = pd.concat([stability_xgb, importance.iloc[:top_importance]], axis=1)

    stability_xgb['genes'] = stability_xgb.index

    stable_genes = stability_xgb.loc[stability_xgb.isna().sum(axis=1) <= n_obs, 'genes']

    ml_filtered_data = data[stable_genes.values.tolist()]
    ml_filtered_data[cond_col] = data[cond_col]

    return ml_filtered_data


def run_utest(data, cond_col):
    '''
    Function that runs multiple Mann-Whitney U tests for every pair of conditions.
    FDR is controlled using Benjamini-Hochberg correction.

    Arguments:
    - data: a dataframe with counts/pseudocounts of genes expressions and a condition column
    - cond_col: a name of the condition column

    Returns:
    - A dataframe with genes, groups tested, pvals and padj
    '''
    groups = np.unique(data[cond_col])

    results_df = []
    expr = data.drop(columns=[cond_col])

    # Loop over each feature
    for i in range(expr.shape[1]):
        # Loop over each possible pair of groups
        for j in range(len(groups)):
            for k in range(j + 1, len(groups)):
                # Get the samples for each group
                group1 = expr.loc[(data[cond_col] == groups[j]), expr.columns[i]].apply(lambda x: float(x))
                group2 = expr.loc[(data[cond_col] == groups[k]), expr.columns[i]].apply(lambda x: float(x))
                # Run the Mann-Whitney U test and print the result
                stat, pval = mannwhitneyu(group1, group2, nan_policy='omit')
                results_df.append({'Gene': expr.columns[i],
                                   'Groups': f'Group {groups[j] + 1} vs Group {groups[k] + 1}',
                                   'pval': pval})

    results_df = pd.DataFrame.from_records(results_df)

    rej, p_adj, alphsid, alphb = multitest.multipletests(results_df['pval'], alpha=0.05, method='fdr_bh')

    results_df['padj'] = p_adj

    return results_df.sort_values(by=['padj'])


def MarkerFinder(data, cond_col, top_importance, n_obs, output_stat, output_hm):
    '''
    Function that runs all the functions above. The order:
    1) Rau filter
    2) XGBoost
        2a) Hyperparameters tuning
        2b) Retrieveing importances
    3) Mann-Whitney

    Arguments:
    - data: a dataframe with counts/pseudocounts of genes expressions and a condition column
    - cond_col: a name of the condition column
    - top_importance: the number of most important genes to keep from each iteration
    - n_obs: required minimal number of occurrences of a gene in the top list across all iterations
    - output_stat: file name for the results output
    - output_hm: file name for the heatmap dataset output

    Returns:
    - A dataframe with genes, groups tested, pvals and padj
    '''
    raw_data = pd.read_table(data, index_col=None)

    filtered_data = RauLCF(raw_data, cond_col)

    filtered_data = filtered_data.apply(lambda x: pd.to_numeric(x.convert_dtypes()))

    ml_biomarkers = run_xgb(filtered_data, cond_col, top_importance, n_obs)

    results = run_utest(ml_biomarkers, cond_col)

    results.to_csv(output_stat, sep="\t", index=False)

    heatmap_vars=results['Gene'].tolist()
    heatmap_vars.append(cond_col)

    raw_data[heatmap_vars].sort_values(by=cond_col).to_csv(output_hm, sep="\t", index=False)

    return results


'''
------------------------------------------------------
Test call
------------------------------------------------------
'''
MarkerFinder("./data/dummy_expr.txt", "condition", 50, 50, "./data/results_stat.txt", "./data/results_hm.txt")

# %%
