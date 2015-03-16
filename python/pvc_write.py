# -*- coding: utf-8 -*-
'''
Created on Thu Jul 03 11:32:08 2014

@author: Laurent
'''

##################
# Import Libraries
##################
#Native
import os, time, shutil, re, traceback
import matplotlib.pyplot as plt
import matplotlib.pylab as plb
from matplotlib import rcParams
import numpy as np
from scipy import stats
import cPickle as pickle

#Internal
import pvc_configure as configure
import pvc_workers   as workers
import pvc_mathTools as mathTools

##################
# Folder tools
##################
def createSubFolder(folderpath, filename, Archives = True):
    '''Creates a folder named 'filename'
    
       If such a folder already exists at the designated location and Archives = True, creates a subfolder 
       named 'Archives' and another subfolder named 'yyyymmdd_hhmmss' and moves all files in the folder 
       to that subfolder'''
       
    newfolderpath = folderpath

    try: 
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
        
        else:
            if Archives is True:
                if os.listdir(folderpath) != []:
                    print '   =================================='                    
                    print '     Folder with the name ' ' + filename + ' ' already exist!'
                    print '   Moving all current files to a subfolder named "Archives" '
                    print '   ==================================' 
                     
                    if not os.path.exists(os.path.join(folderpath, 'Archives')):
                        os.makedirs(os.path.join(folderpath, 'Archives'))
                        
                    datename = str(time.localtime().tm_year)+str(time.localtime().tm_mon).zfill(2)  + str(time.localtime().tm_mday).zfill(2) + '_' + str(time.localtime().tm_hour) + 'h' + str(time.localtime().tm_min) + 'm' + str(time.localtime().tm_sec) + 's' 
                    newfolderpath = os.path.join(folderpath, 'Archives', datename)
                    os.makedirs(newfolderpath)        
                    for files in os.listdir(folderpath):
                        if files != 'Archives' and not files.endswith('inpx'):
                             shutil.move(os.path.join(folderpath, files),os.path.join(newfolderpath, files) )
    except:
        newfolderpath = False
        
    return newfolderpath
    
def defineName(dirname, TypeOfAnalysis):
    '''Finds the folders named after the analysis type and find the greatest increment'''
    last_num = 0
    
    past_analysis  = [f for f in os.listdir(dirname) if 'Analysis' in f]
    if past_analysis != []:
        for f in past_analysis:
            striped = f.strip('.csv')
            if TypeOfAnalysis in f:
                try:
                    num = int(striped.split('_')[-1])
                    if num > last_num: last_num = num
                except:
                    pass
    
    last_num += 1  
    filename = TypeOfAnalysis + '_Analysis_' + str(last_num)
    
    return filename, last_num

def findCalibName(dirname, name = 'point'):
    '''Finds the folders named name_x and find the greatest increment x'''
    last_num = 0
    
    past_analysis  = [f for f in os.listdir(dirname) if name in f]
    if past_analysis != []:
        for f in past_analysis:
            striped = f.strip('.csv')
            num = int(striped.split('_')[-1])
            if num > last_num: last_num = num
    
    last_num += 1  
    filename = name+'_' + str(last_num)
    
    return filename

################################ 
#        Calibration history functions       
################################
class mean_delta:
    def __init__(self,lists):
        try:
            self.mean = float(lists[0])
        except:
            self.mean = 'nan'
        try:    
            self.delta = float(lists[1])
        except:
            self.mean = 'nan'
        
class Content:
    def __init__(self,num,seeds,point,oppLCcount,manLCcount,flow,forFMgaps,oppLCagaps,oppLCbgaps,manLCagaps,manLCbgaps,forSpeeds,fout):
        self.num        = int(num)
        self.seeds      = [int(i) for i in seeds]
        self.point      = [float(i) for i in point]
        self.oppLCcount = mean_delta(oppLCcount)
        self.manLCcount = mean_delta(manLCcount)
        self.flow       = mean_delta(flow)
        self.forFMgaps  = mean_delta(forFMgaps)
        self.oppLCagaps = mean_delta(oppLCagaps)
        self.oppLCbgaps = mean_delta(oppLCbgaps)
        self.manLCagaps = mean_delta(manLCagaps)
        self.manLCbgaps = mean_delta(manLCbgaps)
        self.forSpeeds  = mean_delta(forSpeeds)
        try:
            self.fout   = float(fout[0])
            self.C_0    = float(fout[1])
            self.C_1    = float(fout[2])
            self.C_2    = float(fout[3])
        except:
            self.fout   = fout[0]
            self.C_0    = 'nan'
            self.C_1    = 'nan'
            self.C_2    = 'nan'
            
