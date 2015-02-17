import os, argparse
import pvc_define as define


def commands(parser):
    parser.add_argument('-n', '--nbr',  type=int,  dest='nbr',  default=1,          help='Number of points to produce') 
    parser.add_argument('-f', '--file',            dest='file', default='',         help='CSV file to gather variable informations from (Required)')
    parser.add_argument('-d', '--dir',             dest='dir',  default=os.curdir,  help='Directory (Optional: default is current working directory)')
    return parser.parse_args()
    
Commands = commands(argparse.ArgumentParser())

variables  = define.extractParamFromCSV(Commands.dir, Commands.file)
corrected_variables = [var for var in variables if var.include is True]
points = define.genLHCsample(corrected_variables, Commands.nbr)

for i in xrange(len(corrected_variables)):
    
    string = '{0:<20}'.format(corrected_variables[i].name+':') + '\t'
    
    for n in xrange(Commands.nbr):
        string += str(round(points[n][i],2)) + '\t'
        
    print string