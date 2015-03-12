# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 14:49:46 2015

@author: Laurent
"""
import os, argparse, copy
from scipy import stats

import pvc_write      as write
import pvc_outputs    as outputs
import pvc_calibTools as calibTools
import pvc_csvParse   as csvParse
import pvc_mathTools  as mathTools

def Commands(parser):
    parser.add_argument('-c', '--choose',  choices=['Forward_Gaps','Lane_Change_Gaps','Speeds'],  dest='chosen',  default='Forward_Gaps',          help='Variable to analyse') 
    parser.add_argument('-d', '--dir',     dest='dirname',  default=os.curdir,  help='Directory (Optional: default is current working directory)')
    return parser.parse_args()
    
commands = Commands(argparse.ArgumentParser())

###################################################################################
dirname = r'C:\Users\Laurent\Desktop\vissim files\A13\Calib_GP06001_0to9000\Calibration_Analysis_64\point_'
commands.chosen = 'Forward_Gaps'

simulationStepsPerTimeUnit = 10
warmUpTime = 100

fps = 30

path_to_csv = r'C:\Users\Laurent\Desktop\vissim files\A13\Calib_GP06001_0to9000'
inpxname = 'calib_gp06001_0to9000.inpx'

fullpath = r'C:\Users\Laurent\Desktop\vissim files\A13\Calib_GP06001_0to9000\Calib_GP06001_0to9000.traj'

for dire in xrange(1,2):
    commands.dirname = dirname + str(dire)
    
    print '>>>>>>>>>> Start on '+str(commands.dirname)    +' <<<<<<<<<<<<<<<<<<'
    
    if len([f for f in os.listdir(commands.dirname) if f.endswith('fzp')]) > 0:
        ###################################################################################
        
        
        
        #extracting corridors information for vissim file calculations
        VissimCorridors, trafIntCorridors = csvParse.extractVissimCorridorsFromCSV(path_to_csv, inpxname)
        
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
        main = open(os.path.join(commands.dirname, 'compare_dist_report.csv'),'w')
        expo = open(os.path.join(commands.dirname, 'compare_dist_exponential.csv'),'w')
        #pois = open(os.path.join(commands.dirname, 'compare_dist_poisson.csv'),'w')
        #gamm = open(os.path.join(commands.dirname, 'compare_dist_gamma.csv'),'w')
          
        #compare data
        stat_list = [chosen_video_stat.cumul_all.raw]
        unpack_dists = calibTools.treat_stats_list(chosen_stat)
        for i in unpack_dists:
            stat_list.append(i)
        stat_list.append(chosen_stat.cumul_all.raw)
        
        raw_mat = calibTools.ks_matrix(stat_list)
        
        legend = 'legend:\n f0: video data\n f1 to f'+str(len(chosen_stat.distributions))+': vissim file distributions\n f'+str(len(chosen_stat.distributions)+1)+': vissim concat data\n \n'
        main.write(legend)
        expo.write(legend)
        #pois.write(legend)
        #gamm.write(legend)    
        
        main.write('___________________________________________________________________\n')
        main.write('Kolmolgorov-Smirnov correspondance matrix\n')
        main.write('\n')
        
        write.writeInFile(main,['',['f'+str(i) for i in range(0,len(chosen_stat.distributions)+2)]])
        
        for l in xrange(len(raw_mat)):
            write.writeInFile(main,[l,raw_mat[l]], rounding=False)
        main.write('\n')
        
        #compare data with selected random functions
        #usefull doc: http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kstest.html#scipy.stats.kstest
        
        ##############################################################################################################
        ##Exponential function
        ##usefull doc: http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.expon.html#scipy.stats.expon
        ## cdf = 1-e**(-lambda*x); pdf = lambda*e**(-lambda*x)  -- we need to test many lambas since the distribution is unknown
        main.write('___________________________________________________________________\n')
        main.write('Adequation test with exponential function\n')
        main.write('\n')
        
        nbr_test = 40
        translate_test = 61
        translate = 0
        video_best_found = [[],[]]
        vissim_dists_best_found = [[],[]]
        vissim_cumul_best_found = [[],[]]
        
        test_list = [0.01*i for i in xrange(2,nbr_test+2,2)] + [i for i in xrange(0,nbr_test/2,1)]    
        
        for i in xrange(translate_test):
            d_values = []
            p_values = []
            titles = ['']
            ###video
            this_d_line = ['f0']
            this_p_line = ['f0']
            for j in test_list:
                d,p = stats.ks_2samp(chosen_video_stat.cumul_all.raw,stats.expon.rvs(size=10000,scale=j,loc=translate))
                this_d_line.append(d)
                this_p_line.append(p)
                
                if len(video_best_found[0]) <= 5:
                    video_best_found[0].append(p); video_best_found[1].append('l:1/'+str(j)+', t:'+str(translate)) 
                else:
                    pos = video_best_found[0].index(min(video_best_found[0]))
                    if p > video_best_found[0][pos]:
                        video_best_found[0][pos] = p; video_best_found[1][pos] = 'l:1/'+str(j)+', t:'+str(translate)
                    
            d_values.append(this_d_line)
            p_values.append(this_p_line)
            ###distributiond
            for i in xrange(len(chosen_stat.distributions)):
                this_d_line = ['f'+str(i+1)]
                this_p_line = ['f'+str(i+1)]
                for j in test_list:
                    d,p = stats.ks_2samp(chosen_stat.distributions[i].raw,stats.expon.rvs(size=10000,scale=j,loc=translate))
                    this_d_line.append(d)
                    this_p_line.append(p)
                    
                    if len(vissim_dists_best_found[0]) <= 5:
                        vissim_dists_best_found[0].append(p); vissim_dists_best_found[1].append('l:1/'+str(j)+', t:'+str(translate)) 
                    else:
                        pos = vissim_dists_best_found[0].index(min(vissim_dists_best_found[0]))
                        if p > vissim_dists_best_found[0][pos]:
                            vissim_dists_best_found[0][pos] = p; vissim_dists_best_found[1][pos] = 'd:'+str(i+1)+' l:1/'+str(j)+', t:'+str(translate)
                    
                d_values.append(this_d_line)
                p_values.append(this_p_line)
                
            ###cumul_all
            this_d_line = ['f'+str(len(chosen_stat.distributions)+1)]
            this_p_line = ['f'+str(len(chosen_stat.distributions)+1)]
            for j in test_list:
                d,p = stats.ks_2samp(chosen_stat.cumul_all.raw,stats.expon.rvs(size=10000,scale=j,loc=translate))
                this_d_line.append(d)
                this_p_line.append(p)
                titles.append('lambda=1/'+str(j))
                
                if len(vissim_cumul_best_found[0]) <= 5:
                    vissim_cumul_best_found[0].append(p); vissim_cumul_best_found[1].append('l:1/'+str(j)+', t:'+str(translate)) 
                else:
                    pos = vissim_cumul_best_found[0].index(min(vissim_cumul_best_found[0]))
                    if p > vissim_cumul_best_found[0][pos]:
                        vissim_cumul_best_found[0][pos] = p; vissim_cumul_best_found[1][pos] = 'l:1/'+str(j)+', t:'+str(translate)
        
            d_values.append(this_d_line)
            p_values.append(this_p_line)
            
            expo.write('p_values[lambda = 1/i], translate = '+str(translate)+'\n')
            write.writeInFile(expo,titles)
            for line in p_values:
                write.writeInFile(expo,line, rounding=False)
            expo.write('\n')
            
            expo.write('D_values[lambda = 1/i], translate = '+str(translate)+'\n')
            write.writeInFile(expo,titles)
            for line in d_values:
                write.writeInFile(expo,line, rounding=False)    
                    
            translate += 0.1
        
        sorted_video_best_found_p, sorted_video_best_found_loc = mathTools.sort2lists(video_best_found[0], video_best_found[1], ascending_order=False)
        sorted_vissim_dists_best_found_p, sorted_vissim_dists_best_found_loc = mathTools.sort2lists(vissim_dists_best_found[0], vissim_dists_best_found[1], ascending_order=False)
        sorted_vissim_cumul_best_found_p, sorted_vissim_cumul_best_found_loc = mathTools.sort2lists(vissim_cumul_best_found[0], vissim_cumul_best_found[1], ascending_order=False)
        main.write('best matches [d: distribtion #, l: lambda value, t: translation value]\n')
        write.writeInFile(main,['video best','','','vissim dist best','','','vissim cumul best','','',])
        write.writeInFile(main,['p','loc','','p','loc','','p','loc',''])
        for i in xrange(len(vissim_cumul_best_found[0])):  
            write.writeInFile(main,[sorted_video_best_found_p[i],sorted_video_best_found_loc[i],'',sorted_vissim_dists_best_found_p[i],sorted_vissim_dists_best_found_loc[i],'',sorted_vissim_cumul_best_found_p[i],sorted_vissim_cumul_best_found_loc[i]], rounding=False)     
        main.write('\n')
                
        '''
        ##############################################################################################################
        ##Poisson function
        ##usefull doc: http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.expon.html#scipy.stats.expon
        ## cdf = 1-e**(-lambda*x); pdf = lambda*e**(-lambda*x)  -- we need to test many lambas since the distribution is unknown
        main.write('___________________________________________________________________\n')
        main.write('Adequation test with Poisson function\n')
        main.write('\n')
        
        nbr_test = 20
        translate_test = 61
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
                d,p = stats.ks_2samp(chosen_video_stat.cumul_all.raw,stats.poisson.rvs(size=10000,mu=float(j+1)/2,loc=translate))
                this_d_line.append(d)
                this_p_line.append(p)
                
                if len(video_best_found[0]) <= 5:
                    video_best_found[0].append(p); video_best_found[1].append('mu:'+str(float(j+1)/2)+', t:'+str(translate)) 
                else:
                    pos = video_best_found[0].index(min(video_best_found[0]))
                    if p > video_best_found[0][pos]:
                        video_best_found[0][pos] = p; video_best_found[1][pos] = 'mu:'+str(float(j+1)/2)+', t:'+str(translate)
                    
            d_values.append(this_d_line)
            p_values.append(this_p_line)
            ###distributiond
            for i in xrange(len(chosen_stat.distributions)):
                this_d_line = ['f'+str(i+1)]
                this_p_line = ['f'+str(i+1)]
                for j in xrange(nbr_test):
                    d,p = stats.ks_2samp(chosen_stat.distributions[i].raw,stats.poisson.rvs(size=10000,mu=float(j+1)/2,loc=translate))
                    this_d_line.append(d)
                    this_p_line.append(p)
                    
                    if len(vissim_dists_best_found[0]) <= 5:
                        vissim_dists_best_found[0].append(p); vissim_dists_best_found[1].append('mu:'+str(float(j+1)/2)+', t:'+str(translate)) 
                    else:
                        pos = vissim_dists_best_found[0].index(min(vissim_dists_best_found[0]))
                        if p > vissim_dists_best_found[0][pos]:
                            vissim_dists_best_found[0][pos] = p; vissim_dists_best_found[1][pos] = 'd:'+str(i+1)+' mu:'+str(float(j+1)/2)+', t:'+str(translate)
                    
                d_values.append(this_d_line)
                p_values.append(this_p_line)
                
            ###cumul_all
            this_d_line = ['f'+str(len(chosen_stat.distributions)+2)]
            this_p_line = ['f'+str(len(chosen_stat.distributions)+2)]
            for j in xrange(nbr_test):
                d,p = stats.ks_2samp(chosen_stat.cumul_all.raw,stats.poisson.rvs(size=10000,mu=float(j+1)/2,loc=translate))
                this_d_line.append(d)
                this_p_line.append(p)
                titles.append('lambda='+str(float(j+2)/2))
                
                if len(vissim_cumul_best_found[0]) <= 5:
                    vissim_cumul_best_found[0].append(p); vissim_cumul_best_found[1].append('mu:'+str(float(j+1)/2)+', t:'+str(translate)) 
                else:
                    pos = vissim_cumul_best_found[0].index(min(vissim_cumul_best_found[0]))
                    if p > vissim_cumul_best_found[0][pos]:
                        vissim_cumul_best_found[0][pos] = p; vissim_cumul_best_found[1][pos] = 'mu:'+str(float(j+1)/2)+', t:'+str(translate)
        
            d_values.append(this_d_line)
            p_values.append(this_p_line)
            
            pois.write('p_values[lambda = i/2], translate = '+str(translate)+'\n')
            write.writeInFile(pois,titles)
            for line in p_values:
                write.writeInFile(pois,line, rounding=False)
            pois.write('\n')
            
            pois.write('D_values[lambda = i/2], translate = '+str(translate)+'\n')
            write.writeInFile(pois,titles)
            for line in d_values:
                write.writeInFile(pois,line, rounding=False)    
                    
            translate += 0.1
        
        sorted_video_best_found_p, sorted_video_best_found_loc = mathTools.sort2lists(video_best_found[0], video_best_found[1], ascending_order=False)
        sorted_vissim_dists_best_found_p, sorted_vissim_dists_best_found_loc = mathTools.sort2lists(vissim_dists_best_found[0], vissim_dists_best_found[1], ascending_order=False)
        sorted_vissim_cumul_best_found_p, sorted_vissim_cumul_best_found_loc = mathTools.sort2lists(vissim_cumul_best_found[0], vissim_cumul_best_found[1], ascending_order=False)
        main.write('best matches [d: distribtion #, l: lambda value, t: translation value]\n')
        write.writeInFile(main,['video best','','','vissim dist best','','','vissim cumul best','','',])
        write.writeInFile(main,['p','loc','','p','loc','','p','loc',''])
        for i in xrange(len(vissim_cumul_best_found[0])):  
            write.writeInFile(main,[sorted_video_best_found_p[i],sorted_video_best_found_loc[i],'',sorted_vissim_dists_best_found_p[i],sorted_vissim_dists_best_found_loc[i],'',sorted_vissim_cumul_best_found_p[i],sorted_vissim_cumul_best_found_loc[i]], rounding=False)     
        main.write('\n')
            
        
        ##############################################################################################################
        ##Gamma function
        ##usefull doc: http://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.gamma.html#scipy.stats.gamma
        ## we need to test many lambas and a since the distribution is unknown
        main.write('___________________________________________________________________\n')
        main.write('Adequation test with gamma function\n')
        main.write('\n')
        
        nbr_test = 20
        translate_test = 31
        translate = 0
        a_tests = 16
        a = 0.1
        video_best_found = [[],[]]
        vissim_dists_best_found = [[],[]]
        vissim_cumul_best_found = [[],[]]
        
        for a_test in xrange(a_tests):
            for i in xrange(translate_test):
                d_values = []
                p_values = []
                titles = ['']
                ###video
                this_d_line = ['f0']
                this_p_line = ['f0']
                for j in xrange(nbr_test):
                    d,p = stats.ks_2samp(chosen_video_stat.cumul_all.raw,stats.gamma.rvs(a,size=10000,scale=j,loc=translate))
                    this_d_line.append(d)
                    this_p_line.append(p)
                    
                    if len(video_best_found[0]) <= 5:
                        video_best_found[0].append(p); video_best_found[1].append('l:1/'+str(j)+', a:'+str(a)+'t:'+str(translate)) 
                    else:
                        pos = video_best_found[0].index(min(video_best_found[0]))
                        if p > video_best_found[0][pos]:
                            video_best_found[0][pos] = p; video_best_found[1][pos] = 'l:1/'+str(j)+', a:'+str(a)+'t:'+str(translate)
                        
                d_values.append(this_d_line)
                p_values.append(this_p_line)
                ###distributiond
                for i in xrange(len(chosen_stat.distributions)):
                    this_d_line = ['f'+str(i+1)]
                    this_p_line = ['f'+str(i+1)]
                    for j in xrange(nbr_test):
                        d,p = stats.ks_2samp(chosen_stat.distributions[i].raw,stats.gamma.rvs(a,size=10000,scale=j,loc=translate))
                        this_d_line.append(d)
                        this_p_line.append(p)
                        
                        if len(vissim_dists_best_found[0]) <= 5:
                            vissim_dists_best_found[0].append(p); vissim_dists_best_found[1].append('l:1/'+str(j)+', a:'+str(a)+'t:'+str(translate)) 
                        else:
                            pos = vissim_dists_best_found[0].index(min(vissim_dists_best_found[0]))
                            if p > vissim_dists_best_found[0][pos]:
                                vissim_dists_best_found[0][pos] = p; vissim_dists_best_found[1][pos] = 'd:'+str(i+1)+' l:1/'+str(j)+', a:'+str(a)+'t:'+str(translate)
                        
                    d_values.append(this_d_line)
                    p_values.append(this_p_line)
                    
                ###cumul_all
                this_d_line = ['f'+str(len(chosen_stat.distributions)+2)]
                this_p_line = ['f'+str(len(chosen_stat.distributions)+2)]
                for j in xrange(nbr_test):
                    d,p = stats.ks_2samp(chosen_stat.cumul_all.raw,stats.gamma.rvs(a,size=10000,scale=j,loc=translate))
                    this_d_line.append(d)
                    this_p_line.append(p)
                    titles.append('lambda=1/'+str(j+1))
                    
                    if len(vissim_cumul_best_found[0]) <= 5:
                        vissim_cumul_best_found[0].append(p); vissim_cumul_best_found[1].append('l:1/'+str(j)+', a:'+str(a)+'t:'+str(translate)) 
                    else:
                        pos = vissim_cumul_best_found[0].index(min(vissim_cumul_best_found[0]))
                        if p > vissim_cumul_best_found[0][pos]:
                            vissim_cumul_best_found[0][pos] = p; vissim_cumul_best_found[1][pos] = 'l:1/'+str(j)+', a:'+str(a)+'t:'+str(translate)
            
                d_values.append(this_d_line)
                p_values.append(this_p_line)
                
                gamm.write('p_values[lambda = 1/i], a = '+str(a)+'translate = '+str(translate)+'\n')
                write.writeInFile(gamm,titles)
                for line in p_values:
                    write.writeInFile(gamm,line, rounding=False)
                gamm.write('\n')
                
                gamm.write('D_values[lambda = 1/i], a = '+str(a)+'translate = '+str(translate)+'\n')
                write.writeInFile(gamm,titles)
                for line in d_values:
                    write.writeInFile(gamm,line, rounding=False)    
                        
                translate += 0.1
            a_tests += 0.1
        
        sorted_video_best_found_p, sorted_video_best_found_loc = mathTools.sort2lists(video_best_found[0], video_best_found[1], ascending_order=False)
        sorted_vissim_dists_best_found_p, sorted_vissim_dists_best_found_loc = mathTools.sort2lists(vissim_dists_best_found[0], vissim_dists_best_found[1], ascending_order=False)
        sorted_vissim_cumul_best_found_p, sorted_vissim_cumul_best_found_loc = mathTools.sort2lists(vissim_cumul_best_found[0], vissim_cumul_best_found[1], ascending_order=False)
        main.write('best matches [a: gamma shape parameter, d: distribtion #, l: lambda value, t: translation value]\n')
        write.writeInFile(main,['video best','','','vissim dist best','','','vissim cumul best','','',])
        write.writeInFile(main,['p','loc','','p','loc','','p','loc',''])
        for i in xrange(len(vissim_cumul_best_found[0])):  
            write.writeInFile(main,[sorted_video_best_found_p[i],sorted_video_best_found_loc[i],'',sorted_vissim_dists_best_found_p[i],sorted_vissim_dists_best_found_loc[i],'',sorted_vissim_cumul_best_found_p[i],sorted_vissim_cumul_best_found_loc[i]], rounding=False)     
        main.write('\n')
        '''
        
        
                
        main.close()
        expo.close()
        #gamm.close()
        #pois.close()
        
        #trace graphs  - output = .fzp files directory
        
        #write report  - output = .fzp files directory