class History:
    '''stores all history related functions for easy access'''
    @staticmethod
    def find_last_number(filename):
        '''finds the number of the last recorded evaluation and returns the number of the new evaluation'''
        last_num = 0
        with open(os.path.join(os.getcwd(),filename), 'r') as hist:
            for l in hist:
                if l.strip() != '' and l.startswith('#') is False:
                    last_num += 1
        return last_num + 1

    @staticmethod
    def read_history(filename):
        '''reads the history '''
        history = {}
        with open(os.path.join(os.getcwd(),filename), 'r') as hist:           
            for l in hist:
                if l.strip() != '' and l.startswith('#') is False:
                    if l.strip().split('\t|\t')[0] != 'Itt':
                        types = l.strip().split('\t|\t')
                        if types[-1].split('\t')[0] == 'crashed':
                            stats_data = ['nan' for i in xrange(19)]
                        else:
                            stats_data = types[3].strip('*').split('\t')
                        history[types[0]] = Content(types[0].strip('\t'),types[1].split('\t'),types[2].split('\t'),[stats_data[0], stats_data[1]],[stats_data[2], stats_data[3]],[stats_data[4], stats_data[5]],[stats_data[7], stats_data[8]],[stats_data[9], stats_data[10]],[stats_data[11], stats_data[12]],[stats_data[13], stats_data[14]],[stats_data[15], stats_data[16]],[stats_data[17], stats_data[18]], types[4].split('\t'))
        return history.values()
        
    @staticmethod
    def create_history(dirname, filename, nbr_seeds, networks):
        with open(os.path.join(dirname, filename), 'w') as hist:
            #first line:
            hist.write('Itt\t|\t')
            for net in xrange(len(networks)):
                for seed in xrange(nbr_seeds):
                    hist.write('Seeds, net'+str(seed+1)+'\t')
                    for i in xrange(nbr_seeds-1):
                       hist.write('\t') 
            hist.write('|\tpoint\t|\t')   
            for net in xrange(len(networks)):
                for comp in xrange(len(networks[net].traj_paths)):
                    hist.write('Network_'+str(net)+'_Video_'+str(comp)+'\t')
                    for i in xrange(18):
                        hist.write('\t')
                    hist.write('|\t')
            #2nd line:
            hist.write('#\t|\t')
            for net in xrange(len(networks)):
                for seed in xrange(nbr_seeds):
                    hist.write('Seed_'+str(seed+1)+'\t')
            hist.write('|\tpoint\t|\t')   
            for net in xrange(len(networks)):
                for comp in xrange(len(networks[net].traj_paths)):
                    hist.write('oppLCcount (mean)\t oppLCcount (delta)\t')
                    hist.write('manLCcount (mean)\t manLCcount (delta)\t')
                    hist.write('flow (mean)\t flow (delta)\t')  
                    hist.write('-\t')                    
                    hist.write('forFMgap (mean)\t forFMgap (ks_d_stat)\t')
                    hist.write('oppLCagap (mean)\t oppLCagap (ks_d_stata)\t')
                    hist.write('oppLCbgap (mean)\t oppLCbgap (ks_d_stat)\t')
                    hist.write('manLCagap (mean)\t manLCagap (ks_d_stat)\t')
                    hist.write('manLCbgap (mean)\t manLCbgap (ks_d_stat)\t')
                    hist.write('forSpeeds (mean)\t forSpeeds (ks_d_stat)\t')
                    hist.write('|\t')
    		
            hist.write('fout\tC0\tC1\tC2\n')
            
    @staticmethod
    def write_history(last_num, seeds, points, networks, fout,  dirname, filename):   
        with open(os.path.join(dirname, filename), 'a') as hist:
            hist.write(str(last_num)+'\t')
            hist.write('|\t')

            #seeds
            for seed in seeds:
                hist.write(str(seed)+'\t')
            hist.write('|\t')
    
            #tried point
            for p in points:
                hist.write(str(p)+'\t')
            hist.write('|\t')
    
            #secondary comparaison
            for net in xrange(len(networks)):
                for comp in networks[net].videoComparison:
                    variables = mathTools.ToOneList(list(comp))
                    for v in xrange(len(variables)):
                        if v == 6:
                            hist.write('-\t')
                        hist.write(str(variables[v]) +'\t')
                    hist.write('|\t')
    
            #fout
            for f in fout:
                hist.write(str(f)+'\t')
            hist.write('\n')
            
