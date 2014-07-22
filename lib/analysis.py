# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 14:43:44 2014

@author: Laurent
"""

################################ 
#        Importing dependencies       
################################ 
#Natives
import os, shutil, time, sys, copy
import numpy as np
from scipy.stats import t, chi2

#Internal
import lib.tools_write as write
import lib.vissim as vissim
import lib.outputs as outputs

################################ 
#        Statistical precision analysis       
################################

def statistical_ana(concat_variables, default_values, filename, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters):
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
    text = []
   
    #set the number of runs to 10
    first_seed = parameters[1]    
    parameters[2] = 10
    iterrations_ran = 10
    
    #renaming the inpx and moving it to the output folder
    if os.path.exists(os.path.join(outputspath, "Statistical_test.inpx")) is False:
        shutil.copy(InpxPath, os.path.join(outputspath, InpxName))
        os.rename(os.path.join(outputspath, InpxName), os.path.join(outputspath, "Statistical_test.inpx"))
    
    print 'Starting the first 10 runs'
    
    if commands.mode:  #this serves to bypass Vissim while testing the code
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
    else:
        Vissim = vissim.startVissim(running, os.path.join(outputspath,  "Statistical_test.inpx"))
                            
        #Vissim initialisation and simulation running                                                   
        simulated = vissim.initializeSimulation(Vissim, parameters, default_values, concat_variables, commands.save_swp)
        print '*** Simulation completed *** Runtime: ' + str(time.clock())                    
        
        if simulated is False:
            print 'could not simulate ' + filename
        
        vissim.stopVissim(Vissim) #unsure if i should stop and start vissim every iteration... to be tested.
        
        #output treatment
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs(outputspath, config.sim_steps, config.warm_up_time)
        print '*** Output treatment completed *** Runtime: ' + str(time.clock())
       
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

    '''
    MUST ADD GRAPH OPTION
    '''
    
    while N > iterrations_ran and iterrations_ran < 100:
        
        print 'Starting the ' + str(iterrations_ran + 1) + "th iteration"        
        
        old_data = [forFMgap.cumul_all.raw, forFMgap.cumul_all.raw, oppLCbgap.cumul_all.raw, manLCagap.cumul_all.raw, manLCbgap.cumul_all.raw]        
        
        #incrementing the number of iteration do by 1                
        parameters[1] = first_seed + iterrations_ran
        parameters[2] = 1
        iterrations_ran += 1
        
        #calling vissim
        if commands.mode:  #this serves to bypass Vissim while testing the code
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
        else:
            Vissim = vissim.startVissim(running, os.path.join(outputspath, filename))
                                
            #Vissim initialisation and simulation running
            simulated = vissim.initializeSimulation(Vissim, parameters, default_values, concat_variables, commands.save_swp)
            print '*** Simulation completed *** Runtime: ' + str(time.clock())                    
            
            if simulated is False:
                print 'could not simulate ' + filename
            
            vissim.stopVissim(Vissim) #unsure if i should stop and start vissim every iteration... to be tested.
            
            #output treatment
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs(outputspath, config.sim_steps, config.warm_up_time, old_data, first_file = iterrations_ran)
            print '*** Output treatment completed *** Runtime: ' + str(time.clock())        
        
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
        
        '''
        MUST ADD GRAPH OPTION
        '''
        
    print "Statistical precision achieved - generating report"
    
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
        position = 0
    else:
        position = current_range[1]
        if current_name == "CoopLnChg":
            points_array = current_range[0]
        else:
            points_array = []
            if nbr_points > 1:
                for point in range(nbr_points):
                    points_array.append(current_range[0][0] + point * (current_range[0][1] - current_range[0][0]) /  (nbr_points - 1) )
            else:
                points_array.append((current_range[0][0] + current_range[0][1]) / 2)
            
    return working_values, points_array, position
        
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
        if working_values[var_dict["LookBackDistMax"][1]] < current_value:
            working_values[var_dict["LookBackDistMax"][1]] = current_value + 0.1
            message.append('LookBackDistMax was set to a value lower than the value set to LookAheadDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookAheadDistMax":
        if working_values[var_dict["LookBackDistMin"][1]] > current_value:
            working_values[var_dict["LookBackDistMin"][1]] = current_value - 0.1
            message.append('LookBackDistMin was set to a value higher than the value set to LookAheadDistMax. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookBackDistMin":
        if working_values[var_dict["LookBackDistMax"][1]] < current_value:
            working_values[var_dict["LookBackDistMax"][1]] = current_value + 0.1
            message.append('LookBackDistMax was set to a value lower than the value set to LookBackDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookAheadDistMax":
        if working_values[var_dict["LookBackDistMin"][1]] > current_value:
            working_values[var_dict["LookBackDistMin"][1]] = current_value - 0.1
            message.append('LookBackDistMin was set to a value higher than the value set to LookBackDistMax. To avoid a crash of Vissim, the value was adjusted')
        
    return working_values, message
        
def sensitivityAnalysis(rangevalues, inputs, default = False):
    '''Runs the sensitivity analysis for a set of predetermined values
    
       note: rangevalues = [range, position in the complete list]
    '''    

    #unpacking inputs - should eventually be changed directly in the code
    concat_variables    = inputs [0]
    default_values      = inputs [1]
    InpxPath            = inputs [2]
    InpxName            = inputs [3]
    outputspath         = inputs [4]
    graphspath          = inputs [5]
    config              = inputs [6]
    commands            = inputs [7]
    running             = inputs [8]
    parameters          = inputs [9]
    if default is False:
        firstrun_results = inputs[10]      
    
    #preparing the outputs    
    text = []
    
    #creating a dictionnary
    var_dict = varDict(concat_variables, default_values)    

    #treating the values given in rangevalues    
    for value in range(len(rangevalues)):        
        #defining the variable being worked on and the range of values it can take
        if default is True:
            current_range = []
            value_name = "Default"
        else:
            current_range = rangevalues[value]   
            value_name = concat_variables[rangevalues[value][1]]
        
        #defining the values needed for the current cycle
        working_values, points_array, position = setCalculatingValues(default_values, value_name, config.nbr_points, current_range, default)

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
            if default is True:
                filename = 'Default_values.inpx'
                folder = 'Default_values'
            else:
                filename = value_name + '_' + str(round(point,3)) + '.inpx'
                folder = value_name + '_' + str(round(point, 3))
    
            folderpath = os.path.join(outputspath, folder)
            newfolderpath = write.createSubFolder(folderpath, folder)
            
            if newfolderpath is False:
                sys.exit()
                print 'newfolderpath = Newfolderpath = False, must find a way to handle this issue'   
            
            #renaming the inpx and moving it to the new folder
            if os.path.exists(os.path.join(folderpath, filename)) is False:
                shutil.copy(InpxPath, os.path.join(folderpath, InpxName))
                os.rename(os.path.join(folderpath, InpxName), os.path.join(folderpath, filename))
    
            #Starting a Vissim instance
            if commands.mode:  #this serves to bypass Vissim while testing the code
                flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
            else:
                Vissim = vissim.startVissim(running, os.path.join(folderpath, filename))
                                    
                #Vissim initialisation and simulation running
                simulated = vissim.initializeSimulation(Vissim, parameters, corrected_values, concat_variables, commands.save_swp)
                #print '*** Simulation completed *** Runtime: ' + str(time.clock())                    
                
                if simulated is False:
                    print 'could not simulate ' + filename
                
                vissim.stopVissim(Vissim) #unsure if i should stop and start vissim every iteration... to be tested.
                
                #output treatment
                flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs(folderpath, config.sim_steps, config.warm_up_time)
                #print '*** Output treatment completed *** Runtime: ' + str(time.clock())
            
            if default is True:
                firstrun_results = []
                firstrun_results.append(float(forFMgap.cumul_all.mean))
                firstrun_results.append(float(oppLCagap.cumul_all.mean))
                firstrun_results.append(float(oppLCbgap.cumul_all.mean))
                firstrun_results.append(float(manLCagap.cumul_all.mean))
                firstrun_results.append(float(manLCbgap.cumul_all.mean))
                firstrun_results.append(float(oppLCcount))
                firstrun_results.append(float(manLCcount))

                
            else:           
                delta_mean_fgap = (forFMgap.cumul_all.mean - firstrun_results[0])/firstrun_results[0]
                delta_mean_Aoppgap = (oppLCagap.cumul_all.mean - firstrun_results[1])/firstrun_results[1]
                delta_mean_Boppgap = (oppLCbgap.cumul_all.mean - firstrun_results[2])/firstrun_results[2]
                delta_mean_Amangap = (manLCagap.cumul_all.mean - firstrun_results[3])/firstrun_results[3]
                delta_mean_Bmangap = (manLCbgap.cumul_all.mean - firstrun_results[4])/firstrun_results[4]
                delta_oppLCcount = (oppLCcount - firstrun_results[5])/firstrun_results[5]
                delta_manLCcount = (manLCcount - firstrun_results[6])/firstrun_results[6]
            
            #printing graphs
            if commands.vis_save:
                variables = [forFMgap,oppLCagap,oppLCbgap,manLCagap,manLCbgap]
                variables_name =["Forward_gaps","Opportunistic_lane_change_'after'_gaps","Opportunistic_lane_change_'before'_gaps","Mandatory_lane_change_'after'_gaps","Mandatory_lane_change_'before'_gaps"]
                for var in range(len(variables)):
                    if default is True:
                        name = "Default_values"
                        subpath = "Default_values"
                    else:
                        name = folder[:]
                        subpath = value_name[:]
                    
                    write.printStatGraphs(graphspath,variables[var], name, variables_name[var], commands.fig_format, config.nbr_runs, subpath)
                
            #writing to file
            if default is True:
                text.append(["Default_values", corrected_values, flow, oppLCcount, "---", manLCcount, "---", forFMgap.cumul_all.mean, "---", oppLCagap.cumul_all.mean, "---", oppLCbgap.cumul_all.mean, "---", manLCagap.cumul_all.mean, "---", manLCbgap.cumul_all.mean,  "---"])
            else:
                text.append([value_name, corrected_values, flow, oppLCcount, delta_oppLCcount, manLCcount, delta_manLCcount, forFMgap.cumul_all.mean, delta_mean_fgap, oppLCagap.cumul_all.mean, delta_mean_Aoppgap, oppLCbgap.cumul_all.mean, delta_mean_Boppgap, manLCagap.cumul_all.mean, delta_mean_Amangap, manLCbgap.cumul_all.mean, delta_mean_Bmangap])       
        
        #breaking the outer loop because the default only needs to be ran once
        if default is True:
            break
    
    if default is True:    
        return text, firstrun_results
    else:
        return text