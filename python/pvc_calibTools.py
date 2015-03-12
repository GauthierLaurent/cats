# -*- coding: utf-8 -*-
'''
Created on Thu Jul 03 11:28:53 2014

@author: Laurent
'''

#this will be used to verify if the serialised data is still matching the data processsed by pcvtools

        
##################
# Import Libraries
##################
#Natives
from itertools import repeat, product
import random, os
import numpy as np
from scipy.stats.mstats import ks_twosamp

#Internal
import pvc_csvParse as csvParse

##################
# Statistic tests
##################
def ks_matrix(dist_list):
    '''building the 2 by 2 matrix'''
    matrix = []
    for i in xrange(len(dist_list)):
        line_i = []
        for j in xrange(len(dist_list)):
            d_v, p_v = ks_twosamp(dist_list[i],dist_list[j])
            line_i.append(d_v)
        matrix.append(line_i)
    return matrix

def count_mat(matrix, treshold):
    '''count how many members of each line respect the treshold'''
    count_list = []
    for line in matrix:
        count_list.append(np.count_nonzero(line < treshold))
    return count_list

def treat_stats_list(stats_list):
    '''used to transform a stat list into a list of lists'''
    raw_list = []
    for i in xrange(len(stats_list.distributions)):
        raw_list.append(stats_list.distributions[i].raw)
    return raw_list

def filter_dist_with_ks(dist_list, treshold):
    '''filter a list of distribution with the Komolgorov-Smirnov test to
       keep only the distributions with the d value lower than threshold.
       
       returns a concatenated distribution and the list of indexes of the
       rejected distributions
       
       IMPORTANT: does not support stat list as input
    '''

    matrix = np.asarray(ks_matrix(dist_list))
    count_list = count_mat(matrix, treshold)
    index = count_list.index(max(count_list))

    concat = [index]
    rejected = []
    for i in range(len(dist_list)):
        if i != index and (matrix[index] <= treshold )[i]:
            concat.append(i)
        elif not (matrix[index] < treshold )[i]:
            rejected.append(i)

    return rejected
    
def checkCorrespondanceOfOutputs(video_value, calculated_value, simulationStepsPerTimeUnit,fps):
    '''Test a range of values with the kolmolgorov-Smirnov test'''

    D_statistic_list = []
    p_value_list = []

    for i in range(len(calculated_value)):
        if len(video_value[i].cumul_all.raw) > 0 and len(calculated_value[i].cumul_all.raw) > 0:
            D_statistic, p_value = ks_twosamp([p/float(simulationStepsPerTimeUnit) for p in video_value[i].cumul_all.raw], [p/float(fps) for p in calculated_value[i].cumul_all.raw])
            D_statistic_list.append(calculated_value[i].cumul_all.mean)     #value (mean)
            D_statistic_list.append(D_statistic)                            #value (delta)
            p_value_list.append(p_value)
        else:
            D_statistic_list.append('0.00') #value (mean)
            D_statistic_list.append('DNE')  #value (delta)
    
    return D_statistic_list
   
################################ 
#        Network Calibration class       
################################
class Network:
    def __init__(self,inpx_path,traj_path_list):
        self.inpx_path = inpx_path

        if isinstance(traj_path_list, list):
            self.traj_paths = traj_path_list
        else:
            self.traj_paths = [traj_path_list] 

        
    def addtraj(self,traj):
        self.traj_paths = self.traj_paths + [traj]
                       
    def addCorridor(self, corridor):
        self.corridors = corridor
        
    def addVissim(self, vissim):
        self.vissim = vissim
        
    def addVideoComparison(self,data_list):
        try:
            self.videoComparison.append(data_list)
        except:
            self.videoComparison = [data_list]        
    
    @staticmethod
    def buildNetworkObjects(config):
        '''takes all info from calib.cfg and build a network object out of it. This
           fonction will not duplicate a network that has been entered multiple times
           to be processed on two different videos files'''
        
        inpx_list = {}
        if config.active_network_1:
            inpx_list[config.path_to_inpx_file_1.split(os.sep)[-1]] = Network(config.path_to_inpx_file_1,config.path_to_video_data_1)
            VissimCorridors1, trafIntCorridors1 = csvParse.extractVissimCorridorsFromCSV(config.path_to_csv_net1.strip(config.path_to_csv_net1.split(os.sep)[-1]), config.path_to_inpx_file_1.split(os.sep)[-1])
            inpx_list[config.path_to_inpx_file_1.split(os.sep)[-1]].addCorridor(VissimCorridors1)
            
        if config.active_network_2:
            if config.path_to_inpx_file_2.split(os.sep)[-1] not in inpx_list:
                inpx_list[config.path_to_inpx_file_2.split(os.sep)[-1]] = Network(config.path_to_inpx_file_2,config.path_to_video_data_2)
                VissimCorridors2, trafIntCorridors2 = csvParse.extractVissimCorridorsFromCSV(config.path_to_csv_net2.strip(config.path_to_csv_net2.split(os.sep)[-1]), config.path_to_inpx_file_2.split(os.sep)[-1])
                inpx_list[config.path_to_inpx_file_2.split(os.sep)[-1]].addCorridor(VissimCorridors2)
            else:
                inpx_list[config.path_to_inpx_file_2.split(os.sep)[-1]].addtraj(config.path_to_video_data_2)
                
        if config.active_network_3:
            if config.path_to_inpx_file_3.split(os.sep)[-1] not in inpx_list:
                inpx_list[config.path_to_inpx_file_3.split(os.sep)[-1]] = Network(config.path_to_inpx_file_3,config.path_to_video_data_3)
                VissimCorridors3, trafIntCorridors3 = csvParse.extractVissimCorridorsFromCSV(config.path_to_csv_net3.strip(config.path_to_csv_net3.split(os.sep)[-1]), config.path_to_inpx_file_3.split(os.sep)[-1])
                inpx_list[config.path_to_inpx_file_3.split(os.sep)[-1]].addCorridor(VissimCorridors3)
            else:
                inpx_list[config.path_to_inpx_file_3.split(os.sep)[-1]].addtraj(config.path_to_video_data_3)    
    
        if config.active_network_4:
            if config.path_to_inpx_file_4.split(os.sep)[-1] not in inpx_list:
                inpx_list[config.path_to_inpx_file_4.split(os.sep)[-1]] = Network(config.path_to_inpx_file_4,config.path_to_video_data_4)
                VissimCorridors4, trafIntCorridors4 = csvParse.extractVissimCorridorsFromCSV(config.path_to_csv_net4.strip(config.path_to_csv_net4.split(os.sep)[-1]), config.path_to_inpx_file_4.split(os.sep)[-1])
                inpx_list[config.path_to_inpx_file_4.split(os.sep)[-1]].addCorridor(VissimCorridors4)
            else:
                inpx_list[config.path_to_inpx_file_4.split(os.sep)[-1]].addtraj(config.path_to_video_data_4)    
            
        return inpx_list.values()  
        