################################ 
#        NOMAD handling functions       
################################                     
class NOMAD:
    '''Stores all NOMAD related functions for easy access'''
    
    @staticmethod
    def read_from_NOMAD(input_name):
        '''Get input point from NOMAD for current evaluation'''
        points = []
        with open(input_name, 'r') as f:
            for l in f:
                inter = l.strip().replace('\t',' ').split(' ')
                for i in inter:
                    points.append(float(i))
        return points
        
    @staticmethod
    def create_NOMAD_params(filepath, variables, starting_point = [], biobj = False):
        '''Writes a default parameter file... no fancy options included'''
        num_dim = str(len(variables))
        X0 = ' '
        LB = ' '
        UB = ' '
        IT = ' '
        if starting_point != []:
            for p in starting_point:
                X0 += str(p) + ' '
        for var in variables:
            if var.type != 'reject':
                if starting_point == []:
                    X0 += str(var.desired_value) + ' '
                if var.vissim_min is not None:
                    LB += str(var.desired_min) + ' '
                else:
                    LB += '- '
                if var.vissim_max is not None:
                    UB += str(var.desired_max) + ' '
                else:
                    UB += '- '
                if var.type == 'R':
                    IT += 'R '
                elif var.type == 'I':
                    IT += 'I '
                else:
                    IT += 'B '
                        
        with open(filepath,'w') as param:
            param.write('DIMENSION      '+num_dim+'					                  # number of variables\n'
                        '\n'
                        'BB_EXE        \'$python calib.py\'                      # blackbox program\n'
                        'BB_INPUT_TYPE  (' + IT + ')\n')
            if biobj is False:
                param.write('BB_OUTPUT_TYPE OBJ EB EB EB\n')
            else:
                param.write('BB_OUTPUT_TYPE OBJ OBJ EB EB EB\n')
            param.write('\n'
                        'X0             (' + X0 + ')    # starting point\n'
                        '\n'
                        'LOWER_BOUND    (' + LB + ')\n'
                        'UPPER_BOUND    (' + UB + ')\n'
                        '\n'
                        '\n'
                        'MAX_BB_EVAL    1000             				# the algorithm terminates when\n'
                        '                              				# 100 black-box evaluations have\n'
                        '                              				# been made\n'
                        'STATS_FILE	NOMAD_history.txt BBE OBJ ( SOL )')
    
    @staticmethod
    def add_new_line(current_lines, l):
        try:
            if current_lines[l+1].strip() == '':
                return ''
            else:
                return '\n'
        except:
            return '\n'
            
    @staticmethod         
    def verify_params(filepath, variables, starting_point = [], biobj = False):
        '''verifies the param file for Dimensions, X0, LB, and UB lenght
           Sets X0 as default parameters unless a point is specified as a list
           in starting_point'''
        
        #note: Flag = [ 0    0 = DIMENSION       value   is correct, 1 = DIMENSION       value   needs to be corrected
        #               1    0 = BB_OUTPUT_TYPE  value   is correct, 1 = BB_OUTPUT_TYPE  value   needs to be corrected
        #               2    0 = DIMENSION       line    is present, 1 = STATS_FILE      line    has to be added
        #               3    0 = BB_EXE          line    is present, 1 = BB_EXE          lien    has to be added  
        #               4    0 = BB_INPUT_TYPE   line    is present, 1 = STATS_FILE      line    has to be added
        #               5    0 = BB_OUTPUT_TYPE  line    is present, 1 = STATS_FILE      line    has to be added
        #               6    0 = X0              line    is present, 1 = STATS_FILE      line    has to be added
        #               7    0 = LOWER_BOUND     line    is present, 1 = STATS_FILE      line    has to be added
        #               8    0 = UPPER_BOUND     line    is present, 1 = STATS_FILE      line    has to be added
        #               9    0 = MAX_BB_EVAL     line    is present, 1 = MAX_BB_EVAL     line    has to be added
        #              10    0 = STATS_FILE      line    is present, 1 = STATS_FILE      line    has to be added        
        #                 ]
        
        if os.path.isfile(filepath):
            flag = [0,0,1,1,1,1,1,1,1,1,1]    
            current_lines = []    
            with open(filepath,'r') as current:
                for l in current:
                    current_lines.append(l)
            
            num_dim = str(len(variables))
            
            for l in xrange(len(current_lines)):
                if 'DIMENSION' in current_lines[l]:
                    flag[2] = 0
                    if int(re.sub('[a-z,A-Z,\t,\s,#,$,]', ' ', current_lines[l].strip())) != num_dim:
                        flag[0] = 1
                        current_lines[l] = 'DIMENSION      '+num_dim+'					                  # number of variables\n'
                
                elif 'BB_OUTPUT_TYPE' in current_lines[l]:
                    flag[5] = 0
                    objcount = current_lines[l].count('OBJ')
                    EBcount = current_lines[l].count('EB')
                    if biobj is False and (objcount != 1 or EBcount != 3):
                        flag[1] = 1
                        
                    if biobj is True and (objcount != 2 or EBcount != 3):
                        flag[1] = 1
                
                elif 'BB_EXE' in current_lines[l]:
                    flag[3] = 0
                                                      
                elif 'BB_INPUT_TYPE' in current_lines[l]:
                    flag[4] = 0
                    
                elif 'X0' in current_lines[l]:
                    flag[6] = 0

                elif 'LOWER_BOUND' in current_lines[l]:
                    flag[7] = 0
                    
                elif 'UPPER_BOUND' in current_lines[l]:
                    flag[8] = 0
                    
                elif 'MAX_BB_EVAL' in current_lines[l]:
                    flag[9] = 0
                    
                elif 'STATS_FILE' in current_lines[l]:
                    flag[10] = 0

            #Adding missing lines
            if flag[2] == 1:
                add = NOMAD.add_new_line(current_lines, l)
                current_lines = ['DIMENSION      '+num_dim+add] + current_lines
                flag[0] = 1
                
            if flag[3] == 1:
                for l in xrange(len(current_lines)):
                    if 'DIMENSION' in current_lines[l]: 
                          Start = current_lines[0:l+1]
                          Mid   = ['\n']+['BB_EXE        \'$python calib.py\'']
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End

            if flag[4] == 1:
                for l in xrange(len(current_lines)):
                    if 'BB_EXE' in current_lines[l]:
                          add = NOMAD.add_new_line(current_lines, l)
                          Start = current_lines[0:l+1]
                          Mid   = ['\n']+['BB_INPUT_TYPE'+add]
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End
                          
            if flag[5] == 1:
                for l in xrange(len(current_lines)):
                    if 'BB_INPUT_TYPE' in current_lines[l]: 
                          add = NOMAD.add_new_line(current_lines, l)
                          Start = current_lines[0:l+1]
                          Mid   = ['BB_OUTPUT_TYPE'+add]
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End
                          flag[1] = 1

            if flag[6] == 1:
                for l in xrange(len(current_lines)):
                    if 'BB_OUTPUT_TYPE' in current_lines[l]:
                          add = NOMAD.add_new_line(current_lines, l)                              
                          Start = current_lines[0:l+1]
                          Mid   = ['\n']+['\nX0'+add]
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End
                          flag[0] = 1

            if flag[7] == 1:
                for l in xrange(len(current_lines)):
                    if 'X0' in current_lines[l]:                               
                          Start = current_lines[0:l+1]
                          Mid   = ['\n']+['\nLOWER_BOUND']
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End
                          flag[0] = 1

            if flag[8] == 1:
                for l in xrange(len(current_lines)):
                    if 'LOWER_BOUND' in current_lines[l]:
                          add = NOMAD.add_new_line(current_lines, l)
                          Start = current_lines[0:l+1]
                          Mid   = ['\nUPPER_BOUND'+add]
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End
                          flag[0] = 1
                          
            if flag[9] == 1:
                for l in xrange(len(current_lines)):
                    if 'UPPER_BOUND' in current_lines[l]:
                          add = NOMAD.add_new_line(current_lines, l)
                          Start = current_lines[0:l+1]
                          Mid   = ['\n']+['\nMAX_BB_EVAL    1000'+add]
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End
            
            if flag[10] == 1:
                for l in xrange(len(current_lines)):
                    if 'MAX_BB_EVAL' in current_lines[l]:
                          Start = current_lines[0:l+1]
                          Mid   = ['\n']+['\nSTATS_FILE   NOMAD_history.txt BBE OBJ ( SOL )']
                          End   = current_lines[l+1:]
                          current_lines = Start + Mid + End

            #correcting outputs
            if flag[1] == 1:
                for l in xrange(len(current_lines)):
                    if 'BB_OUTPUT_TYPE' in current_lines[l]:
                        if biobj is False:
                            current_lines[l] = 'BB_OUTPUT_TYPE OBJ EB EB EB\n'
                        if biobj is True:
                            current_lines[l] = 'BB_OUTPUT_TYPE OBJ OBJ EB EB EB\n'
                    
            #correcting x0, lower_bounds and upper_bounds lines  
            if flag[0] == 1:
                X0 = ' '
                LB = ' '
                UB = ' '
                IT = ' '
                if starting_point != []:
                    for p in starting_point:
                        X0 += str(p) + ' '
                for var in variables:
                    if var.type != 'reject':                        #automatic rejection of boolean values.  
                        if starting_point == []:                    #please run a calibration for each state
                            X0 += str(var.desired_value) + ' '      #(true/false) of the variable
                        if var.desired_min is not None:
                            LB += str(var.desired_min) + ' '
                        else:
                            LB += '- '
                        if var.desired_max is not None:
                            UB += str(var.desired_max) + ' '
                        else:
                            UB += '- '
                        if var.type == 'R':
                            IT += 'R '
                        elif var.type == 'I':
                            IT += 'I '
                        else:
                            IT += 'B '
            
                for l in xrange(len(current_lines)):
                    if 'X0' in current_lines[l]:
                        current_lines[l] = 'X0             (' + X0 + ')\n'
                    elif 'LOWER_BOUND' in current_lines[l]:
                        current_lines[l] = 'LOWER_BOUND    (' + LB + ')\n'
                    elif 'UPPER_BOUND' in current_lines[l]:
                        current_lines[l] = 'UPPER_BOUND    (' + UB + ')\n'
                    elif 'BB_INPUT_TYPE' in current_lines[l]:
                        current_lines[l] = 'BB_INPUT_TYPE  (' + IT + ')\n'
    
            with open(filepath,'w') as new:
                for line in current_lines:
                    new.write(line)
        else:
            print 'No parameter file found for NOMAD at the specified path. Creating default parameter file'
            NOMAD.create_NOMAD_params(filepath, variables, starting_point, biobj)
    
    @staticmethod
    def set_BB_path(filepath, BB_fullpath):
        '''Updates the Black box path NOMAD will try to use'''
        current_lines = []    
        with open(filepath,'r') as current:
            for l in current:
                current_lines.append(l)
        
        for l in xrange(len(current_lines)):
            if 'BB_EXE' in current_lines[l]:
                current_lines[l] = 'BB_EXE        \'$python ' + str(BB_fullpath) + '\'\n'

        with open(filepath,'w') as new:
            for line in current_lines:
                new.write(line)
                
    @staticmethod
    def set_max_eval(filepath, max_eval):
        '''Updates the number of evaluations NOMAD try at most run before stoping'''
        current_lines = []    
        with open(filepath,'r') as current:
            for l in current:
                current_lines.append(l)
        
        for l in xrange(len(current_lines)):
            if 'MAX_BB_EVAL' in current_lines[l]:
                current_lines[l] = 'MAX_BB_EVAL    ' + str(max_eval) +'\n'

        with open(filepath,'w') as new:
            for line in current_lines:
                new.write(line)
            
