# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 18:45:28 2015

@author: Laurent
"""
#External librairies
import os, argparse
import matplotlib.pyplot as plt

#Internal libraries
import pvc_write   as write
import pvc_define  as define
import pvc_outputs as outputs

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
all_variables = define.extractParamFromCSV(os.curdir,Commands.csv)
variables = [var for var in all_variables if var.include is True]
chunks = define.cleanChunks(a, variables)

for c in xrange(len(chunks)):    
    fig, ax = plt.subplots(a, 1, squeeze=True)
    if len(chunks[c]) < a:
        for axis in xrange(a-len(chunks[c])):
            ax[-(axis+1)].axis('off')

    for v in xrange(len(chunks[c])):

        #without the presence of error files
        x_b = []
        y_b = []
        #with the presence of at least an error file
        x_r = []        
        y_r = []
        
        for p in history:
            if p.fout != 'crashed':
                if p.C_0 > 0 or p.C_1 > 0 or p.C_2 > 0:
                    x_r.append(p.point[a*c+v])
                    y_r.append(p.fout)
                    
                else:
                    x_b.append(p.point[a*c+v])
                    y_b.append(p.fout)
        
        ax[v].plot(x_b,y_b, linestyle='None', marker='o', color = 'b')
        ax[v].plot(x_r,y_r, linestyle='None', marker='o', color = 'r')
        ax[v].set_title('Value of fout vs Value of ' + variables[a*c+v].name)

    plt.subplots_adjust(hspace=Commands.hspace)
    plt.savefig(os.path.join(os.curdir, 'Visualization_of_tested_variable_'+str(c)+'_of_'+str(len(chunks)-1)))
    plt.clf()
    plt.close(fig)