##################
# Sampling tools
##################

def genMCsample(variables, n):
    '''generates a Monte Carlo sample of n points'''
    valuesVector = []
    for i in xrange(n):
        thisVector = []
        laneChangeState = random.randrange(0,2)
        for j in xrange(len(variables)):
            if variables[j].vissim_name not in ['CoopLnChg','CoopLnChgSpeedDiff','CoopLnChgCollTm']:
                thisVector.append(random.uniform(variables[j].desired_min,variables[j].desired_max))
            else:
                if variables[j].vissim_name == 'CoopLnChg':
                    if laneChangeState == 1:
                        thisVector.append(True)
                    else:
                        thisVector.append(False)
                else:
                    if laneChangeState == 1:
                        thisVector.append(random.uniform(variables[j].desired_min,variables[j].desired_max))
                    else:
                        thisVector.append(999999)
        valuesVector.append(thisVector)
    return valuesVector

def choose_xn(n,m):
    '''chooses n points with m dimensions'''
    possibility_mat = []    
    for i in xrange(m):        
        possibility_mat.append(range(n))
        
    points = []
    for i in xrange(n):
        point = []
        for j in xrange(len(possibility_mat)):
            coord = random.randint(0,len(possibility_mat[j])-1)
            point.append(possibility_mat[j][coord])
            possibility_mat[j].pop(coord)
        points.append(point)
        
    return points
    
def boolTable(n):
    out = []
    for args in product(*repeat((True, False),n)):
        out.append(list(args))
    return out
    
def genLHCsample(variables,n):
    '''generates a Latin Hypercube sample of n points per non boolean dimension
       
       variables can be either boolean or real number values
       
       returns all combinations of real values (nxn matrix) for the True and False
       possibility of each boolean variable
        
       total number of points returned = ( len(real variables) )*(  2 ** len(bool variables) )
    '''        
    real_dim = []
    disc_dim = []
    
    #classification of boolean and nonboolean variables
    ranges = []
    for var in xrange(len(variables)):
        ranges.append([variables[var].desired_min, variables[var].desired_max])
        if isinstance(variables[var].desired_max, bool):
            disc_dim.append(var)
        else:
            real_dim.append(var)
    
    #subdivision of the ranges of each nonboolean variable
    cut_ranges =  []
    for i in real_dim:
        this_one_range = []   
        for j in xrange(n):
            this_one_range.append([ranges[i][0] + j * (ranges[i][1]-ranges[i][0])/float(n), ranges[i][0] + (j+1) * (ranges[i][1]-ranges[i][0])/float(n)])
        cut_ranges.append(this_one_range)

    #column,row selection
    mat = choose_xn(n,len(real_dim))

    #real values variable point selection
    real_mat = []
    for m in xrange(n):
        point = []
        for k in xrange(len(real_dim)):
            point.append(random.uniform(cut_ranges[k][mat[m][k]][0],cut_ranges[k][mat[m][k]][1]))
        real_mat.append(point)   

    #bool values combinations enumeration
    bool_mat = boolTable(len(disc_dim))

    #assembly line
    #TODO: apply corrections to variables affected by True/False value of the bool variable
    final_mat = []
    for i in xrange(len(bool_mat)):
        semi_mat = []
        for k in xrange(len(real_mat)):
            point = []                
            for m in xrange(len(variables)):
                if m in disc_dim:
                    point.append(bool_mat[i][disc_dim.index(m)])
                else:
                    point.append(real_mat[k][real_dim.index(m)])
            semi_mat.append(point)
        final_mat += semi_mat

    return final_mat
            
    