import os
import math
import argparse
import numpy as np
import warnings
import pandas as pd
from glmnet import LogitNet
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LogisticRegressionCV
import statsmodels.api as sm
from statsmodels.formula.api import glm
from sklearn import metrics
from matplotlib import pylab as plt
warnings.simplefilter(action='ignore', category=FutureWarning)

#########################################
#           Python 3.7.9                #
# input = 'interraction.csv', 'AUC.csv' #
#   output = 'Pred.csv', 'Stat.csv'     #
#########################################

def main(args):

    interractions = args.interractions
    auc = args.auc
    out = args.output
    seed1 = int(args.first_seed)
    seed_end = int(args.last_seed)
    nbr_seed = seed_end-seed1
    nbr_folds = int(args.folds)
    features_to_select =int(args.features)

    if out[-1]!='/':
        out=out+'/'

    if not os.path.exists(out):
        os.mkdir(out)

    interractions = pd.read_csv(interractions)
    interractions = interractions.iloc[:,:features_to_select+1]
    AUC = pd.read_csv(auc, index_col=0)
    AUC = AUC.iloc[:features_to_select]

    modalities = interractions.columns.drop('y')
    y = interractions['y'] #result(0 or 1)
    X = interractions.loc[:,modalities] #value of covariates
    nbr_features = len(modalities)
    samples = len(y)

    stat = pd.DataFrame(columns=['ACC','PREC1','PREC0','RECALL1','RECALL0','F1SCORE','AUC'])
    importance = pd.DataFrame(0, index=modalities, columns=AUC.columns)
    pred = pd.DataFrame(index=range(samples),columns=range(seed1,seed_end))

    for seed in range(seed1,seed_end):
        print(seed)
        skf = StratifiedKFold(n_splits=nbr_folds, shuffle = True, random_state = seed)
        skf.get_n_splits(X, y)

        i=0
        for train_index, test_index in skf.split(X, y):
            index = AUC[AUC[str(seed)+'_'+str(i+1)] > 0.7].index
            X_train, X_test = X.loc[train_index][index], X.loc[test_index][index]
            y_train, y_test = y.loc[train_index], y.loc[test_index]

            # Sklearn
            clf = LogisticRegression(fit_intercept=True, random_state=0)
            clf = clf.fit(X_train, y_train)
            pred.at[test_index,seed] = clf.predict_proba(X_test)[:,1]

            # # GLM
            # X_train_copy = X_train
            # X_train_copy.columns = X_train_copy.columns.str.replace('+','_').str.replace('.', '_').str.replace('/', '_')
            # X_test_copy = X_test
            # X_test_copy.columns = X_test_copy.columns.str.replace('+', '_').str.replace('.', '_').str.replace('/', '_')
            # all_columns = '+'.join(X_train_copy.columns)
            # mod = glm(formula='y_train~'+all_columns+'+1', data=X_train_copy, family=sm.families.Binomial(sm.families.links.logit())).fit()
            # pred.at[test_index,seed] = mod.predict(X_test_copy)

            i+=1
        pred_seed = pred[seed].astype(float).round(0).astype(bool)
        y_bool = y.astype(bool)
        acc = round(metrics.accuracy_score(y_bool, pred_seed), 4)
        prec1 = round(metrics.precision_score(y_bool, pred_seed), 4)
        prec0 = round(metrics.precision_score(~y_bool, ~pred_seed), 4)
        recall1 = round(metrics.recall_score(y_bool, pred_seed), 4)
        recall0 = round(metrics.recall_score(~y_bool, ~pred_seed), 4)
        f1 = round(metrics.f1_score(y_bool, pred_seed), 4)
        auc = round(metrics.roc_auc_score(y_bool, pred[seed]), 4)
        stat.loc[seed-seed1] = [acc,prec1,prec0,recall1,recall0,f1,auc]

    pred.to_csv(out+'Pred.csv', index=False)
    stat.to_csv(out+'Stat.csv')


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--interractions','-i',default='interractions.csv',help='input csv interraction file')
    parser.add_argument('--auc',default='AUC.csv',help='input csv AUC file')
    parser.add_argument('--output','-o',default='LogisticRegression/',help='output folder')
    parser.add_argument('--first_seed',default=2020,help='number of the first seed')
    parser.add_argument('--last_seed',default=2030,help='number of the last seed')
    parser.add_argument('--folds',default=5,help='number of the folds for cross-validation')
    parser.add_argument('--features',default=52,help='number of features to select')
    args = parser.parse_args()

    main(args)
