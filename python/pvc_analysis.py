# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 14:43:44 2014

@author: Laurent
"""

################################ 
#        Importing dependencies       
################################ 
#Natives
import os, shutil, sys, copy
from scipy.stats import t, chi2
from scipy.stats.mstats import ks_twosamp
import cPickle as pickle
import numpy as np

#Internal
import pvc_write as write
import pvc_vissim as vissim
import pvc_outputs as outputs
import pvc_define as define

################################ 
#        Calibration analysis       
################################
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
    
def checkCorrespondanceOfOutputs(video_value, calculated_value):
    '''Test a range of values with the kolmolgorov-Smirnov test'''

    D_statistic_list = []
    p_value_list = []

    for i in range(len(calculated_value)):
        if len(video_value[i].cumul_all.raw) > 0 and len(calculated_value[i].cumul_all.raw) > 0:
            D_statistic, p_value = ks_twosamp(video_value[i].cumul_all.raw, calculated_value[i].cumul_all.raw)
            D_statistic_list.append(D_statistic)
            p_value_list.append(p_value)
        else:
            D_statistic_list.append('DNE')
    
    return D_statistic_list

def runVissimForCalibrationAnalysis(network, inputs):
    '''Note: Vissim is passed in the Network class variable "network" '''
    
    #unpacking inputs
    config           = inputs[0]
    variables        = inputs[1]
    parameters       = inputs[2]
    point_folderpath = inputs[3]
    multi_networks   = inputs[4]
    
    Vissim = network[0].vissim
    
    if multi_networks is True:
        #if we are treating more than one network, than we subdivide the point folder into network folders
        if not os.path.isdir(os.path.join(point_folderpath,os.path.splitext(network[0].inpx_path.split(os.sep)[-1])[0])):
            os.mkdir(os.path.join(point_folderpath,os.path.splitext(network[0].inpx_path.split(os.sep)[-1])[0]))
        
        final_inpx_path = os.path.join(point_folderpath,os.path.splitext(network[0].inpx_path.split(os.sep)[-1])[0])
        shutil.copy(os.path.join(point_folderpath,network[0].inpx_path.split(os.sep)[-1]),os.path.join(final_inpx_path,network[0].inpx_path.split(os.sep)[-1]))    

    else:
        final_inpx_path = copy.deepcopy(point_folderpath)

    Vissim.LoadNet(os.path.join(final_inpx_path,network[0].inpx_path.split(os.sep)[-1]))
    
    values = []
    for var in variables:
        values.append(var.point)
           
    #Initializing and running the simulation
    simulated = vissim.initializeSimulation(Vissim, parameters, values, variables)
 
    if simulated is not True:
        for traj in network[0].traj_paths:
            network[0].addVideoComparison(['SimulationError'])
        return False
             
    else:
        d_stat = []
        rejected_files = []
        
        #treating the outputs
        inputs = [final_inpx_path, config.sim_steps, config.warm_up_time, False, network[0].corridors]
        file_list = [f for f in os.listdir(final_inpx_path) if f.endswith('fzp')]
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forSpeeds = outputs.treatVissimOutputs(file_list, inputs)
       
        #verifying the validity of the distributions
        if config.output_forward_gaps and len(forFMgap.distributions) > 1:
            rejected = filter_dist_with_ks(treat_stats_list(forFMgap), config.ks_threshold)

        if config.output_lane_change and len(oppLCbgap.distributions) > 1:
            rejected = filter_dist_with_ks(treat_stats_list(oppLCbgap), config.ks_threshold)    #using before lane change gaps
        
        #adjustment
        flow.popList(rejected) 
        oppLCcount.popList(rejected) 
        manLCcount.popList(rejected) 
        forFMgap.pop_dist_list(rejected)        
        oppLCagap.pop_dist_list(rejected)
        oppLCbgap.pop_dist_list(rejected)
        manLCagap.pop_dist_list(rejected)
        manLCbgap.pop_dist_list(rejected)
        forSpeeds.pop_dist_list(rejected)

        #memorizing bad files
        for r in rejected:
            rejected_files.append(file_list[r]) 

        #running new data
        goal = parameters[2]
        total_retries = 5 ###this could be moved to the cfg file
        retry = 0
        seed = parameters[1] + goal + 1
        
        while len(forFMgap.distributions) < goal and retry <= total_retries:
            #fixing vissim parameters            
            nbr_run_this_try = len(rejected)
            parameters[2] = nbr_run_this_try  #number of rerun
            parameters[1] = seed
        
            #Initializing and running the simulation
            simulated = vissim.initializeSimulation(Vissim, parameters, values, variables)        
        
            if simulated is True:
                #treating the outputs
                inputs = [final_inpx_path, config.sim_steps, config.warm_up_time, False, network[0].corridors]
                file_list = [f for f in os.listdir(final_inpx_path) if f.endswith('fzp')]
                new_flow, new_oppLCcount, new_manLCcount, new_forwFMgap, new_oppLCagap, new_oppLCbgap, new_manLCagap, new_manLCbgap, new_forSpeeds = outputs.treatVissimOutputs(file_list[-nbr_run_this_try:], inputs)
        
                #verifying the validity of the distributions
                if config.output_forward_gaps:
                    rejected = filter_dist_with_ks(treat_stats_list(outputs.stats.concat(forFMgap,new_forwFMgap)), config.ks_threshold)

                if config.output_lane_change:
                    rejected = filter_dist_with_ks(treat_stats_list(outputs.stats.concat(oppLCbgap,new_oppLCbgap)), config.ks_threshold)    #using before lane change gaps
                    
                #adjustment
                flow.popList(rejected) 
                oppLCcount.popList(rejected) 
                manLCcount.popList(rejected) 
                forFMgap.pop_dist_list(rejected)        
                oppLCagap.pop_dist_list(rejected)
                oppLCbgap.pop_dist_list(rejected)
                manLCagap.pop_dist_list(rejected)
                manLCbgap.pop_dist_list(rejected)
                forSpeeds.pop_dist_list(rejected)
                
                #memorizing bad files
                for r in rejected:
                    rejected_files.append(file_list[-nbr_run_this_try:][r]) 
                
            #fixing while loop info
            seed += nbr_run_this_try
            retry += 1

        #moving unwanted file        
        if len(rejected_files) > 0:
            if not os.path.exists(os.path.join(final_inpx_path, 'rejected_tests')):
                os.makedirs(os.path.join(final_inpx_path, 'rejected_tests'))
            for rejected_file in rejected_files:
                shutil.copy(os.path.join(final_inpx_path,rejected_file),os.path.join(final_inpx_path,'rejected_tests',rejected_file))
        
        non_dist_data = [flow, oppLCcount, manLCcount]
        dist_data = [forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forSpeeds]
        
        #setting video values
        for traj in network[0].traj_paths:
            
            #loading video data            
            video_data_list = write.load_traj(traj)          
            if video_data_list[0] == 'TrajVersionError':
                network[0].addVideoComparison(['TrajVersionError'])
            else:          
                #starting the building of the secondary values outputs
                #for the first 3 variables, which are intergers, we use:
                #                       PE = (M-V)/V
                #       with:    V = number from video
                #                M = mean from modelisation
                # of course this would fail is V = 0, in which case we must turn to
                #                       AE = M-V...   with V = 0: AE = M
                #to which we will add a " * "
                secondary_values = []                
                for d in xrange(len(non_dist_data)):
                    if video_data_list[d] != 0:
                        secondary_values.append((non_dist_data[d].mean-video_data_list[d])/video_data_list[d])
                    else:
                        secondary_values.append(str(non_dist_data[d].mean)+'*')
                        
                #comparing video_values with output values
                video_dist_data = video_data_list[3:]
                secondary_values += checkCorrespondanceOfOutputs(video_dist_data, dist_data)

                #adding video comparison data to the network                   
                network[0].addVideoComparison(secondary_values)

                #determining main p_value
                if config.output_forward_gaps:
                    if secondary_values[4] == 'DNE':
                        d_stat.append('inf')
                    else:
                        d_stat.append(secondary_values[4])
                if config.output_lane_change:
                    if secondary_values[6] == 'DNE':        #using the before gap to calibrate
                        d_stat.append('inf')
                    else:
                        d_stat.append(secondary_values[6])
    
        return d_stat, network[0]

################################ 
#        Statistical precision analysis       
################################

def statistical_ana(concat_variables, default_values, filename, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, corridors):
    '''Finds the number of iterations needed to achieve a good confidence interval
    
    Base on the ODOT specifications:
        1. run 10 simulations and calculates the median and standard deviation for the outputs
        2. run the Student t-test while fixing the confidence interval to +/- err*mu
                   where err is the %error on the mean value, specified in the cfg file.
                   --> N = [t(1-alpha/2;N-1)*S/(err*mu)]^2 with aplha = 0.975 (bivariate 95% confidence)
            2a. calculate the confidence interval for the standard deviation
            
        3. check if N > number of simulations ran up to this point
        4. if yes, run one more simulation and repeat steps 2, 3 and 4 until "number of simulations" >= N
        
    '''
    max_itt = 25    #might consider adding it to the cfg file    
    
    text = []
   
    #set the number of runs to 10
    first_seed = parameters[1]    
    parameters[2] = 10
    iterrations_ran = 10
    
    #renaming the inpx and moving it to the output folder
    if os.path.exists(os.path.join(outputspath, "Statistical_test.inpx")) is False:
        shutil.copy(InpxPath, os.path.join(outputspath, InpxName))
        os.rename(os.path.join(outputspath, InpxName), os.path.join(outputspath, "Statistical_test.inpx"))
    
    if commands.verbose is True:
        print 'Starting the first 10 runs'
    
    if commands.mode:  #this serves to bypass Vissim while testing the code
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.generateRandomOutputs(parameters)
    else:
        Vissim = vissim.startVissim()
        if Vissim == 'StartError':
                print 'Could not start Vissim'
                sys.exit()
        else:
            loaded = vissim.loadNetwork(os.path.join(outputspath,  "Statistical_test.inpx"))
            
            if loaded == 'LoadNetError':                    
                print 'Could not load the Network'
                sys.exit()
                    
            else:                                 
                #Vissim initialisation and simulation running                                                   
                simulated = vissim.initializeSimulation(Vissim, parameters, default_values, concat_variables, commands.save_swp)
                
                if simulated is not True:
                    print simulated
                    sys.exit()
                    
                else:
                    #output treatment
                    if commands.multi is True:
                        inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose, corridors]
                        results = define.createWorkers([f for f in os.listdir(outputspath) if f.endswith("fzp")], outputs.treatVissimOutputs, inputs, commands)            
                        
                        #building the old_data            
                        for i in range(len(results)):
                            if i == 0:
                                flow            = results[i][0]
                                oppLCcount      = results[i][1]
                                manLCcount      = results[i][2]
                                forFMgap        = results[i][3]
                                oppLCagap       = results[i][4]
                                oppLCbgap       = results[i][5]
                                manLCagap       = results[i][6]
                                manLCbgap       = results[i][7]
                                forward_speeds  = results[i][8]                  
                                                   
                            else:
                                flow.addMany(                     results[i][0] )
                                oppLCcount.addMany(               results[i][1] )
                                manLCcount.addMany(               results[i][2] )
                                forFMgap.add_many_dist_list(      results[i][3] )
                                oppLCagap.add_many_dist_list(     results[i][4] )
                                oppLCbgap.add_many_dist_list(     results[i][5] )
                                manLCagap.add_many_dist_list(     results[i][6] )
                                manLCbgap.add_many_dist_list(     results[i][7] )
                                forward_speeds.add_many_dist_list(results[i][8] ) 

                    else:
                        inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose, corridors]
                        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.treatVissimOutputs([f for f in os.listdir(outputspath) if f.endswith("fzp")], inputs)
       
    #Student t-test to find the min number of runs
    t_student = t.ppf(0.975,9)
    err = config.desired_pct_error/100

    N1 = ( t_student * forFMgap.cumul_all.std / (err * forFMgap.cumul_all.mean) )**2
    N2 = ( t_student * oppLCagap.cumul_all.std / (err * oppLCagap.cumul_all.mean) )**2
    N3 = ( t_student * oppLCbgap.cumul_all.std / (err * oppLCbgap.cumul_all.mean)  )**2
    N4 = ( t_student * manLCagap.cumul_all.std / (err * manLCagap.cumul_all.mean)  )**2
    N5 = ( t_student * manLCbgap.cumul_all.std / (err * manLCbgap.cumul_all.mean)  )**2
    
    #if all variables are to be statisticaly significant to 95% confidance, they must all pass the test, thus N1...N5 must be < than the number of runs
    N =  max(N1, N2, N3, N4, N5)    
    
    #std confidence intervals             
    SCI1 = [forFMgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 ,  forFMgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI2 = [oppLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]   
    SCI3 = [oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI4 = [manLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI5 = [manLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    
    text.append(["Nbr_itt","Student-t","Std1","Mean1","N1","Std2","Mean2","N2","Std3","Mean3","N3","Std4","Mean4","N4","Std5","Mean5","N5","N","SCI1max","SCI1min","SCI2max","SCI2min","SCI3max","SCI3min","SCI4max","SCI4min","SCI5max","SCI5min"])
    text.append([iterrations_ran, t_student, forFMgap.cumul_all.std,forFMgap.cumul_all.mean, N1, oppLCagap.cumul_all.std, oppLCagap.cumul_all.mean, N2, oppLCbgap.cumul_all.std, oppLCbgap.cumul_all.mean, N3, manLCagap.cumul_all.std, manLCagap.cumul_all.mean, N4, manLCbgap.cumul_all.std, manLCbgap.cumul_all.mean, N5, N, SCI1, SCI2, SCI3, SCI4, SCI5])    
    
    while N > iterrations_ran and iterrations_ran < max_itt:
        
        if commands.verbose is True:
            print 'Starting the ' + str(iterrations_ran + 1) + "th iteration"        
        
        #building the old_data
        old_data   = [flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds]        
        
        #incrementing needed parameters                
        parameters[1] = first_seed + iterrations_ran    #need to increment the starting Rand Seed by the number of it. already ran
        parameters[2] = 1                               #need to do only one simulation
        iterrations_ran += 1
        
        #calling vissim
        if commands.mode:  #this serves to bypass Vissim while testing the code
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.generateRandomOutputs(parameters)
        else:
            
            #Initialize the new Vissim simulation
            Simulation = Vissim.Simulation
            Simulation.SetAttValue("RandSeed", parameters[1])
            Simulation.SetAttValue("NumRuns", parameters[2])
                                
            #Starting the simulation            
            Simulation.RunContinuous()                                
            
            #determining current file
            file_to_run = ["Statistical_test_" + str(iterrations_ran).zfill(3) + ".fzp"]            

            #output treatment
            inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose, corridors, old_data]
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.treatVissimOutputs(file_to_run, inputs)
        
        #generating the needed means and std
        t_student = t.ppf(0.975, iterrations_ran -1)
        N1 = ( t_student * forFMgap.cumul_all.std / (err * forFMgap.cumul_all.mean) )**2
        N2 = ( t_student * oppLCagap.cumul_all.std / (err * oppLCagap.cumul_all.mean) )**2
        N3 = ( t_student * oppLCbgap.cumul_all.std / (err * oppLCbgap.cumul_all.mean)  )**2
        N4 = ( t_student * manLCagap.cumul_all.std / (err * manLCagap.cumul_all.mean)  )**2
        N5 = ( t_student * manLCbgap.cumul_all.std / (err * manLCbgap.cumul_all.mean)  )**2
        
        N =  max(N1, N2, N3, N4, N5)        
        
        #std confidence intervals             
        SCI1 = [forFMgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 ,  forFMgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI2 = [oppLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]   
        SCI3 = [oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI4 = [manLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI5 = [manLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        
        text.append([iterrations_ran, t_student, forFMgap.cumul_all.std,forFMgap.cumul_all.mean, N1, oppLCagap.cumul_all.std, oppLCagap.cumul_all.mean, N2, oppLCbgap.cumul_all.std, oppLCbgap.cumul_all.mean, N3, manLCagap.cumul_all.std, manLCagap.cumul_all.mean, N4, manLCbgap.cumul_all.std, manLCbgap.cumul_all.mean, N5, N, SCI1, SCI2, SCI3, SCI4, SCI5])     
        
    if iterrations_ran == max_itt and commands.verbose is True:
        print "Maximum number of iterations reached - Stoping calculations and generating report"
    elif commands.verbose is True:
        print "Statistical precision achieved - generating report"     
                
    #closing vissim
    if not commands.mode: 
        closed = vissim.stopVissim(Vissim)
        if not closed:
            print 'Warning, vissim instance could not be closed, potential hold of a required vissim instance'

    '''
    MUST ADD GRAPH OPTION
    '''
    
    return text        
        

################################ 
#        Sensitivity Analisis       
################################

def setCalculatingValues(default_values, current_name, nbr_points, current_range = [], default = False):
    '''Creates the working array to work with for the current iteration 
       NB: current_range = [[min, max], pos]  | for default_values = True, current_range is not needed'''
    
    working_values = copy.deepcopy(default_values)
    if default is True:        
        points_array = [default_values[0]]
    else:
        if current_name == "CoopLnChg":
            points_array = current_range
        else:
            points_array = []
            if nbr_points > 1:
                for point in range(nbr_points):
                    points_array.append(current_range[0] + point * (current_range[1] - current_range[0]) /  (nbr_points - 1) )
            else:
                points_array.append((current_range[0] + current_range[1]) / 2)
            
    return working_values, points_array
        
def varDict(variable_names, default_values):
    '''creates a dictionary for faster search of variables'''
    
    var_dict = {}
    for i in range(len(variable_names)):
       var_dict[variable_names[i]] = [default_values[i], i]
        
    return var_dict    
        
def correctingValues(default_values, current_value, current_name, var_dict):
    '''Checks if the value is in the following list and corrects the linked values accordingly'''
    
    message = []
    working_values = copy.deepcopy(default_values)
    if current_name == "CoopLnChgSpeedDiff":
        working_values[var_dict["CoopLnChg"][1]] = True
    elif current_name == "CoopLnChgCollTm":
        working_values[var_dict["CoopLnChg"][1]] = True
    elif current_name == "LookAheadDistMin":
        if working_values[var_dict["LookAheadDistMax"][1]] < current_value:
            working_values[var_dict["LookAheadDistMax"][1]] = current_value + 0.1
            message.append('LookAheadDistMax was set to a value lower than the value set to LookAheadDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookAheadDistMax":
        if working_values[var_dict["LookAheadDistMin"][1]] > current_value:
            working_values[var_dict["LookAheadDistMin"][1]] = current_value - 0.1
            message.append('LookAheadDistMin was set to a value higher than the value set to LookAheadDistMax. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookBackDistMin":
        if working_values[var_dict["LookBackDistMax"][1]] < current_value:
            working_values[var_dict["LookBackDistMax"][1]] = current_value + 0.1
            message.append('LookBackDistMax was set to a value lower than the value set to LookBackDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookBackDistMax":
        if working_values[var_dict["LookBackDistMin"][1]] > current_value:
            working_values[var_dict["LookBackDistMin"][1]] = current_value - 0.1
            message.append('LookBackDistMin was set to a value higher than the value set to LookBackDistMax. To avoid a crash of Vissim, the value was adjusted')
        
    return working_values, message

def prepareFolderforVissimAnalysis(outputspath, folder_name, InpxName, InpxPath, default = False):
    '''creating a folder containing the files for that iteration'''
    if default is True:
        filename = 'Default_values.inpx'
        folder = 'Default_values'
    else:
        filename = folder_name + '.inpx'
        folder = folder_name

    folderpath = os.path.join(outputspath, folder)
    newfolderpath = write.createSubFolder(folderpath, folder)
    
    if newfolderpath is False:
        print 'Newfolderpath = False, must find a way to handle this issue'
        sys.exit()
    
    #renaming the inpx and moving it to the new folder
    if os.path.exists(os.path.join(folderpath, filename)) is False:
        shutil.copy(InpxPath, os.path.join(folderpath, InpxName))
        os.rename(os.path.join(folderpath, InpxName), os.path.join(folderpath, filename))
    
    return folderpath, filename

def monteCarlo_vissim(valuesVector, inputs):
    parameters     = inputs [0]
    InpxPath       = inputs [1]
    InpxName       = inputs [2]
    outputspath    = inputs [3]
    commands       = inputs [4]
    running        = inputs [5]
    sim_parameters = inputs [6]    
    
    if commands.multi:
        all_values = inputs [7]
        #find the index of the first vector included in the chunk, and compares its position with lowerbound
        lowerbound = all_values.index(valuesVector[0])
    else:
        lowerbound = 0
    
    #preparing the output
    out_valuesVector = []
     
    #analysing the values
    for value in range(len(valuesVector)):        
        #creating a folder containing the files for that iteration
                    
        folderpath, filename = prepareFolderforVissimAnalysis(outputspath, 'Point_' + str(value+lowerbound), InpxName, InpxPath)
      
        if not commands.mode:  #this serves to bypass Vissim while testing the code
            
            #Starting a Vissim instance
            if running is False:
                Vissim = vissim.startVissim()
                running = True
            
            #loading the network
            loaded = vissim.loadNetwork(Vissim, os.path.join(folderpath, filename))
            
            if loaded != 'LoadNetError':  
                #Vissim initialisation and simulation running
                vissim.initializeSimulation(Vissim, sim_parameters, valuesVector[value], parameters, commands.save_swp)
            
        out_valuesVector.append([valuesVector[value], folderpath, lowerbound])

    #closing Vissim
    if not commands.mode:
        closed = vissim.stopVissim(Vissim)
        if not closed:
            print 'Warning, vissim instance could not be closed, potential hold of a required vissim instance'            
    
    return out_valuesVector
            
def monteCarlo_outputs(valuesVector, inputs):
    parameters     = inputs [0]
    sim_parameters = inputs [1]
    outputspath    = inputs [2]
    config         = inputs [3]
    commands       = inputs [4]
    corridors      = inputs [5]
    InpxName       = inputs [6]

    concat_variables = [parameters[i].vissim_name for i in xrange(len(parameters))]
    lowerbound = valuesVector[0][2]

    if commands.multi is True:
        #opening a process output file
        if not os.path.isdir(os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles')):
            os.makedirs(os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles'))
        WorkingPath = os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles')
        multiProcTempFile = outputspath.split(os.sep)[-2] + '_ProcTempFile_points_' + str(lowerbound) + '_to_' + str(len(valuesVector)+lowerbound)
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, "Monte Carlo", config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName, None, multiProcTempFile)       
            
    #preparing the outputs    
    text = []

    for value in xrange(len(valuesVector)):
        if commands.mode:
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.generateRandomOutputs(sim_parameters, rand_seed_shake = value + lowerbound)
            success = True
        else:
            if os.path.isdir(valuesVector[value][1]):
                if [f for f in os.listdir(valuesVector[value][1]) if f.endswith("fzp")] != []:                
                    #output treatment
                    inputs = [valuesVector[value][1], config.sim_steps, config.warm_up_time, commands.verbose, corridors]
                    flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.treatVissimOutputs([f for f in os.listdir(valuesVector[value][1]) if f.endswith("fzp")], inputs)
                    success = True
                else:
                    success = False
            else:
                success = False
                
        #writing to file
        if success == True:
            text.append([value+lowerbound, valuesVector[value][0],flow.mean,oppLCcount.mean,manLCcount.mean,
                         forFMgap.cumul_all.mean,  forFMgap.cumul_all.firstQuart,  forFMgap.cumul_all.median,  forFMgap.cumul_all.thirdQuart,  forFMgap.cumul_all.std,  
                         oppLCagap.cumul_all.mean, oppLCagap.cumul_all.firstQuart, oppLCagap.cumul_all.median, oppLCagap.cumul_all.thirdQuart, oppLCagap.cumul_all.std,
                         oppLCbgap.cumul_all.mean, oppLCbgap.cumul_all.firstQuart, oppLCbgap.cumul_all.median, oppLCbgap.cumul_all.thirdQuart, oppLCbgap.cumul_all.std,
                         manLCagap.cumul_all.mean, manLCagap.cumul_all.firstQuart, manLCagap.cumul_all.median, manLCagap.cumul_all.thirdQuart, manLCagap.cumul_all.std,
                         manLCbgap.cumul_all.mean, manLCbgap.cumul_all.firstQuart, manLCbgap.cumul_all.median, manLCbgap.cumul_all.thirdQuart, manLCbgap.cumul_all.std,       
                         forward_speeds.cumul_all.mean, forward_speeds.cumul_all.firstQuart, forward_speeds.cumul_all.median, forward_speeds.cumul_all.thirdQuart, forward_speeds.cumul_all.std]) 
        
        else:
            #printing the exception in the csv file
            text.append([value+lowerbound, valuesVector[value][0],'No files found for this point. This error may be the result of an error while launching Vissim, while loading the Network or while running the simulation'])

    #security writing of chunk results while in multiprocessing
    if commands.multi is True:
        for i in range(len(text)):
            write.writeInFile(out, text[i])  
        out.close()
        
    #dumping data into a traj file for futur retrival
    ##creating folder
    if not os.path.isdir(os.path.join(outputspath.strip(os.sep+'outputs'),'traj_files')):
        os.makedirs(os.path.join(outputspath.strip(os.sep+'outputs'),'traj_files'))
    
    ## naming file
    trajfilename = outputspath.strip(os.sep+'outputs').split(os.sep)[-1] + '_points_' + str(lowerbound) + '_to_' + str(len(valuesVector)+lowerbound)
    
    ##dumping serialised data
    with open(os.path.join(outputspath.strip(os.sep+'outputs'),'traj_files', trajfilename), 'wb') as output:
        pickle.dump(define.version, output, protocol=2)
        pickle.dump(oppLCcount, output, protocol=2)
        pickle.dump(manLCcount, output, protocol=2)
        pickle.dump(flow, output, protocol=2)
        pickle.dump(forFMgap, output, protocol=2)
        pickle.dump(oppLCagap, output, protocol=2)
        pickle.dump(oppLCbgap, output, protocol=2)
        pickle.dump(manLCagap, output, protocol=2)
        pickle.dump(manLCbgap, output, protocol=2)
        pickle.dump(forward_speeds, output, protocol=2)
    
    return text

def createFirstRun_results(firstrun_results, variable):
    if variable.cumul_all.mean is not None:
        firstrun_results.append(float(variable.cumul_all.mean))
        firstrun_results.append(float(variable.cumul_all.firstQuart))
        firstrun_results.append(float(variable.cumul_all.median))
        firstrun_results.append(float(variable.cumul_all.thirdQuart))
        firstrun_results.append(float(variable.cumul_all.std))
    else:
        firstrun_results.append('---')
        firstrun_results.append('---')
        firstrun_results.append('---')
        firstrun_results.append('---')
        firstrun_results.append('---')
    return firstrun_results    
	
def createDelta(firstrun_results, variable):
    if firstrun_results != '---' and variable is not None:
        return  (variable - firstrun_results)/firstrun_results
    else:
        return '---'
        
def OAT_sensitivity(values, inputs, default = False):
    '''Runs the sensitivity analysis for a set of predetermined values
    
       note: rangevalues = [range, position in the complete list]
    '''    
    if isinstance(values[0], list) is False:
        values = [values]
        
    #unpacking inputs - should eventually be changed directly in the code
    all_values          = inputs [0]
    InpxPath            = inputs [1]
    InpxName            = inputs [2]
    outputspath         = inputs [3]
    graphspath          = inputs [4]
    config              = inputs [5]
    commands            = inputs [6]
    running             = inputs [7]
    sim_parameters      = inputs [8]
    verbose             = inputs [9]
    corridors           = inputs [10]
    if default is False:
        firstrun_results = inputs[11]

    default_values =  [all_values[i].vissim_default for i in xrange(len(all_values))]
    concat_variables = [all_values[i].vissim_name for i in xrange(len(all_values))]
    parameters = [all_values[i] for i in xrange(len(all_values))]
    all_names = [all_values[i].name for i in xrange(len(all_values))]
    
    #preparing the outputs    
    text = []
    
    if commands.multi is True and default is False:
        #opening a process output file
        WorkingPath = outputspath.strip(os.sep+'outputs')
        multiProcTempFile = outputspath.split(os.sep)[-2] + '_ProcTempFile_' + values[0][0].name
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, "Sensitivity", config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName, default_values, multiProcTempFile)       
    
    #creating a dictionnary
    var_dict = varDict(concat_variables, default_values)    

    #treating the values given in rangevalues    
    for value in xrange(len(values)):
        
        #defining the variable being worked on and the range of values it can take
        if default is True:
            current_range = []
            value_name = "Default"
            position = 0
        else:
            current_range = [values[value][0].desired_min,values[value][0].desired_max]   
            value_name = values[value][0].name
            position = all_names.index(value_name)
        
        #defining the values needed for the current cycle
        working_values, points_array = setCalculatingValues(default_values, value_name, config.nbr_points, current_range, default)

        #iterating on the number points
        for point in points_array:
            iteration_values = copy.deepcopy(working_values)
            iteration_values[position] = point
              
            #correcting the value array for variables that need to interact with others
            corrected_values, message = correctingValues(iteration_values, point, value_name, var_dict)
            
            if message != []:
                print'*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***' 
                print message
                print' occured for variable ' + str(value_name) + ' = ' + str(point) 
                print'*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'
            
            #creating a folder containing the files for that iteration
            folderpath, filename = prepareFolderforVissimAnalysis(outputspath, value_name + '_' + str(round(point,3)), InpxName, InpxPath, default)

            #Starting a Vissim instance
            if commands.mode:  #this serves to bypass Vissim while testing the code
                if default is False:
                    rand_seed_shake = 100*points_array.index(point)+value
                else:
                    rand_seed_shake = 0
                flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.generateRandomOutputs(sim_parameters, rand_seed_shake)
            
            else:
                #Vissim starting and loading network block
                if running is False: Vissim = vissim.startVissim()
                if Vissim == 'StartError':
                    if default is True:
                        print 'Could not start Vissim for default values, shutting down the analysis'
                        sys.exit()
                    else:
                        text.append([value_name, corrected_values,'Could not start Vissim'])
                        continue

                else:
                    loaded = vissim.loadNetwork(Vissim, os.path.join(folderpath, filename))
                    
                    if loaded == 'LoadNetError':                    
                        if default is True:
                            print 'Could not load the Network for default values, shutting down the analysis'
                            sys.exit()
                        else:
                            text.append([value_name, corrected_values,'Could not load the Network'])
                            continue
                        
                    else:
                        #preventing a new loading of Vissim for that iteration
                        running = True
                        
                        #Vissim initialisation and simulation running
                        simulated = vissim.initializeSimulation(Vissim, sim_parameters, corrected_values, parameters, commands.save_swp)
                        
                        if simulated is not True:
                            text.append([value_name, corrected_values,''.join(str(simulated))])    #printing the exception in the csv file
                            if default is True: firstrun_results = []                        
                            continue
                        else:
                            #output treatment
                            inputs = [folderpath, config.sim_steps, config.warm_up_time, verbose, corridors]
                            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forward_speeds = outputs.treatVissimOutputs([f for f in os.listdir(folderpath) if f.endswith("fzp")], inputs)
                            #print '*** Output treatment completed *** Runtime: ' + str(time.clock())
                            
            
            if default is True:
                firstrun_results = []
                firstrun_results = createFirstRun_results(firstrun_results, forFMgap)
                firstrun_results = createFirstRun_results(firstrun_results, oppLCagap)
                firstrun_results = createFirstRun_results(firstrun_results, oppLCbgap)
                firstrun_results = createFirstRun_results(firstrun_results, manLCagap)
                firstrun_results = createFirstRun_results(firstrun_results, manLCbgap)
                firstrun_results.append(float(flow.mean))
                firstrun_results.append(float(oppLCcount.mean))
                firstrun_results.append(float(manLCcount.mean))
                firstrun_results = createFirstRun_results(firstrun_results, forward_speeds)
                
            else:
                delta_mean_fgap           = createDelta(firstrun_results[0], forFMgap.cumul_all.mean)
                delta_firstQuart_fgap     = createDelta(firstrun_results[1], forFMgap.cumul_all.firstQuart)
                delta_median_fgaps        = createDelta(firstrun_results[2], forFMgap.cumul_all.median)
                delta_thirdQuart_fgaps    = createDelta(firstrun_results[3], forFMgap.cumul_all.thirdQuart)
                delta_std_fgaps           = createDelta(firstrun_results[4], forFMgap.cumul_all.std)                
                
                delta_mean_Aoppgap        = createDelta(firstrun_results[5], oppLCagap.cumul_all.mean)
                delta_firstQuart_Aoppgap  = createDelta(firstrun_results[6], oppLCagap.cumul_all.firstQuart)
                delta_median_Aoppgap      = createDelta(firstrun_results[7], oppLCagap.cumul_all.median)
                delta_thirdQuart_Aoppgap  = createDelta(firstrun_results[8], oppLCagap.cumul_all.thirdQuart)
                delta_std_Aoppgap         = createDelta(firstrun_results[9], oppLCagap.cumul_all.std)
                
                delta_mean_Boppgap        = createDelta(firstrun_results[10], oppLCbgap.cumul_all.mean)
                delta_firstQuart_Boppgap  = createDelta(firstrun_results[11], oppLCbgap.cumul_all.firstQuart)
                delta_median_Boppgap      = createDelta(firstrun_results[12], oppLCbgap.cumul_all.median)
                delta_thirdQuart_Boppgap  = createDelta(firstrun_results[13], oppLCbgap.cumul_all.thirdQuart)
                delta_std_Boppgap         = createDelta(firstrun_results[14], oppLCbgap.cumul_all.std)
                
                delta_mean_Amangap        = createDelta(firstrun_results[15], manLCagap.cumul_all.mean)
                delta_firstQuart_Amangap  = createDelta(firstrun_results[16], manLCagap.cumul_all.firstQuart)
                delta_median_Amangap      = createDelta(firstrun_results[17], manLCagap.cumul_all.median)
                delta_thirdQuart_Amangap  = createDelta(firstrun_results[18], manLCagap.cumul_all.thirdQuart)
                delta_std_Amangap         = createDelta(firstrun_results[19], manLCagap.cumul_all.std)
                
                delta_mean_Bmangap        = createDelta(firstrun_results[20], manLCbgap.cumul_all.mean)
                delta_firstQuart_Bmangap  = createDelta(firstrun_results[21], manLCbgap.cumul_all.firstQuart)
                delta_median_Bmangap      = createDelta(firstrun_results[22], manLCbgap.cumul_all.median)
                delta_thirdQuart_Bmangap  = createDelta(firstrun_results[23], manLCbgap.cumul_all.thirdQuart)
                delta_std_Bmangap         = createDelta(firstrun_results[24], manLCbgap.cumul_all.std)
                
                if firstrun_results[25] != 0:
                    delta_flow = (flow.mean - firstrun_results[25])/firstrun_results[25]
                else:
                    delta_flow = '---'
                
                if firstrun_results[26] != 0:
                    delta_oppLCcount = (oppLCcount.mean - firstrun_results[26])/firstrun_results[26]
                else:
                    delta_oppLCcount = '---'
                    
                if firstrun_results[27] != 0:
                    delta_manLCcount = (manLCcount.mean - firstrun_results[27])/firstrun_results[27]
                else:
                    delta_manLCcount = '---'                    
                
                delta_mean_Speeds         = createDelta(firstrun_results[28], forward_speeds.cumul_all.mean)
                delta_firstQuart_Speeds   = createDelta(firstrun_results[29], forward_speeds.cumul_all.firstQuart)
                delta_median_Speeds       = createDelta(firstrun_results[30], forward_speeds.cumul_all.median)
                delta_thirdQuart_Speeds   = createDelta(firstrun_results[31], forward_speeds.cumul_all.thirdQuart)
                delta_std_Speeds          = createDelta(firstrun_results[32], forward_speeds.cumul_all.std)
                            
            #printing graphs
            if commands.vis_save:
                variables = [forFMgap,oppLCagap,oppLCbgap,manLCagap,manLCbgap]
                variables_name =["Forward_gaps","Opportunistic_lane_change_'after'_gaps","Opportunistic_lane_change_'before'_gaps","Mandatory_lane_change_'after'_gaps","Mandatory_lane_change_'before'_gaps"]
                for var in xrange(len(variables)):
                    if default is True:
                        name = "Default_values"
                        subpath = "Default_values"
                    else:
                        name = filename.strip('.inpx')
                        subpath = value_name[:]
                    
                    write.printStatGraphs(graphspath,variables[var], name, variables_name[var], commands.fig_format, config.nbr_runs, subpath)
                    
            #writing to file
            if default is True:
                text.append(["Default_values", corrected_values, flow.mean, "---",  oppLCcount.mean, "---", manLCcount.mean, "---",
                             forFMgap.cumul_all.mean,  "---", forFMgap.cumul_all.firstQuart,  "---", forFMgap.cumul_all.median,  "---", forFMgap.cumul_all.thirdQuart,  "---", forFMgap.cumul_all.std,  "---",
                             oppLCagap.cumul_all.mean, "---", oppLCagap.cumul_all.firstQuart, "---", oppLCagap.cumul_all.median, "---", oppLCagap.cumul_all.thirdQuart, "---", oppLCagap.cumul_all.std, "---",
                             oppLCbgap.cumul_all.mean, "---", oppLCbgap.cumul_all.firstQuart, "---", oppLCbgap.cumul_all.median, "---", oppLCbgap.cumul_all.thirdQuart, "---", oppLCbgap.cumul_all.std, "---",
                             manLCagap.cumul_all.mean, "---", manLCagap.cumul_all.firstQuart, "---", manLCagap.cumul_all.median, "---", manLCagap.cumul_all.thirdQuart, "---", manLCagap.cumul_all.std, "---",
                             manLCbgap.cumul_all.mean, "---", manLCbgap.cumul_all.firstQuart, "---", manLCbgap.cumul_all.median, "---", manLCbgap.cumul_all.thirdQuart, "---", manLCbgap.cumul_all.std, "---",
                             forward_speeds.cumul_all.mean, "---", forward_speeds.cumul_all.firstQuart, "---", forward_speeds.cumul_all.median, "---", forward_speeds.cumul_all.thirdQuart, "---", forward_speeds.cumul_all.std, "---"])       

            else:
                text.append([value_name, corrected_values, flow.mean, delta_flow, oppLCcount.mean, delta_oppLCcount, manLCcount.mean, delta_manLCcount,
                             forFMgap.cumul_all.mean,  delta_mean_fgap,    forFMgap.cumul_all.firstQuart,  delta_firstQuart_fgap,    forFMgap.cumul_all.median,  delta_median_fgaps,   forFMgap.cumul_all.thirdQuart,  delta_thirdQuart_fgaps,   forFMgap.cumul_all.std,  delta_std_fgaps,
                             oppLCagap.cumul_all.mean, delta_mean_Aoppgap, oppLCagap.cumul_all.firstQuart, delta_firstQuart_Aoppgap, oppLCagap.cumul_all.median, delta_median_Aoppgap, oppLCagap.cumul_all.thirdQuart, delta_thirdQuart_Aoppgap, oppLCagap.cumul_all.std, delta_std_Aoppgap,
                             oppLCbgap.cumul_all.mean, delta_mean_Boppgap, oppLCbgap.cumul_all.firstQuart, delta_firstQuart_Boppgap, oppLCbgap.cumul_all.median, delta_median_Boppgap, oppLCbgap.cumul_all.thirdQuart, delta_thirdQuart_Boppgap, oppLCbgap.cumul_all.std, delta_std_Boppgap,
                             manLCagap.cumul_all.mean, delta_mean_Amangap, manLCagap.cumul_all.firstQuart, delta_firstQuart_Amangap, manLCagap.cumul_all.median, delta_median_Amangap, manLCagap.cumul_all.thirdQuart, delta_thirdQuart_Amangap, manLCagap.cumul_all.std, delta_std_Amangap,
                             manLCbgap.cumul_all.mean, delta_mean_Bmangap, manLCbgap.cumul_all.firstQuart, delta_firstQuart_Bmangap, manLCbgap.cumul_all.median, delta_median_Bmangap, manLCbgap.cumul_all.thirdQuart, delta_thirdQuart_Bmangap, manLCbgap.cumul_all.std, delta_std_Bmangap,       
                             forward_speeds.cumul_all.mean, delta_mean_Speeds, forward_speeds.cumul_all.firstQuart, delta_firstQuart_Speeds, forward_speeds.cumul_all.median, delta_median_Speeds, forward_speeds.cumul_all.thirdQuart, delta_thirdQuart_Speeds, forward_speeds.cumul_all.std, delta_std_Speeds]) 
                         
        #breaking the outer loop because the default only needs to be ran once
        if default is True:
            break

    if not commands.mode:
        closed = vissim.stopVissim(Vissim)
        if not closed:
            print 'Warning, vissim instance could not be closed, potential hold of a required vissim instance'
    
    #security writing of chunk results while in multiprocessing
    if commands.multi is True and default is False:
        for i in range(len(text)):
            write.writeInFile(out, text[i])  
        out.close()
        
    if default is True:  
        return text, firstrun_results
    else:
        return text