################################ 
#        Serialized data files     
################################    
def write_traj(depositpath,name,opp_LC_count,man_LC_count,flow,forward_gaps,opp_LC_agaps,opp_LC_bgaps,man_LC_agaps,man_LC_bgaps,forwar_speed):
    '''dumps data into a file named name.traj in the folder provided in depositpath'''    
    with open(os.path.join(depositpath, name + '.traj'), 'wb') as output:       
        Version = configure.Version()     
        pickle.dump(Version,      output, protocol=2)
        pickle.dump(opp_LC_count, output, protocol=2)
        pickle.dump(man_LC_count, output, protocol=2)
        pickle.dump(flow,         output, protocol=2)
        pickle.dump(forward_gaps, output, protocol=2)
        pickle.dump(opp_LC_agaps, output, protocol=2)
        pickle.dump(opp_LC_bgaps, output, protocol=2)
        pickle.dump(man_LC_agaps, output, protocol=2)
        pickle.dump(man_LC_bgaps, output, protocol=2)
        pickle.dump(forwar_speed, output, protocol=2)

def load_traj(fullpath):
    '''loads data from the traj file provided in full path
    full path must end with \name.traj'''
    with open(fullpath, 'rb') as input_file:
        version      = pickle.load(input_file)
        opp_LC_count = pickle.load(input_file)
        man_LC_count = pickle.load(input_file)
        flow         = pickle.load(input_file)
        forward_gaps = pickle.load(input_file)
        opp_LC_agaps = pickle.load(input_file)
        opp_LC_bgaps = pickle.load(input_file)
        man_LC_agaps = pickle.load(input_file)
        man_LC_bgaps = pickle.load(input_file)
        forwar_speed = pickle.load(input_file)
        
    if configure.Version.verify_data_version(version):
        return [opp_LC_count, man_LC_count, flow, forward_gaps, opp_LC_agaps, opp_LC_bgaps, man_LC_agaps, man_LC_bgaps, forwar_speed]
    else:
        return ['TrajVersionError']

def write_calib(working_path, parameters, variables, networks):
    with open(os.path.join(working_path,'pvcdata.calib'), 'wb') as trans:
        pickle.dump(parameters, trans, protocol=2)
        pickle.dump(variables, trans, protocol=2)
        pickle.dump(networks, trans, protocol=2)

def load_calib():
    '''loads pvcdata.calib''' 
    with open(os.path.join(os.getcwd(),'pvcdata.calib'), 'rb') as input_file:
        parameters   = pickle.load(input_file)
        variables    = pickle.load(input_file)
        networks     = pickle.load(input_file)

    return parameters, variables, networks
    
