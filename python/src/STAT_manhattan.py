import argparse
import csv
import operator
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.stats.multitest as multi
from colour import Color
from scipy.stats import mannwhitneyu
from sklearn import metrics

#########################################
#           Python 3.7.9                #
#           input = csv file            #
#           output = 'mhplot.pdf'       #
#########################################

def main(args):

    input = args.input
    out = args.output
    original_features = int(args.original_features)
    
    print('Creating: ',os.path.basename(out))

    if not os.path.exists(os.path.dirname(out)):
        try:
            os.makedirs(os.path.dirname(out))
        except:
            pass

    input_file = pd.read_csv(input)
    y = input_file['y'] #result(0 or 1)
    modalities = input_file.columns.drop('y')#[original_features:]
    X = input_file.loc[:,modalities] #value of covariates

    values = pd.DataFrame(index=modalities,columns=['AUC','pval','qval'])

    # Calculate AUC, pval and qval

    for mod in modalities:
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for label in [0,1]:
            fpr[label], tpr[label], _ = metrics.roc_curve(y, X[mod], pos_label=label)
            roc_auc[label] = round(metrics.auc(fpr[label], tpr[label]),3)
        ind_max = max(roc_auc.items(), key=operator.itemgetter(1))[0]
        values.loc[mod,'AUC'] = round(roc_auc[ind_max],3)
        values.loc[mod,'pval'] = mannwhitneyu(X.iloc[y[y==1].index][mod],X.iloc[y[y==0].index][mod], alternative='two-sided')[1]
    
    values['qval'] = abs(multi.multipletests(values['pval'], method = 'fdr_bh')[1])

    values = values.iloc[original_features:]
    # values = values.loc[values[values['AUC'] >= min_auc].index]
    # nbr_features = len(values.index)

    for mod in values.index:
        values.loc[mod,'pval'] = mannwhitneyu(X.iloc[y[y==1].index][mod],X.iloc[y[y==0].index][mod], alternative='two-sided')[1]

    values['pval'] = round(-np.log(values['pval'].astype(float))/np.log(10),3)
    values['qval'] = round(-np.log(values['qval'].astype(float))/np.log(10),3)

    features = values.index.str.replace(' ',',').values.astype(str)
    mod1 = [val[0] for val in np.char.split(features,'+')]
    mod1 = [val[0] for val in np.char.split(mod1,'*')]
    mod2 = [val[-1] for val in np.char.split(features,'+')]
    unique_mod = []
    for mod in mod1 :
        if mod not in unique_mod: unique_mod.append(mod)

    # Plot

    fig, axes = plt.subplots(nrows=3, ncols=1)
    df = pd.DataFrame(mod1, columns=['mod1'])
    colormap = ['orange', 'green', 'purple', 'blue', 'cyan']
    colors = dict(zip(unique_mod,colormap))
    Max = pd.DataFrame(index=unique_mod, columns=values.columns)
    counts = []
    ticks = []
    for i in range(len(unique_mod)):
        Max.loc[unique_mod[i]] = (values[values.index.str.startswith(unique_mod[i])].astype(float)).idxmax(axis=0)
        counts.append(mod1.count(unique_mod[i]))
        ticks.append(counts[i]/2 + sum(counts[:i]))

    for ax, value in zip(fig.axes, values.columns.values):
        plt.sca(ax)
        ax.scatter(values.index, values.loc[:,value], s=20, c=df['mod1'].map(colors))
        for i in Max.index:
            maxx = Max.loc[i,value]
            plt.annotate(maxx.split('+')[-1], (list(values.index.values).index(maxx), values.loc[maxx,value]))

        locs, labels = plt.xticks()
        x = [min(locs), max(locs)]
        mean = values[value].mean()
        y = [mean, mean]
        plt.plot(x, y, color="midnightblue", linewidth=1)

        plt.xticks(ticks, colors.keys(), rotation=90)
        plt.ylabel(values.columns[-int(round(3*ax.get_position().y0)+1)])

    # plt.show()
    plt.gcf().set_size_inches(15, 15)
    plt.savefig(out)

    print('Saving: ',os.path.basename(out))




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('input',help='input csv file (original or interraction features)')
    parser.add_argument('--output','-o',default='out/manhattan.pdf',help='output filename')
    parser.add_argument('--original_features',default=0,help='number of original features to remove from interractions')
    args = parser.parse_args()

    main(args)
