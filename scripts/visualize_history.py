# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 18:45:28 2015

@author: Laurent
"""

import os, argparse
import matplotlib.pyplot as plt

import pvc_write  as write
import pvc_define as define

def commands(parser):
    parser.add_argument('--nbr',    type=int, dest='nbr',    default=2,     help='Number of graphs per figure (Nx1)') 
    parser.add_argument('--hspace',           dest='hspace', default=0.3,   help='Horizontal space between subplots')
    parser.add_argument('--csv',              dest='csv',    required=True, help='Directory (Optional: default is current working directory)')
    return parser.parse_args()
    
Commands = commands(argparse.ArgumentParser())

a = Commands.nbr

history = write.History.read_history('calib_history.txt')

all_variables = define.extractParamFromCSV(os.curdir,Commands.csv)
variables = [var for var in all_variables if var.include is True]
chunks = define.cleanChunks(a, variables)

for c in xrange(len(chunks)):    
    fig, ax = plt.subplots(a, 1, squeeze=True)
    if len(chunks[c]) < a:
        for axis in xrange(a-len(chunks[c])):
            ax[-(axis+1)].axis('off')

    for v in xrange(len(chunks[c])):
        x = [p.point[a*c+v] for p in history if p.fout != 'crashed']
        y = [p.fout for p in history if p.fout != 'crashed']
        
            #import pdb;pdb.set_trace()
        ax[v].plot(x,y, linestyle='None', marker='o')
        ax[v].set_title('Value of fout vs Value of ' + variables[a*c+v].name)

    plt.subplots_adjust(hspace=Commands.hspace)
    plt.savefig(os.path.join(os.curdir, 'Visualization_of_tested_variable_'+str(c)+'_of_'+str(len(chunks)-1)))
    plt.clf()
    plt.close(fig)