##################
# Report tools
##################    
def writeSensitivityHeader(dirname, variables, TypeOfAnalysis, first_seed, nbr_runs, warmUpTime, desiredSimulatedTime, Inpxname, values = None, multiProcTempFile = False):
    '''writes the header. For sensitivity analysis, the header has 19 lines'''
    
    if multiProcTempFile is False:
        name, last_num = defineName(dirname, TypeOfAnalysis) 
        subdirname = createSubFolder(os.path.join(dirname,name), name, Archives = False)
        filename = '{}/'+ name + '.csv'
    else:
        subdirname = dirname
        filename = '{}/' + multiProcTempFile + '.csv'
        last_num = int(multiProcTempFile.split('_')[2])
    
    #header writing
    out = open(filename.format(subdirname), 'w')
    out.write('Vissim filename: ' + str(Inpxname) + '\n')
    out.write('Analysis number: ' + str(last_num) + '\n')
    out.write('Type of analysis: ' + str(TypeOfAnalysis) + '\n')
    if TypeOfAnalysis != 'Student':
        out.write('Number of runs per tested variables: ' + str(nbr_runs) + '\n')  
    out.write('First seed: ' + str(first_seed) + '      (increment: 1) \n')       
    out.write('Simulation lenght: ' + str(desiredSimulatedTime) + '\n')  
    out.write('Warm up time: ' + str(warmUpTime) + '\n')  
    out.write('Date: ' + str(time.localtime().tm_year) + '/' + str(time.localtime().tm_mon).zfill(2) + '/'  + str(time.localtime().tm_mday).zfill(2) + '\n')
    out.write('\n')
    
    #Statistical-precision subheader
    if TypeOfAnalysis == 'Statistical-precision':  
        out.write('Test based on a desired confidance interval of +/- S\n'
                  '       **  N = [t(1-alpha/2;N-1)*S]^2  **\n'
                  '\n'
                  'For the Confidance interval of standard deviation, a Chi-square test is used\n'
                  '       **  CI = [(N-1)^0.5*S*Xhi(N-1)]  **\n'
                  '\n'                                    
                  'Base values (default values) used to run the test:\n')
        for var in variables:
            out.write(str(var) + ';')
        out.write('\n')
        for var in values:
            out.write(str(var) + ';')
        out.write('\n')
        out.write('\n'
                  '*Nbr_itt: number of itterations ran to run the t-test\n'
                  '*N1: minimum number of iterrations needed to give a CI of 1.0 for the forward gaps\n'
                  '*N2: minimum number of iterrations needed to give a CI of 1.0 for the opportunistic lane change gaps calculated after lane change\n'
                  '*N3: minimum number of iterrations needed to give a CI of 1.0 for the opportunistic lane change gaps calculated before lane change\n'
                  '*N4: minimum number of iterrations needed to give a CI of 1.0 for the mandatory lane change gaps calculated after lane change\n'
                  '*N5: minimum number of iterrations needed to give a CI of 1.0 for the mandatory lane change gaps calculated before lane change\n'
                  '*SCI1: Confidance interval calculated for the standard deviation for the forward gaps\n'
                  '*SCI2: Confidance interval calculated for the standard deviation for the opportunistic lane change gaps calculated after lane change\n'
                  '*SCI3: Confidance interval calculated for the standard deviation for the opportunistic lane change gaps calculated before lane change\n'
                  '*SCI4: Confidance interval calculated for the standard deviation for the mandatory lane change gaps calculated after lane change\n'
                  '*SCI5: Confidance interval calculated for the standard deviation for the mandatory lane change gaps calculated before lane change\n')
        
    #Sensitivity subheader
    if TypeOfAnalysis == 'Sensitivity' or TypeOfAnalysis == 'Monte Carlo': 
        out.write('*var_name: Name of the tested variable\n'
                  'Note: m = mean, fq = first quartile, md = median, tq = third quartile, std = standard deviation, %diff = relative difference with the default values results'
                  '*flow: Vehicular flow\n'
                  '*nbr_opp: Number of opportunistic lane changes\n'
                  '*nbr_man: Number of mandatory lane changes\n'
                  '*forward: Forward gaps (all specified lanes concatenated, calculated at the middle of each link)\n'
                  '*LC_Aopp: Opportunistic lane change gap calculated after the lane changing vehicule inserted into the new lane \n'
                  '*LC_Bopp: Opportunistic lane change gap calculated before the lane changing vehicule began changing lane\n'
                  '*LC_Aman: Mandatory lane change gap calculated after the lane changing vehicule inserted into the new lane \n'
                  '*LC_Aman: Mandatory lane change gap calculated before the lane changing vehicule began changing lane \n'
                  '*f_speed: Speed distribution (all specified lanes concatenated, calculated at the same point as forward gaps)\n'
                  '\n'
                  'var_name;')
        for var in variables:
            out.write(str(var) + ';')
        if TypeOfAnalysis == 'Sensitivity': 
            out.write('flow;% diff;nbr_opp;% diff;nbr_man;% diff;'
                      'm_forward;% diff;fq_forward;% diff;md_forward;% diff;tq_forward;% diff;std_forward;% diff;'
                      'm_LC_Aopp;% diff;fq_LC_Aopp;% diff;md_LC_Aopp;% diff;tq_LC_Aopp;% diff;std_LC_Aopp;% diff;'
                      'm_LC_Bopp;% diff;fq_LC_Bopp;% diff;md_LC_Bopp;% diff;tq_LC_Bopp;% diff;std_LC_Bopp;% diff;'
                      'm_LC_Aman;% diff;fq_LC_Aman;% diff;md_LC_Aman;% diff;tq_LC_Aman;% diff;std_LC_Aman;% diff;'
                      'm_LC_Bman;% diff;fq_LC_Bman;% diff;md_LC_Bman;% diff;tq_LC_Bman;% diff;std_LC_Bman;% diff;'
                      'm_f_speed;% diff;fq_f_speed;% diff;md_f_speed;% diff;tq_f_speed;% diff;std_f_speed;% diff\n'
                      )        
        else:
            out.write('flow;nbr_opp;nbr_man;'
                      'm_forward;fq_forward;md_forward;tq_forward;std_forward;'
                      'm_LC_Aopp;fq_LC_Aopp;md_LC_Aopp;tq_LC_Aopp;std_LC_Aopp;'
                      'm_LC_Bopp;fq_LC_Bopp;md_LC_Bopp;tq_LC_Bopp;std_LC_Bopp;'
                      'm_LC_Aman;fq_LC_Aman;md_LC_Aman;tq_LC_Aman;std_LC_Aman;'
                      'm_LC_Bman;fq_LC_Bman;md_LC_Bman;tq_LC_Bman;std_LC_Bman;'
                      'm_f_speed;fq_f_speed;md_f_speed;tq_f_speed;std_f_speed;\n'
                      )
   
    #Calibration header
   
    return out, subdirname
    
