# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 12:54:24 2015

@author: lab
"""

if __name__ == "__main__":
    '''takes a single number as entry, corresponding to the point folder path number'''

    import pandas, os, sys
    import pvc_mathTools as mathTools

    data = pandas.read_csv(os.path.join(os.getcwd(),'calib_history.txt'), index_col='#', header=0, lineterminator='\n', error_bad_lines=True, sep='\t', skiprows=1)
    initial_fout = data['fout'][1]

    tmp = data.loc[int(sys.argv[1]),'fout':]
    if tmp['fout'] < initial_fout and (tmp[1:] <= 0).all():
        pass #we got an improvement and we keep the point

    else:
        if not (tmp[1:] > 10).any():
            pass #we have a really problematic point and we keep it

        else:
            elements = mathTools.goIntoDirs(os.path.join(os.getcwd(),'point_'+str(int(sys.argv[1]))))

            for elem in elements:
                if '.inpx' in elem or '.png' in elem:
                    pass #we keep images and vissim network files
                else:
                    os.remove(elem)
