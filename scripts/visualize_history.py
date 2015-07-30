# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 18:45:28 2015

@author: Laurent
"""
#External librairies
import os, argparse
import matplotlib.pyplot as plt
import pandas
import parallel_coordinates

#Internal libraries
import pvc_csvParse as csvParse

#Command parser
def commands(parser):
    parser.add_argument('--dir',                dest='cwd',    default=os.getcwd(), help='Directory (Optional: default is current working directory)')
    parser.add_argument('--csv',                dest='csv',    required=True,       help='Name of the CSV file associated with the inpx')
    return parser.parse_args()

#Main code
Commands = commands(argparse.ArgumentParser())

all_variables = csvParse.extractParamFromCSV(Commands.cwd,Commands.csv)
variables = [var for var in all_variables if var.include is True]

data = pandas.read_csv(os.path.join(Commands.cwd,'calib_history.txt'), index_col=False, header=0, lineterminator='\n', error_bad_lines=True, sep='\t', skiprows=1)

#finding the best point
tmp = data.loc[:,'fout':]                                       #keeping fout and the constraints
cols = [c for c in tmp.columns.tolist() if c.startswith('C')]   #columns corresponding to constraints
line = tmp.loc[(tmp[cols] <= 0).all(1),'fout'].argmin()         #line with the lowest value of fout in the submatrix where all const <= 0

                    #in one line...     tmp.loc[(tmp[[c for c in tmp.columns.tolist() if c.startswith('C')]] <= 0).all(1),'fout'].argmin()
#changing the value in the big data frame
data.loc[line,'State'] = 'Best point'

#keeping only the columns we want to trace
columns = [var.name for var in variables] + ['State']
data = data[columns]

lower_bounds = [var.desired_min for var in variables if var.include is True]
upper_bounds = [var.desired_max for var in variables if var.include is True]

parallel_coordinates.parallel_coordinates(data.dropna(subset=['State']), 'State', color = ['#993399','b','g','r'], normalize=True, bounds = [lower_bounds, upper_bounds], vertical_xtickslabels=True, tracepriority=['First Point','Best Point','Feasible','Unfeasible'], tracepriority_linewidth=[10, 10, 1, 1])
plt.show()