def writeRealDataReport(dirname, filename, video_names, inpxname, min_time, max_time, speed_centiles, other_info):
    '''writes the report file.
       Speed_centiles MUST be of the form [list_of_name,list_of_values]
       other_info Must include directly the format to output'''
    
    #header writing
    out = open(filename.format(dirname), 'w')
    out.write('Video analysed: ' + str(video_names) + '\n')
    out.write('Associated Vissim file: ' + str(inpxname) + '\n')
    if min_time or max_time is not None:
        if min_time is None:
            out.write('Video analysed from time 0 to '+str(max_time)+' (frames)\n')
        elif max_time is None:
            out.write('Video analysed from time '+str(min_time)+' (frames) till end\n')
        else:
            out.write('Video analysed from time '+str(min_time)+' to '+str(max_time)+' (frames)\n') 
    out.write('Date: ' + str(time.localtime().tm_year) + '/' + str(time.localtime().tm_mon).zfill(2) + '/'  + str(time.localtime().tm_mday).zfill(2) + '\n')
    out.write('\n')

    #speed centile description
    out.write('Usefull speed centiles for vissim calibration:\n')
    writeInFile(out, ['centile (%)'] + speed_centiles[0])
    writeInFile(out, ['speed (m/frame)*'] + speed_centiles[1])
    out.write('*m/s = (m/frame)*fps  and km/h = (m/frame)*fps*3.6\m')
    out.write('\n')
    
    #subheader
    for i in other_info:       
        writeInFile(out, i)  
      
    out.close()
   
    return

def writeDisgnosedReport(dirname, filename, video_names, inpxname, min_time, max_time, maxSpeed, excess_speed, invert_speed, fps):
    '''writes the disgnosis file.'''
    
    #header writing
    out = open(filename.format(dirname), 'w')
    out.write('Video analysed: ' + str(video_names) + '\n')
    out.write('Associated Vissim file: ' + str(inpxname) + '\n')
    if min_time or max_time is not None:
        if min_time is None:
            out.write('Video analysed from time 0 to '+str(max_time)+' (frames)\n')
        elif max_time is None:
            out.write('Video analysed from time '+str(min_time)+' (frames) till end\n')
        else:
            out.write('Video analysed from time '+str(min_time)+' to '+str(max_time)+' (frames)\n') 
    out.write('Date: ' + str(time.localtime().tm_year) + '/' + str(time.localtime().tm_mon).zfill(2) + '/'  + str(time.localtime().tm_mday).zfill(2) + '\n')
    out.write('\n')

    #excess speed
    out.write('Speed threshold used: '+str(maxSpeed*3.6*fps)+'\n')
    out.write('List of objects with speed greater than threshold: (#obj, #first_frame, mean speed)\n')
    for exc in excess_speed:
        writeInFile(out, [exc.getNum(), exc.getFirstInstant(), np.mean(np.asarray(exc.curvilinearVelocities)[:,0])*fps*3.6] )

    #wrong way speed
    out.write('Speed threshold used: '+str(maxSpeed*3.6*fps)+'\n')
    out.write('List of objects with speed greater lower than 0 (possible wrong way): (#obj, #first_frame, mean speed)\n')
    for inv in invert_speed:
        writeInFile(out, [inv.getNum(), inv.getFirstInstant(), np.mean(np.asarray(inv.curvilinearVelocities))] )
          
    out.close()
   
    return

    
def writeListToCSV(lists, name):
    '''writes a CSV file which will contain one line per element in lists'''
    out = open(name, 'w')
    for sublist in lists:
        writeInFile(out,sublist)
    out.close()
        
def writeInFile(out, *args, **kwargs):
    '''Writes any number of arguments into the file given in out'''    
    variables = mathTools.ToOneList(list(args))

    rounding = 4
    if kwargs is not None:
        for key, value in kwargs.items():
            if key == 'rounding':
                rounding = value
    
    for var in variables:
        if isinstance(var,float) is True:            
            if rounding is False:
                out.write(str(var) + ';')
            else:
                out.write(str(round(var,rounding)) + ';')
        else:
            out.write(str(var) +';')
    out.write('\n')
   
def timeStamp(variables, points, sim, itt = None):
    '''adds a timer recap to a file'''
    text = []
    total_time = time.clock()
    avg_per_point = total_time/(len(variables) * points + 1 ) 
    avg_per_sim   = total_time/((len(variables) * points + 1 )*sim)
    
    #the append([]) serves to add an empty line before the time marker when using writeInFile
    text.append([])
    text.append(['Total elapsed time (sec) :',total_time])
    if itt is not None: text.append(['Number of itaration required :', itt])
    text.append(['Average time per point (sec) :',avg_per_point])
    text.append(['Average time per simulation (sec): ',avg_per_sim])
    
    return text
    
##################
# In-console print tools
##################
def verboseIntro(commands, config, TypeOfAnalysis):
    print ('--> Starting a ' + TypeOfAnalysis + ' Analysis with the following options: ')
    if commands.multi or commands.multi_test or commands.mode or commands.vis_save:
        print ('      -- -- -- -- -- -- -- -- -- -- -- -- -- --   ')
        if commands.multi:
            print (' |-> Multiprocessing activated ')
        if commands.multi_test:
            print (' |-> Multiprocessing debug mode activated ')
        if commands.mode:
            print (' |-> Test mode activated ')
        if commands.vis_save:
            print (' |-> Graphic saving mode activated \n'
                   '        *files will be saved as ' + str(commands.fig_format))                   
            
    print ('      -- -- -- -- -- -- -- -- -- -- -- -- -- --     \n'
           'Inpx to process:       ' + str(config.inpx_name) + '\n'   
           'Simulation steps:      ' + str(config.sim_steps)      )
    print ('      -- -- -- -- -- -- -- -- -- -- -- -- -- --         ')
    if TypeOfAnalysis == 'Sensitivity': 
        print('Number of points:      ' + str(config.nbr_points)    + '\n'
              'Number of simulations: ' + str(config.nbr_runs)       )
    print ('Simulation time:       ' + str(config.simulation_time)   + '\n'
           'Simulation warm up:    ' + str(config.warm_up_time)      )
    if TypeOfAnalysis == 'Statistical-precision':
        print('      -- -- -- -- -- -- -- -- -- -- -- -- -- --         \n'
              'Desired pourcentage error on the mean confidence interval: ' + str(config.desired_pct_error) +' %')
    print''

