# -*- coding: utf-8 -*-
'''
Created on Thu Jul 10 14:43:44 2014

@author: Laurent
'''

################################ 
#        Importing dependencies       
################################ 
#Natives
import os, shutil, sys, copy
from scipy.stats import t, chi2
import cPickle as pickle

#Internal
import pvc_write      as write
import pvc_vissim     as vissim
import pvc_outputs    as outputs
import pvc_calibTools as calibTools
import pvc_workers    as workers
import pvc_configure  as configure

################################ 
#        Calibration analysis       
################################
def runVissimForCalibrationAnalysis(network, inputs):
    '''Note: Vissim is passed in the Network class variable 'network' 
       
       One instance of runVissimForCalibrationAnalysis is started for each studied
       Network
    '''
    
    #unpacking inputs
    config           = inputs[0]
    variables        = inputs[1]
    parameters       = inputs[2]
    point_folderpath = inputs[3]
    multi_networks   = inputs[4]
    
    Vissim = vissim.startVissim()
    
    if multi_networks is True:
        #if we are treating more than one network, than we subdivide the point folder into network folders
        if not os.path.isdir(os.path.join(point_folderpath,os.path.splitext(network[0].inpx_path.split(os.sep)[-1])[0])):
            os.mkdir(os.path.join(point_folderpath,os.path.splitext(network[0].inpx_path.split(os.sep)[-1])[0]))

        final_inpx_path = os.path.join(point_folderpath,os.path.splitext(network[0].inpx_path.split(os.sep)[-1])[0])
        shutil.move(os.path.join(point_folderpath,network[0].inpx_path.split(os.sep)[-1]),os.path.join(final_inpx_path,network[0].inpx_path.split(os.sep)[-1]))    

    else:
        final_inpx_path = copy.deepcopy(point_folderpath)

    #retry the start vissim after having killed all vissims - only owrks if not in multi network mode    
    if isinstance(Vissim, str) and multi_networks is False:
        vissim.isVissimRunning(True)
        Vissim = vissim.startVissim()        
    
    #check for starting error
    if isinstance(Vissim, str):           
        for traj in network[0].traj_paths:        
            network[0].addVideoComparison(['StartError'])
            return False, network[0], ['N/A' for i in xrange(parameters[2])]

    #load the network
    load = vissim.loadNetwork(Vissim, os.path.join(final_inpx_path,network[0].inpx_path.split(os.sep)[-1]), err_file=True)    

    #check for network loading error
    if load is not True:
        for traj in network[0].traj_paths:        
            network[0].addVideoComparison(['LoadNetError'])
            return False, network[0], ['N/A' for i in xrange(parameters[2])]
    
    values = []
    for var in variables:
        values.append(var.point)
           
    #Initializing and running the simulation
    simulated = vissim.initializeSimulation(Vissim, parameters, values, variables, err_file_path=final_inpx_path)
    
    if simulated is not True:
        for traj in network[0].traj_paths:
            network[0].addVideoComparison(['SimulationError'])
            vissim.stopVissim(Vissim)
        return False, network[0], ['N/A' for i in xrange(parameters[2])]
             
    else:
        d_stat = []
        rejected_files = []
        #import pdb;pdb.set_trace()
        #treating the outputs
        inputs = [final_inpx_path, False, network[0].corridors, outputs.Derived_data(), config]
        file_list = [f for f in os.listdir(final_inpx_path) if f.endswith('fzp')]
        if len(file_list) > 1 and multi_networks is False:
            commands = workers.FalseCommands()
            packedStatsLists = workers.createWorkers(file_list, outputs.treatVissimOutputs, inputs, commands, defineNbrProcess = 2)

            vissim_data = packedStatsLists[0]

            for stat in xrange(1,len(packedStatsLists)):
                outputs.Derived_data.concat(vissim_data, packedStatsLists[stat])

        else:
            vissim_data = outputs.treatVissimOutputs(file_list, inputs)
        
        if config.ks_switch:
            #verifying the validity of the distributions
            if config.output_forward_gaps:
                if len(vissim_data.forFMgap.distributions) > 1:
                    rejected = calibTools.filter_dist_with_ks(calibTools.treat_stats_list(vissim_data.forFMgap), config.ks_threshold)
                else:
                    rejected = []
                    
            if config.output_lane_change:
                if len(vissim_data.oppLCbgap.distributions) > 1:
                    rejected = calibTools.filter_dist_with_ks(calibTools.treat_stats_list(vissim_data.oppLCbgap), config.ks_threshold)    #using before lane change gaps
                else:
                    rejected = []
                    
            #adjustment
            vissim_data.popManyOutputList(['flow', 'oppLCcount', 'manLCcount', 'forFMgap', 'oppLCagap', 'oppLCbgap', 'manLCagap', 'manLCbgap', 'forSpeeds'], rejected)
    
            #memorizing bad files
            for r in reversed(rejected):
                rejected_files.append(file_list[r])
                
            #running new data
            goal = parameters[2]
            total_retries = 5 ###this could be moved to the cfg file
            retry = 0
            first_seed = parameters[1]
            new_seed = first_seed + goal*parameters[5]
            
            while len(vissim_data.forFMgap.distributions) < goal and retry <= total_retries:
                #fixing vissim parameters            
                nbr_run_this_try = len(rejected)
                parameters[2] = nbr_run_this_try  #number of rerun
                parameters[1] = new_seed
            
                #Initializing and running the simulation
                simulated = vissim.initializeSimulation(Vissim, parameters, values, variables, err_file_path=final_inpx_path)        
            
                if simulated is True:
                    #treating the outputs
                    inputs = [final_inpx_path, False, network[0].corridors, vissim_data, config]
                    file_list = [f for f in os.listdir(final_inpx_path) if f.endswith('fzp')]
                    vissim_data = outputs.treatVissimOutputs(file_list[-nbr_run_this_try:], inputs)
                    
                    #verifying the validity of the distributions
                    if config.output_forward_gaps:
                        if len(vissim_data.forFMgap.distributions) > 1:
                            rejected = calibTools.filter_dist_with_ks(calibTools.treat_stats_list(vissim_data.forFMgap), config.ks_threshold)
                        else:
                            rejected = []
                            
                    if config.output_lane_change:
                        if len(vissim_data.oppLCbgap.distributions) > 1:
                            rejected = calibTools.filter_dist_with_ks(calibTools.treat_stats_list(vissim_data.oppLCbgap), config.ks_threshold)    #using before lane change gaps
                        else:
                            rejected = []
                            
                    #adjustment
                    vissim_data.popManyOutputList(['flow', 'oppLCcount', 'manLCcount', 'forFMgap', 'oppLCagap', 'oppLCbgap', 'manLCagap', 'manLCbgap', 'forSpeeds'], rejected)

                    #memorizing bad files
                    for r in reversed(rejected):
                        rejected_files.append(file_list[r]) 
                    
                #fixing while loop info
                new_seed += nbr_run_this_try*parameters[5]
                retry += 1
    
            #moving unwanted file        
            if len(rejected_files) > 0:
                if not os.path.exists(os.path.join(final_inpx_path, 'rejected_tests')):
                    os.makedirs(os.path.join(final_inpx_path, 'rejected_tests'))
                for rejected_file in rejected_files:
                    shutil.move(os.path.join(final_inpx_path,rejected_file),os.path.join(final_inpx_path,'rejected_tests',rejected_file))
                    
                    #moving associated error files if they exist
                    if os.path.exists(os.path.join(final_inpx_path,os.path.splitext(rejected_file)[0] + '.err')):
                        shutil.move(os.path.join(final_inpx_path,os.path.splitext(rejected_file)[0] + '.err'), os.path.join(final_inpx_path,'rejected_tests',os.path.splitext(rejected_file)[0] + '.err'))
                            
                    #removing the unwanted files from the file list
                    file_list.remove(rejected_file)
                    
                #creating a storage file for seed information
                with open(os.path.join(final_inpx_path,'rejected_tests','info.seeds'),'w') as seed:
                    seed.write('first seed:      '+str(first_seed)+'\n'
                               'seed increment : '+str(parameters[5])+'\n'
                               '\n')
                    for s in xrange(len(file_list)+len(rejected_files)):
                        seed.write('seed_'+str(s+1)+': '+str(parameters[1]+s*parameters[5])+'\n')

        seed_nums = outputs.extract_num_from_fzp_list(file_list)
                    
        non_dist_data = [vissim_data.oppLCcount, vissim_data.manLCcount, vissim_data.flow]
        dist_data = [vissim_data.forFMgap, vissim_data.oppLCagap, vissim_data.oppLCbgap, vissim_data.manLCagap, vissim_data.manLCbgap, vissim_data.forSpeeds]
        
        #setting video values
        for traj in network[0].traj_paths:
            
            #loading video data            
            video_data = write.load_traj(traj)          
            if video_data == 'TrajVersionError':
                network[0].addVideoComparison(['TrajVersionError'])
            else:
                non_dist_video_data = [video_data.oppLCcount, video_data.manLCcount, video_data.flow]
                dist_video_data = [video_data.forFMgap, video_data.oppLCagap, video_data.oppLCbgap, video_data.manLCagap, video_data.manLCbgap, video_data.forSpeeds]
                #starting the building of the secondary values outputs
                #for the first 3 variables, which are intergers, we use:
                #                       PE = (M-V)/V
                #       with:    V = number from video
                #                M = mean from modelisation
                # of course this would fail is V = 0, in which case we must turn to
                #                       AE = M-V...   with V = 0: AE = M
                #to which we will add a ' * '
                secondary_values = []
                for d in xrange(len(non_dist_data)):
                    if non_dist_video_data[d].mean != 0:
                        secondary_values.append([non_dist_data[d].mean, (non_dist_data[d].mean-non_dist_video_data[d].mean)/non_dist_video_data[d].mean])
                    else:
                        if non_dist_data[d].mean is not None and non_dist_data[d].mean != 0:                            
                            secondary_values.append([non_dist_data[d].mean, str(non_dist_data[d].mean)+'*'])                           
                        else:
                            secondary_values.append(['0.00', '0.00*'])

                #comparing video_values with output values
                secondary_values += calibTools.checkCorrespondanceOfOutputs(dist_video_data, dist_data, parameters[0], config.fps)

                #adding video comparison data to the network                   
                network[0].addVideoComparison(secondary_values)

                #verifying the constraints
                num, dp, a0 = outputs.search_folder_for_error_files(final_inpx_path)
                c0, c1, c2 = outputs.convert_errors_to_constraints(config, num, dp, a0)

                #determining main p_value
                #
                #at this point, secondary_value looks like:
                #    [[oppLCgap, oppLCgap_delta], [manLCgap, manLCgap_delta], [flow, flow_delta], ...
                #         0-0          0-1            1-0          1-1         2-0      2-1
                #           
                #      forFMgap, forFMgap_KS_d, oppLCagap, oppLCagap_KS_d, oppLCbgap, oppLCbgap_KS_d, ...
                #         3            4              5          6              7          8
                # 
                #      manLCagap, manLCagap_KS_d, manLCbgap, manLCbgap_KS_d, speeds, speeds_KS_d]
                #         9           10             11         12             13         14
                #
                if config.output_forward_gaps:
                    if secondary_values[4] == 'DNE':
                        d_stat.append(['inf', c0, c1, c2])
                    else:
                        d_stat.append([secondary_values[4], c0, c1, c2])
                    write.plot_dists(final_inpx_path, traj.split(os.sep)[-1].strip('.traj'), dist_video_data[0], dist_data[0], secondary_values[4], parameters[0], config.fps, seed_nums)
                        
                if config.output_lane_change:
                    if secondary_values[8] == 'DNE':        #using the before gap to calibrate
                        d_stat.append(['inf', c0, c1, c2])
                    else:
                        d_stat.append([secondary_values[8], c0, c1, c2])
                    write.plot_dists(final_inpx_path, traj.split(os.sep)[-1].strip('.traj'), dist_video_data[2], dist_data[2], secondary_values[6], parameters[0], config.fps, seed_nums)
        
        vissim.stopVissim(Vissim)
        return d_stat, network[0], seed_nums

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
        4. if yes, run one more simulation and repeat steps 2, 3 and 4 until 'number of simulations' >= N
        
    '''
    max_itt = 25    #might consider adding it to the cfg file    
    
    text = []
   
    #set the number of runs to 10
    first_seed = parameters[1]    
    parameters[2] = 10
    iterrations_ran = 10
    
    #renaming the inpx and moving it to the output folder
    if os.path.exists(os.path.join(outputspath, 'Statistical_test.inpx')) is False:
        shutil.copy(InpxPath, os.path.join(outputspath, InpxName))
        os.rename(os.path.join(outputspath, InpxName), os.path.join(outputspath, 'Statistical_test.inpx'))
    
    if commands.verbose is True:
        print 'Starting the first 10 runs'
    
    if commands.mode:  #this serves to bypass Vissim while testing the code
        Outputs = outputs.generateRandomOutputs(parameters)
    else:
        Vissim = vissim.startVissim()
        if Vissim == 'StartError':
                print 'Could not start Vissim'
                sys.exit()
        else:
            loaded = vissim.loadNetwork(os.path.join(outputspath,  'Statistical_test.inpx'))
            
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
                        inputs = [outputspath, commands.verbose, corridors, outputs.Derived_data(), config]
                        results = workers.createWorkers([f for f in os.listdir(outputspath) if f.endswith('fzp')], outputs.treatVissimOutputs, inputs, commands)            
                        
                        Outputs = results[0]
                        #building the old_data            
                        for i in range(len(results)):
                            outputs.Derived_data.concat(Outputs, results[i])

                    else:
                        inputs = [outputspath, commands.verbose, corridors, outputs.Derived_data(), config]
                        Outputs = outputs.treatVissimOutputs([f for f in os.listdir(outputspath) if f.endswith('fzp')], inputs)
       
    #Student t-test to find the min number of runs
    t_student = t.ppf(0.975,9)
    err = config.desired_pct_error/100

    N1 = ( t_student * Outputs.forFMgap.cumul_all.std / (err * Outputs.forFMgap.cumul_all.mean) )**2
    N2 = ( t_student * Outputs.oppLCagap.cumul_all.std / (err * Outputs.oppLCagap.cumul_all.mean) )**2
    N3 = ( t_student * Outputs.oppLCbgap.cumul_all.std / (err * Outputs.oppLCbgap.cumul_all.mean)  )**2
    N4 = ( t_student * Outputs.manLCagap.cumul_all.std / (err * Outputs.manLCagap.cumul_all.mean)  )**2
    N5 = ( t_student * Outputs.manLCbgap.cumul_all.std / (err * Outputs.manLCbgap.cumul_all.mean)  )**2
    
    #if all variables are to be statisticaly significant to 95% confidance, they must all pass the test, thus N1...N5 must be < than the number of runs
    N =  max(N1, N2, N3, N4, N5)    
    
    #std confidence intervals             
    SCI1 = [Outputs.forFMgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 ,  Outputs.forFMgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI2 = [Outputs.oppLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.oppLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]   
    SCI3 = [Outputs.oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI4 = [Outputs.manLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.manLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI5 = [Outputs.manLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.manLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    
    text.append(['Nbr_itt','Student-t','Std1','Mean1','N1','Std2','Mean2','N2','Std3','Mean3','N3','Std4','Mean4','N4','Std5','Mean5','N5','N','SCI1max','SCI1min','SCI2max','SCI2min','SCI3max','SCI3min','SCI4max','SCI4min','SCI5max','SCI5min'])
    text.append([iterrations_ran, t_student, Outputs.forFMgap.cumul_all.std,Outputs.forFMgap.cumul_all.mean, N1, Outputs.oppLCagap.cumul_all.std, Outputs.oppLCagap.cumul_all.mean, N2, Outputs.oppLCbgap.cumul_all.std, Outputs.oppLCbgap.cumul_all.mean, N3, Outputs.manLCagap.cumul_all.std, Outputs.manLCagap.cumul_all.mean, N4, Outputs.manLCbgap.cumul_all.std, Outputs.manLCbgap.cumul_all.mean, N5, N, SCI1, SCI2, SCI3, SCI4, SCI5])    
    
    while N > iterrations_ran and iterrations_ran < max_itt:
        
        if commands.verbose is True:
            print 'Starting the ' + str(iterrations_ran + 1) + 'th iteration'        
        
        #incrementing needed parameters                
        parameters[1] = first_seed + iterrations_ran    #need to increment the starting Rand Seed by the number of it. already ran
        parameters[2] = 1                               #need to do only one simulation
        iterrations_ran += 1
        
        #calling vissim
        if commands.mode:  #this serves to bypass Vissim while testing the code
            Outputs = outputs.generateRandomOutputs(parameters)
        else:
            
            #Initialize the new Vissim simulation
            Simulation = Vissim.Simulation
            Simulation.SetAttValue('RandSeed', parameters[1])
            Simulation.SetAttValue('NumRuns', parameters[2])
                                
            #Starting the simulation            
            Simulation.RunContinuous()                                
            
            #determining current file
            file_to_run = ['Statistical_test_' + str(iterrations_ran).zfill(3) + '.fzp']            

            #output treatment
            inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose, corridors, Outputs, config]
            Outputs = outputs.treatVissimOutputs(file_to_run, inputs)
        
        #generating the needed means and std
        t_student = t.ppf(0.975, iterrations_ran -1)
        N1 = ( t_student * Outputs.forFMgap.cumul_all.std / (err * Outputs.forFMgap.cumul_all.mean) )**2
        N2 = ( t_student * Outputs.oppLCagap.cumul_all.std / (err * Outputs.oppLCagap.cumul_all.mean) )**2
        N3 = ( t_student * Outputs.oppLCbgap.cumul_all.std / (err * Outputs.oppLCbgap.cumul_all.mean)  )**2
        N4 = ( t_student * Outputs.manLCagap.cumul_all.std / (err * Outputs.manLCagap.cumul_all.mean)  )**2
        N5 = ( t_student * Outputs.manLCbgap.cumul_all.std / (err * Outputs.manLCbgap.cumul_all.mean)  )**2
        
        N =  max(N1, N2, N3, N4, N5)        
        
        #std confidence intervals             
        SCI1 = [Outputs.forFMgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 ,  Outputs.forFMgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI2 = [Outputs.oppLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.oppLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]   
        SCI3 = [Outputs.oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI4 = [Outputs.manLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.manLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI5 = [Outputs.manLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , Outputs.manLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        
        text.append([iterrations_ran, t_student, Outputs.forFMgap.cumul_all.std,Outputs.forFMgap.cumul_all.mean, N1, Outputs.oppLCagap.cumul_all.std, Outputs.oppLCagap.cumul_all.mean, N2, Outputs.oppLCbgap.cumul_all.std, Outputs.oppLCbgap.cumul_all.mean, N3, Outputs.manLCagap.cumul_all.std, Outputs.manLCagap.cumul_all.mean, N4, Outputs.manLCbgap.cumul_all.std, Outputs.manLCbgap.cumul_all.mean, N5, N, SCI1, SCI2, SCI3, SCI4, SCI5])     
        
    if iterrations_ran == max_itt and commands.verbose is True:
        print 'Maximum number of iterations reached - Stoping calculations and generating report'
    elif commands.verbose is True:
        print 'Statistical precision achieved - generating report'     
                
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
        if current_name == 'CoopLnChg':
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
    if current_name == 'CoopLnChgSpeedDiff':
        working_values[var_dict['CoopLnChg'][1]] = True
    elif current_name == 'CoopLnChgCollTm':
        working_values[var_dict['CoopLnChg'][1]] = True
    elif current_name == 'LookAheadDistMin':
        if working_values[var_dict['LookAheadDistMax'][1]] < current_value:
            working_values[var_dict['LookAheadDistMax'][1]] = current_value + 0.1
            message.append('LookAheadDistMax was set to a value lower than the value set to LookAheadDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == 'LookAheadDistMax':
        if working_values[var_dict['LookAheadDistMin'][1]] > current_value:
            working_values[var_dict['LookAheadDistMin'][1]] = current_value - 0.1
            message.append('LookAheadDistMin was set to a value higher than the value set to LookAheadDistMax. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == 'LookBackDistMin':
        if working_values[var_dict['LookBackDistMax'][1]] < current_value:
            working_values[var_dict['LookBackDistMax'][1]] = current_value + 0.1
            message.append('LookBackDistMax was set to a value lower than the value set to LookBackDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == 'LookBackDistMax':
        if working_values[var_dict['LookBackDistMin'][1]] > current_value:
            working_values[var_dict['LookBackDistMin'][1]] = current_value - 0.1
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
            
def monteCarlo_outputs(valuesVector, other_inputs):
    parameters     = other_inputs [0]
    sim_parameters = other_inputs [1]
    outputspath    = other_inputs [2]
    config         = other_inputs [3]
    commands       = other_inputs [4]
    corridors      = other_inputs [5]
    InpxName       = other_inputs [6]

    concat_variables = [parameters[i].vissim_name for i in xrange(len(parameters))]
    lowerbound = valuesVector[0][2]

    if commands.multi is True:
        #opening a process output file
        if not os.path.isdir(os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles')):
            os.makedirs(os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles'))
        WorkingPath = os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles')
        multiProcTempFile = outputspath.split(os.sep)[-2] + '_ProcTempFile_points_' + str(lowerbound) + '_to_' + str(len(valuesVector)+lowerbound)
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, 'Monte Carlo', config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName, None, multiProcTempFile)       
            
    #preparing the outputs    
    text = []

    for value in xrange(len(valuesVector)):
        if commands.mode:
            Outputs = outputs.generateRandomOutputs(sim_parameters, rand_seed_shake = value + lowerbound)
            success = True
        else:
            if os.path.isdir(valuesVector[value][1]):
                if [f for f in os.listdir(valuesVector[value][1]) if f.endswith('fzp')] != []:                
                    #output treatment
                    inputs = [valuesVector[value][1], commands.verbose, corridors, outputs.Derived_data(), config]
                    Outputs = outputs.treatVissimOutputs([f for f in os.listdir(valuesVector[value][1]) if f.endswith('fzp')], inputs)
                    success = True
                else:
                    success = False
            else:
                success = False
                
        #writing to file
        if success == True:
            text.append([value+lowerbound, valuesVector[value][0],Outputs.flow.mean,Outputs.oppLCcount.mean,Outputs.manLCcount.mean,
                         Outputs.forFMgap.cumul_all.mean,  Outputs.forFMgap.cumul_all.firstQuart,  Outputs.forFMgap.cumul_all.median,  Outputs.forFMgap.cumul_all.thirdQuart,  Outputs.forFMgap.cumul_all.std,  
                         Outputs.oppLCagap.cumul_all.mean, Outputs.oppLCagap.cumul_all.firstQuart, Outputs.oppLCagap.cumul_all.median, Outputs.oppLCagap.cumul_all.thirdQuart, Outputs.oppLCagap.cumul_all.std,
                         Outputs.oppLCbgap.cumul_all.mean, Outputs.oppLCbgap.cumul_all.firstQuart, Outputs.oppLCbgap.cumul_all.median, Outputs.oppLCbgap.cumul_all.thirdQuart, Outputs.oppLCbgap.cumul_all.std,
                         Outputs.manLCagap.cumul_all.mean, Outputs.manLCagap.cumul_all.firstQuart, Outputs.manLCagap.cumul_all.median, Outputs.manLCagap.cumul_all.thirdQuart, Outputs.manLCagap.cumul_all.std,
                         Outputs.manLCbgap.cumul_all.mean, Outputs.manLCbgap.cumul_all.firstQuart, Outputs.manLCbgap.cumul_all.median, Outputs.manLCbgap.cumul_all.thirdQuart, Outputs.manLCbgap.cumul_all.std,       
                         Outputs.forSpeeds.cumul_all.mean, Outputs.forSpeeds.cumul_all.firstQuart, Outputs.forSpeeds.cumul_all.median, Outputs.forSpeeds.cumul_all.thirdQuart, Outputs.forSpeeds.cumul_all.std]) 
        
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
        pickle.dump(configure.Version(), output, protocol=2)
        pickle.dump(Outputs, output, protocol=2)
    
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
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, 'Sensitivity', config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName, default_values, multiProcTempFile)       
    
    #creating a dictionnary
    var_dict = varDict(concat_variables, default_values)    

    #treating the values given in rangevalues    
    for value in xrange(len(values)):
        
        #defining the variable being worked on and the range of values it can take
        if default is True:
            current_range = []
            value_name = 'Default'
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
                Outputs = outputs.generateRandomOutputs(sim_parameters, rand_seed_shake)
            
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
                            inputs = [folderpath, verbose, corridors, outputs.Derived_data(), config]
                            Outputs = outputs.treatVissimOutputs([f for f in os.listdir(folderpath) if f.endswith('fzp')], inputs)
                            #print '*** Output treatment completed *** Runtime: ' + str(time.clock())
                            
            
            if default is True:
                firstrun_results = []
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.forFMgap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.oppLCagap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.oppLCbgap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.manLCagap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.manLCbgap)
                firstrun_results.append(float(Outputs.flow.mean))
                firstrun_results.append(float(Outputs.oppLCcount.mean))
                firstrun_results.append(float(Outputs.manLCcount.mean))
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.forSpeeds)
                
            else:
                delta_mean_fgap           = createDelta(firstrun_results[0], Outputs.forFMgap.cumul_all.mean)
                delta_firstQuart_fgap     = createDelta(firstrun_results[1], Outputs.forFMgap.cumul_all.firstQuart)
                delta_median_fgaps        = createDelta(firstrun_results[2], Outputs.forFMgap.cumul_all.median)
                delta_thirdQuart_fgaps    = createDelta(firstrun_results[3], Outputs.forFMgap.cumul_all.thirdQuart)
                delta_std_fgaps           = createDelta(firstrun_results[4], Outputs.forFMgap.cumul_all.std)                
                
                delta_mean_Aoppgap        = createDelta(firstrun_results[5], Outputs.oppLCagap.cumul_all.mean)
                delta_firstQuart_Aoppgap  = createDelta(firstrun_results[6], Outputs.oppLCagap.cumul_all.firstQuart)
                delta_median_Aoppgap      = createDelta(firstrun_results[7], Outputs.oppLCagap.cumul_all.median)
                delta_thirdQuart_Aoppgap  = createDelta(firstrun_results[8], Outputs.oppLCagap.cumul_all.thirdQuart)
                delta_std_Aoppgap         = createDelta(firstrun_results[9], Outputs.oppLCagap.cumul_all.std)
                
                delta_mean_Boppgap        = createDelta(firstrun_results[10], Outputs.oppLCbgap.cumul_all.mean)
                delta_firstQuart_Boppgap  = createDelta(firstrun_results[11], Outputs.oppLCbgap.cumul_all.firstQuart)
                delta_median_Boppgap      = createDelta(firstrun_results[12], Outputs.oppLCbgap.cumul_all.median)
                delta_thirdQuart_Boppgap  = createDelta(firstrun_results[13], Outputs.oppLCbgap.cumul_all.thirdQuart)
                delta_std_Boppgap         = createDelta(firstrun_results[14], Outputs.oppLCbgap.cumul_all.std)
                
                delta_mean_Amangap        = createDelta(firstrun_results[15], Outputs.manLCagap.cumul_all.mean)
                delta_firstQuart_Amangap  = createDelta(firstrun_results[16], Outputs.manLCagap.cumul_all.firstQuart)
                delta_median_Amangap      = createDelta(firstrun_results[17], Outputs.manLCagap.cumul_all.median)
                delta_thirdQuart_Amangap  = createDelta(firstrun_results[18], Outputs.manLCagap.cumul_all.thirdQuart)
                delta_std_Amangap         = createDelta(firstrun_results[19], Outputs.manLCagap.cumul_all.std)
                
                delta_mean_Bmangap        = createDelta(firstrun_results[20], Outputs.manLCbgap.cumul_all.mean)
                delta_firstQuart_Bmangap  = createDelta(firstrun_results[21], Outputs.manLCbgap.cumul_all.firstQuart)
                delta_median_Bmangap      = createDelta(firstrun_results[22], Outputs.manLCbgap.cumul_all.median)
                delta_thirdQuart_Bmangap  = createDelta(firstrun_results[23], Outputs.manLCbgap.cumul_all.thirdQuart)
                delta_std_Bmangap         = createDelta(firstrun_results[24], Outputs.manLCbgap.cumul_all.std)
                
                if firstrun_results[25] != 0:
                    delta_flow = (Outputs.flow.mean - firstrun_results[25])/firstrun_results[25]
                else:
                    delta_flow = '---'
                
                if firstrun_results[26] != 0:
                    delta_oppLCcount = (Outputs.oppLCcount.mean - firstrun_results[26])/firstrun_results[26]
                else:
                    delta_oppLCcount = '---'
                    
                if firstrun_results[27] != 0:
                    delta_manLCcount = (Outputs.manLCcount.mean - firstrun_results[27])/firstrun_results[27]
                else:
                    delta_manLCcount = '---'                    
                
                delta_mean_Speeds         = createDelta(firstrun_results[28], Outputs.forSpeeds.cumul_all.mean)
                delta_firstQuart_Speeds   = createDelta(firstrun_results[29], Outputs.forSpeeds.cumul_all.firstQuart)
                delta_median_Speeds       = createDelta(firstrun_results[30], Outputs.forSpeeds.cumul_all.median)
                delta_thirdQuart_Speeds   = createDelta(firstrun_results[31], Outputs.forSpeeds.cumul_all.thirdQuart)
                delta_std_Speeds          = createDelta(firstrun_results[32], Outputs.forSpeeds.cumul_all.std)
                            
            #printing graphs
            if commands.vis_save:
                variables = [Outputs.forFMgap,Outputs.oppLCagap,Outputs.oppLCbgap,Outputs.manLCagap,Outputs.manLCbgap]
                variables_name = ['Forward_gaps','Opportunistic_lane_change_after_gaps','Opportunistic_lane_change_before_gaps','Mandatory_lane_change_after_gaps','Mandatory_lane_change_before_gaps']
                for var in xrange(len(variables)):
                    if default is True:
                        name = 'Default_values'
                        subpath = 'Default_values'
                    else:
                        name = filename.strip('.inpx')
                        subpath = value_name[:]
                    
                    write.printStatGraphs(graphspath,variables[var], name, variables_name[var], commands.fig_format, config.nbr_runs, subpath)
                    
            #writing to file
            if default is True:
                text.append(['Default_values', corrected_values, Outputs.flow.mean, '---',  Outputs.oppLCcount.mean, '---', Outputs.manLCcount.mean, '---',
                             Outputs.forFMgap.cumul_all.mean,  '---', Outputs.forFMgap.cumul_all.firstQuart,  '---', Outputs.forFMgap.cumul_all.median,  '---', Outputs.forFMgap.cumul_all.thirdQuart,  '---', Outputs.forFMgap.cumul_all.std,  '---',
                             Outputs.oppLCagap.cumul_all.mean, '---', Outputs.oppLCagap.cumul_all.firstQuart, '---', Outputs.oppLCagap.cumul_all.median, '---', Outputs.oppLCagap.cumul_all.thirdQuart, '---', Outputs.oppLCagap.cumul_all.std, '---',
                             Outputs.oppLCbgap.cumul_all.mean, '---', Outputs.oppLCbgap.cumul_all.firstQuart, '---', Outputs.oppLCbgap.cumul_all.median, '---', Outputs.oppLCbgap.cumul_all.thirdQuart, '---', Outputs.oppLCbgap.cumul_all.std, '---',
                             Outputs.manLCagap.cumul_all.mean, '---', Outputs.manLCagap.cumul_all.firstQuart, '---', Outputs.manLCagap.cumul_all.median, '---', Outputs.manLCagap.cumul_all.thirdQuart, '---', Outputs.manLCagap.cumul_all.std, '---',
                             Outputs.manLCbgap.cumul_all.mean, '---', Outputs.manLCbgap.cumul_all.firstQuart, '---', Outputs.manLCbgap.cumul_all.median, '---', Outputs.manLCbgap.cumul_all.thirdQuart, '---', Outputs.manLCbgap.cumul_all.std, '---',
                             Outputs.forSpeeds.cumul_all.mean, '---', Outputs.forSpeeds.cumul_all.firstQuart, '---', Outputs.forSpeeds.cumul_all.median, '---', Outputs.forSpeeds.cumul_all.thirdQuart, '---', Outputs.forSpeeds.cumul_all.std, '---'])       

            else:
                text.append([value_name, corrected_values, Outputs.flow.mean, delta_flow, Outputs.oppLCcount.mean, delta_oppLCcount, Outputs.manLCcount.mean, delta_manLCcount,
                             Outputs.forFMgap.cumul_all.mean,  delta_mean_fgap,    Outputs.forFMgap.cumul_all.firstQuart,  delta_firstQuart_fgap,    Outputs.forFMgap.cumul_all.median,  delta_median_fgaps,   Outputs.forFMgap.cumul_all.thirdQuart,  delta_thirdQuart_fgaps,   Outputs.forFMgap.cumul_all.std,  delta_std_fgaps,
                             Outputs.oppLCagap.cumul_all.mean, delta_mean_Aoppgap, Outputs.oppLCagap.cumul_all.firstQuart, delta_firstQuart_Aoppgap, Outputs.oppLCagap.cumul_all.median, delta_median_Aoppgap, Outputs.oppLCagap.cumul_all.thirdQuart, delta_thirdQuart_Aoppgap, Outputs.oppLCagap.cumul_all.std, delta_std_Aoppgap,
                             Outputs.oppLCbgap.cumul_all.mean, delta_mean_Boppgap, Outputs.oppLCbgap.cumul_all.firstQuart, delta_firstQuart_Boppgap, Outputs.oppLCbgap.cumul_all.median, delta_median_Boppgap, Outputs.oppLCbgap.cumul_all.thirdQuart, delta_thirdQuart_Boppgap, Outputs.oppLCbgap.cumul_all.std, delta_std_Boppgap,
                             Outputs.manLCagap.cumul_all.mean, delta_mean_Amangap, Outputs.manLCagap.cumul_all.firstQuart, delta_firstQuart_Amangap, Outputs.manLCagap.cumul_all.median, delta_median_Amangap, Outputs.manLCagap.cumul_all.thirdQuart, delta_thirdQuart_Amangap, Outputs.manLCagap.cumul_all.std, delta_std_Amangap,
                             Outputs.manLCbgap.cumul_all.mean, delta_mean_Bmangap, Outputs.manLCbgap.cumul_all.firstQuart, delta_firstQuart_Bmangap, Outputs.manLCbgap.cumul_all.median, delta_median_Bmangap, Outputs.manLCbgap.cumul_all.thirdQuart, delta_thirdQuart_Bmangap, Outputs.manLCbgap.cumul_all.std, delta_std_Bmangap,       
                             Outputs.forSpeeds.cumul_all.mean, delta_mean_Speeds,  Outputs.forSpeeds.cumul_all.firstQuart, delta_firstQuart_Speeds,  Outputs.forSpeeds.cumul_all.median, delta_median_Speeds,  Outputs.forSpeeds.cumul_all.thirdQuart, delta_thirdQuart_Speeds,  Outputs.forSpeeds.cumul_all.std, delta_std_Speeds]) 
                         
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