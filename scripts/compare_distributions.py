# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 14:49:46 2015

@author: Laurent
"""
import os, argparse, copy
from scipy import stats
import matplotlib.pyplot as plt

import pvc_write as write
import pvc_outputs as outputs
import pvc_analysis as analysis
import pvc_define as define

def Commands(parser):
    parser.add_argument('-c', '--choose',  choices=['Forward_Gaps','Lane_Change_Gaps','Speeds'],  dest='chosen',  default='Forward_Gaps',          help='Variable to analyse') 
    parser.add_argument('-d', '--dir',     dest='dirname',  default=os.curdir,  help='Directory (Optional: default is current working directory)')
    return parser.parse_args()
    
commands = Commands(argparse.ArgumentParser())

###################################################################################
commands.dirname = r'C:\Users\Laurent\Desktop\vissim files\A13\Calib_GP06001_0to9000\Calibration_Analysis_1\point_1'
commands.chosen = 'Forward_Gaps'

simulationStepsPerTimeUnit = 10
warmUpTime = 100

fps = 30

path_to_csv = r'C:\Users\Laurent\Desktop\vissim files\A13\Calib_GP06001_0to9000'
inpxname = 'calib_gp06001_0to9000.inpx'

fullpath = r'C:\Users\Laurent\Desktop\vissim files\A13\Calib_GP06001_0to9000\Autoroute13.traj'

###################################################################################

#extracting corridors information for vissim file calculations
VissimCorridors, trafIntCorridors = define.extractVissimCorridorsFromCSV(path_to_csv, inpxname)

#treat the .fzp files
inputs = [commands.dirname, simulationStepsPerTimeUnit, warmUpTime, True, VissimCorridors]
flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forSpeeds = outputs.treatVissimOutputs([f for f in os.listdir(commands.dirname) if f.endswith('fzp')], inputs)

#extract video data
video_data = write.load_traj(fullpath)

#define used data
if commands.chosen == 'Forward_Gaps':
    chosen_video_stat = video_data[3]
    chosen_stat = copy.deepcopy(forFMgap)
if commands.chosen == 'Lane_Change_Gaps':
    chosen_video_stat = video_data[4]
    chosen_stat = copy.deepcopy(oppLCagap)
if commands.chosen == 'Speeds':
    chosen_video_stat = video_data[8]
    chosen_stat = copy.deepcopy(forSpeeds)

'''
fig, ax = plt.subplots(1, 1)
ax.hist([i/fps for i in chosen_video_stat.cumul_all.raw if i/fps < 30], histtype='stepfilled', bins = 100, color = 'b', alpha=0.7, label='video data')#, normed=True, histtype='stepfilled', alpha=0.2)
ax.hist([i/simulationStepsPerTimeUnit for i in chosen_stat.distributions[0].raw if i/simulationStepsPerTimeUnit < 30], histtype='stepfilled', bins = 100, color = 'r', alpha=0.5, label='vissim data - 1rst dist')#, normed=True, histtype='stepfilled', alpha=0.2)
ax.legend(loc='best', frameon=False)
plt.show()
import pdb;pdb.set_trace()
''' 
#open report  - output = .fzp files directory
out = open(os.path.join(commands.dirname, 'compare_dist_report.csv'),'w')
   
#compare data
stat_list = [chosen_video_stat.cumul_all.raw]
unpack_dists = analysis.treat_stats_list(chosen_stat)
for i in unpack_dists:
    stat_list.append(i)
stat_list.append(chosen_stat.cumul_all.raw)

raw_mat = analysis.ks_matrix(stat_list)


out.write('legend:\n')
out.write('f0: video data\n')
out.write('f1 to f'+str(len(chosen_stat.distributions))+': vissim file distributions\n')
out.write('f'+str(len(chosen_stat.distributions)+1)+': vissim concat data\n')
out.write('\n')

out.write('___________________________________________________________________\n')
out.write('Kolmolgorov-Smirnov correspondance matrix\n')
out.write('\n')

write.writeInFile(out,['',['f'+str(i) for i in range(0,len(chosen_stat.distributions)+2)]])

for l in xrange(len(raw_mat)):
    write.writeInFile(out,[l,raw_mat[l]], rounding=False)
out.write('\n')

#compare data with selected random functions
#usefull doc: http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kstest.html#scipy.stats.kstest

##Exponential function
##usefull doc: http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.expon.html#scipy.stats.expon
## cdf = 1-e**(-lambda*x); pdf = lambda*e**(-lambda*x)  -- we need to test many lambas since the distribution is unknown
out.write('___________________________________________________________________\n')
out.write('Adequation test with exponential function\n')
out.write('\n')

nbr_test = 40
translate_test = 31
translate = 0
video_best_found = [[],[]]
vissim_dists_best_found = [[],[]]
vissim_cumul_best_found = [[],[]]

for i in xrange(translate_test):
    d_values = []
    p_values = []
    titles = ['']
    ###video
    this_d_line = ['f0']
    this_p_line = ['f0']
    for j in xrange(nbr_test):
        d,p = stats.ks_2samp(chosen_video_stat.cumul_all.raw,stats.expon.rvs(size=1000,scale=j,loc=translate))
        this_d_line.append(d)
        this_p_line.append(p)
        
        if len(video_best_found[0]) <= 5:
            video_best_found[0].append(p); video_best_found[1].append('l:'+str(j)+', t:'+str(translate)) 
        else:
            pos = video_best_found[0].index(min(video_best_found[0]))
            if p > video_best_found[0][pos]:
                video_best_found[0][pos] = p; video_best_found[1][pos] = 'l:'+str(j)+', t:'+str(translate)
            
    d_values.append(this_d_line)
    p_values.append(this_p_line)
    ###distributiond
    for i in xrange(len(chosen_stat.distributions)):
        this_d_line = ['f'+str(i+1)]
        this_p_line = ['f'+str(i+1)]
        for j in xrange(nbr_test):
            d,p = stats.ks_2samp(chosen_stat.distributions[i].raw,stats.expon.rvs(size=1000,scale=j,loc=translate))
            this_d_line.append(d)
            this_p_line.append(p)
            
            if len(vissim_dists_best_found[0]) <= 5:
                vissim_dists_best_found[0].append(p); vissim_dists_best_found[1].append('l:'+str(j)+', t:'+str(translate)) 
            else:
                pos = vissim_dists_best_found[0].index(min(vissim_dists_best_found[0]))
                if p > vissim_dists_best_found[0][pos]:
                    vissim_dists_best_found[0][pos] = p; vissim_dists_best_found[1][pos] = 'd:'+str(i+1)+' l:'+str(j)+', t:'+str(translate)
            
        d_values.append(this_d_line)
        p_values.append(this_p_line)
        
    ###cumul_all
    this_d_line = ['f'+str(len(chosen_stat.distributions)+2)]
    this_p_line = ['f'+str(len(chosen_stat.distributions)+2)]
    for j in xrange(nbr_test):
        d,p = stats.ks_2samp(chosen_stat.cumul_all.raw,stats.expon.rvs(size=1000,scale=j,loc=translate))
        this_d_line.append(d)
        this_p_line.append(p)
        titles.append('lambda='+str(j+1))
        
        if len(vissim_cumul_best_found[0]) <= 5:
            vissim_cumul_best_found[0].append(p); vissim_cumul_best_found[1].append('l:'+str(j)+', t:'+str(translate)) 
        else:
            pos = vissim_cumul_best_found[0].index(min(vissim_cumul_best_found[0]))
            if p > vissim_cumul_best_found[0][pos]:
                vissim_cumul_best_found[0][pos] = p; vissim_cumul_best_found[1][pos] = 'l:'+str(j)+', t:'+str(translate)

    d_values.append(this_d_line)
    p_values.append(this_p_line)
    
    out.write('p_values[lambda = i], translate = '+str(translate)+'\n')
    write.writeInFile(out,titles)
    for line in p_values:
        write.writeInFile(out,line, rounding=False)
    out.write('\n')
    
    out.write('D_values[lambda = i], translate = '+str(translate)+'\n')
    write.writeInFile(out,titles)
    for line in d_values:
        write.writeInFile(out,line, rounding=False)    
    out.write('\n')
            
    translate += 0.1

out.write('best matches [d: distribtion #, l: lambda value, t: translation value]\n')
write.writeInFile(out,['video best','','','vissim dist best','','','vissim cumul best','','',])
write.writeInFile(out,['p','loc','','p','loc','','p','loc',''])
for i in xrange(len(vissim_cumul_best_found[0])):  
    write.writeInFile(out,[video_best_found[0][i],video_best_found[1][i],'',vissim_dists_best_found[0][i],vissim_dists_best_found[1][i],'',vissim_cumul_best_found[0][i],vissim_cumul_best_found[1][i]], rounding=False)     
    
        


#trace graphs  - output = .fzp files directory

#write report  - output = .fzp files directory