##################
# Graphic tools
##################        
def printStatGraphs(graphspath, variable, value_name, variable_name, graphformat, nsim, subpath = ''):
    '''create graphs for a type 'Stats' variable | data comes from vissim output
       file
    
       Primarily used to plot data from sensitivity analysis'''

    #creating the cumulative graph                         
    if variable.distributions[0].value != []:    #checks if the variable is empty
        plt.plot(variable.distributions[0].value, variable.distributions[0].cumul)
        plt.xlabel(variable_name.replace('_',' '))
        plt.ylabel('Count')
        plt.title('Cumulated distribution for ' + variable_name.replace('_',' '))
        plt.savefig(os.path.join(graphspath, 'cumul_dist_graphs', subpath, value_name + '_cumulative_distribution_for_'+ variable_name + '.' + graphformat), format =  graphformat)
        plt.clf()
        plt.close()
    
    #creating the distributions graph
    ##concatenated distributions
    if variable.cumul_all.raw != []:                                                        #checks if the variable is empty  
        fig = plt.figure()
        fig.add_axes((0.1,0.1,0.65,0.80))
        nbr, bins, patches = plt.hist(variable.cumul_all.raw,100,histtype = 'step')
        #kde is the equation of the cumulated gaussians
        kde = stats.gaussian_kde(variable.cumul_all.raw)                                    
        test = np.arange(min(variable.cumul_all.raw) -1,max(variable.cumul_all.raw) +1,0.1)
        #kde(array) returns the probability (0..1) for each variables in the array.
        #The integral of the resulting curve = 1, so to scale it with the raw data, we multiply it by the number of variables in the data... ie: len(raw_data)       
        line = plt.plot(test, len(variable.cumul_all.raw)*kde(test), '--')                            
        plt.xlabel(variable_name.replace('_',' '))
        plt.ylabel('Count')
        plt.title('Concatenated distributions for\n' + variable_name.replace('_',' '))
        plt.xlim(min(variable.cumul_all.raw) -1, max(variable.cumul_all.raw) +1 )
        plt.ylim(ymax = max(nbr) +2)
        plt.figlegend([patches[0], line[0]],['Raw','Best fit'],'center right')
        plt.savefig(os.path.join(graphspath, 'distribution_graphs', subpath, value_name + '_concatenated_distributions_for_'+ variable_name + '.' + graphformat), format =  graphformat) 
        plt.clf()
        plt.close(fig)
    
        ##all simulations - linked to the concatenated because it allows us to have bins that convers equally each distributions and so make them comparable   
        simline = []
        simtext = []
        bestline = []
        besttext = []
        find_ymax = 0
        fig = plt.figure()
        fig.add_axes((0.1,0.1,0.63,0.80))
        
        if variable_name == 'Forward_gaps':
            chunks = workers.toChunks(len(variable.distributions)//nsim, range(len(variable.distributions)))
        for i in range(len(variable.distributions)):
            if variable.distributions[i].raw != []: #checks if the variable is empty
                nbr, bins, patches = plt.hist(variable.distributions[i].raw,range=(bins[0],bins[-1]),histtype = 'step')
                
                if variable_name == 'Forward_gaps':
                    for chunk in chunks:
                        if i in chunk:                    
                            simtext.append('Simulation '+ str(i//(len(variable.distributions)//nsim) + 1) +'\nLane ' + str(i - chunk[0] +1) + '/' + str(len(variable.distributions)//nsim) )

                else:
                    simtext.append('Simulation '+ str(i+1))
                
                simline.append(patches[0])
                if max(nbr) > find_ymax:
                    find_ymax = max(nbr)
                kde = stats.gaussian_kde(variable.distributions[i].raw)
                dist = np.arange(min(variable.distributions[i].raw) -1,max(variable.distributions[i].raw) +1,0.1)
                lines = plt.plot(dist, len(variable.distributions[i].raw)*kde(dist), '--')            
                if variable_name == 'Forward_gaps':
                    besttext.append('Best fit for\n'+ str(i+1))
                else:
                    besttext.append('Best fit for\nsimulation'+ str(i+1))
                bestline.append(lines[0])
        handles = simline + bestline
        labels = simtext + besttext       
            
        plt.xlabel(variable_name.replace('_',' '))
        plt.ylabel('Count')
        plt.title('Individual distributions of all simulations for\n' + variable_name.replace('_',' '))
        plt.figlegend(handles, labels,'center right')
        #plt.legend(bbox_to_anchor = (1.3, 0.5))
        plt.ylim(ymax = find_ymax + 2) 
        plt.xlim(min(variable.cumul_all.raw) -1, max(variable.cumul_all.raw) +1 )      
        plt.savefig(os.path.join(graphspath, 'distribution_graphs', subpath, value_name + '_simulations_distributions_for_'+ variable_name + '.' + graphformat), format =  graphformat)    
        plt.clf()
        plt.close(fig)                  
    return True

def plot_st(objects, align_corr_dict, alignments, fps, dirname, video_name):
    '''generates a time-space diagram for each alignment
    
       Primarily used for video data'''
    for a in xrange(len(alignments)):
        fig = plt.figure()
        for o in objects:
            t = []
            s = []
            for pos in xrange(len(o.getCurvilinearPositions().getSCoordinates())):
                if o.getCurvilinearPositions().getLanes()[pos] == a:
                    t.append((o.getFirstInstant()+pos)/float(fps))
                    s.append(o.getCurvilinearPositions().getSCoordinates()[pos])
            plt.plot(t,s,'b')

        plt.xlabel('time (sec)' )
        plt.ylabel('distance (m)')
        plt.title('Time-space diagram for alignment ' + alignments[a] + ' in corridor ' + str(align_corr_dict[int(alignments[a])]))
        plt.savefig(os.path.join(dirname, 'Time-space diagram for alignment ' + alignments[a] + ' for corridor ' + str(align_corr_dict[int(alignments[a])]) + ' for video ' + str(video_name.strip('.sqlite'))))
        plt.clf()
        plt.close(fig)    
    return
    
def plot_qt(time_serie, gaps_serie, dirname, video_name, corridor, fps, min_time, max_time):
    '''generates a flow on time diagram for alignment number 'align_num' using gap
       information only handles one time/gap serie at a time
                  
       Primarily used for video data'''

    #plot data       
    time = list(np.asarray(time_serie)/fps)

    #flow is obtained with an arithmetic mobile mean
    flow = []
    for g in xrange(len(gaps_serie)):
        if g == 0 or g == 1:        
            mean_gap = np.mean(gaps_serie[0:5])
        elif g == len(gaps_serie) -1 or g == len(gaps_serie) -2:
            mean_gap = np.mean(gaps_serie[-5:])
        else:
            mean_gap = np.mean(gaps_serie[g-2:g+3])
        flow.append(fps*3600/mean_gap)
    
    #finding min and max time for the graph axis
    if min_time is None:
        min_gtime = mathTools.myfloor(min(time), base=20)
    else:
        min_gtime = mathTools.myfloor(min_time/fps, base=20)
        
    if max_time is None:
        max_gtime = mathTools.myceil(max(time), base=20)
    else:
        max_gtime = mathTools.myceil(max_time/fps, base=20)
    
    fig = plt.figure()
    plt.plot(time, flow, color = 'b')
    
    plt.xlim(min_gtime, max_gtime)
    plt.xticks(range(min_gtime,max_gtime,20))
    plt.xlabel('time (sec)')
    plt.ylabel('flow (veh/h)')
    plt.title('Flow in corridor '+str(corridor)+' for video '+str(video_name.strip('.sqlite'))+' with regard to time')
    plt.savefig(os.path.join(dirname, 'Flow-time diagram for corridor ' + str(corridor) + ' for video ' + str(video_name.strip('.sqlite'))))
    plt.clf()
    plt.close(fig)    
    return

def plot_dists(dirname, video_data, vissim_data, fout, simulationStepsPerTimeUnit, fps, normalized=True):
    try:    
        fig, ax = plt.subplots(2, 1, squeeze=True)
        video_p_list  = [i/float(fps) for i in video_data.cumul_all.raw if i/fps < 60]
        vissim_p_list = [i/float(simulationStepsPerTimeUnit) for i in vissim_data.cumul_all.raw if i/simulationStepsPerTimeUnit < 60]
        if len(video_p_list) > 0:
            ax[0].hist(video_p_list, normed=normalized, histtype='stepfilled', bins = 100, color = 'b', alpha=0.6, label='video data')
        if len(vissim_p_list) > 0:
            ax[0].hist(vissim_p_list, normed=normalized, histtype='stepfilled', bins = 100, color = 'r', alpha=0.6, label='vissim concat data')
        ax[0].legend(loc='best', frameon=False)
        ax[0].set_title('Comparison of Vissim data and Video data\n'+r'$f_{out}$'+' = ' + str(round(fout,4)))
    
        if len(vissim_p_list) > 0:
            ax[1].hist(vissim_p_list, normed=normalized, histtype='stepfilled', bins = 100, color = 'r', alpha=0.6, label='vissim concat data')    
        for j in xrange(len(vissim_data.distributions)):
            dist_p_list = [i/float(simulationStepsPerTimeUnit) for i in vissim_data.distributions[j].raw if i/simulationStepsPerTimeUnit < 60]
            if len(dist_p_list) > 0:
                ax[1].hist(dist_p_list, normed=normalized, histtype='stepfilled', bins = 100, alpha=0.4, label='vissim data - run #'+str(j+1))
        ax[1].legend(loc='best', frameon=False)
        ax[1].set_title('Comparison of all Vissim data')
    
        plt.subplots_adjust(hspace=0.3)
        plt.savefig(os.path.join(dirname, 'Video and Vissim distributions'))
        plt.clf()
        plt.close(fig)    
    except:
        traceback.print_exc(file=open(os.path.join(dirname, 'Graphic.err'),'w'))
    
##################
# Drawing tools
##################
def tellMe(s, target=False):
    '''Used in drawAlign'''
    if(not target):
        target = plt
    
    print('Drawing console: '+s)
    plt.title(s,fontsize=14)
    plt.draw()

def drawAlign(target=False):
    ''' This module will enable user to draw alignments ontop of trajectories
        
    Note: Expects trajectory plot to be pre-drawn
    Thanks to Paul St-Aubin PvaTools
    '''
    if(not target):
        target = plt
        
    plt.setp(target.gca(), autoscale_on=False)
    
    exit_cond = False
    alignments = []
    pj = []
    j = 0
    ## Segments
    rcParams['lines.markersize']=24
    while not exit_cond:
        pts = []
        while len(pts) < 2:
            tellMe('Draw alignments. Left click: select points, right click: undo, middle click: exit.', target=target)
            pts = [list(x) for x in plb.ginput(0, timeout=-1)]
            if(len(pts) < 2):
                tellMe('Too few points, starting over.', target=target)
                time.sleep(1) # Wait a second
    
        ph = plb.plot([x[0] for x in pts], [x[1] for x in pts], 'm', lw=2 )
    
        tellMe('Save alignments? Mouse click for yes, key click for no.', target=target)
        save_cond = plb.waitforbuttonpress()
        for p in ph: p.remove()
        if(not save_cond):
            alignments.append(pts)
            pj.append(plb.plot([x[0] for x in pts], [x[1] for x in pts], 'k', lw=2))
            j += 1
        
        tellMe('Add alignments? Mouse for yes, key for no.', target=target)
        exit_cond = plb.waitforbuttonpress()
    rcParams['lines.markersize']=6 #back to default value
    return alignments
