# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 18:45:28 2015

@author: Laurent
"""
#External librairies
import os, argparse
import matplotlib.pyplot as plt

#Internal libraries
import pvc_write    as write
import pvc_csvParse as csvParse
import pvc_workers  as workers

#Command parser
def commands(parser):
    parser.add_argument('--nbr',    type=int,   dest='nbr',    default=2,     help='Number of graphs per figure (Nx1)') 
    parser.add_argument('--hspace',             dest='hspace', default=0.3,   help='Horizontal space between subplots')
    parser.add_argument('--csv',                dest='csv',    required=True, help='Directory (Optional: default is current working directory)')
    parser.add_argument('--nVeh',   type=float, dest='num',    default=10)
    parser.add_argument('--decel',  type=float, dest='dp',     default=0)
    parser.add_argument('--accel',  type=float, dest='a0',     default=0)
    return parser.parse_args()

class thisConfig:
    def __init__(self,num,dp,a0):
        self.num_const_thresh = num
        self.dp_const_thresh  = dp
        self.a0_const_thresh  = a0

#Main code
Commands = commands(argparse.ArgumentParser())
a = Commands.nbr

history = write.History.read_history('calib_history.txt')
all_variables = csvParse.extractParamFromCSV(os.curdir,Commands.csv)
variables = [var for var in all_variables if var.include is True]
chunks = workers.cleanChunks(a, variables)

prob_history = [p for p in history if p.fout!= 'crashed' and (p.C_0 > 0 or p.C_1 > 0 or p.C_2 > 0)]
c_ok_history = [p for p in history if p.fout!= 'crashed' and (p.C_0 <= 0 and p.C_1 <= 0 and p.C_2 <= 0)]

#y values for every graph is the same
##blue for variables without violated constraints
y_b = [p.fout for p in c_ok_history]
##red for variables with at least one violated constraint
y_r = [p.fout for p in prob_history]

for c in xrange(len(chunks)):    
    fig, ax = plt.subplots(a, 1, squeeze=True)
    if len(chunks[c]) < a:
        for axis in xrange(a-len(chunks[c])):
            ax[-(axis+1)].axis('off')

    for v in xrange(len(chunks[c])):
        #without violated constraints
        x_b = [p.point[a*c+v] for p in c_ok_history]
        #with at least one violated constraint
        x_r = [p.point[a*c+v] for p in prob_history]        
        
        ax[v].plot(x_b,y_b, linestyle='None', marker='o', color = 'b')
        ax[v].plot(x_r,y_r, linestyle='None', marker='o', color = 'r')
        ax[v].set_title('Value of '+r'$f_{out}$'+' vs Value of ' + variables[a*c+v].name)

    plt.subplots_adjust(hspace=Commands.hspace)
    plt.savefig(os.path.join(os.curdir, 'Visualization_of_tested_variable_'+str(c)+'_of_'+str(len(chunks)-1)))
    plt.clf()
    plt.close(fig)

constraint_list = xrange(3)
const_chunks = workers.cleanChunks(a, constraint_list)
for c in xrange(len(const_chunks)):
    fig, ax = plt.subplots(a, 1, squeeze=True)
    if len(const_chunks[c]) < a:
        for axis in xrange(a-len(const_chunks[c])):
            ax[-(axis+1)].axis('off')

    for v in xrange(len(const_chunks[c])):
        if const_chunks[c][v] == 0:
            h_b = [p.C_0 for p in c_ok_history]
            h_r = [p.C_0 for p in prob_history]
        elif const_chunks[c][v] == 1:
            h_b = [p.C_1 for p in c_ok_history]
            h_r = [p.C_1 for p in prob_history]
        elif const_chunks[c][v] == 2:
            h_b = [p.C_2 for p in c_ok_history]
            h_r = [p.C_2 for p in prob_history]

        ax[v].plot(h_b,y_b, linestyle='None', marker='o', color = 'b')
        ax[v].plot(h_r,y_r, linestyle='None', marker='o', color = 'r')
        ax[v].set_title('Value of '+r'$f_{out}$'+' Value of constraint C' + str(const_chunks[c][v]))

    plt.subplots_adjust(hspace=Commands.hspace)
    plt.savefig(os.path.join(os.curdir, 'Visualization_of_constraints_'+str(c)+'_of_'+str(len(const_chunks)-1)))
    plt.clf()
    plt.close(fig)    
    