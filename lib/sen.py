# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 14:43:44 2014

@author: Laurent
"""

################################ 
#        Importing dependencies       
################################ 
#Natives
import os, shutil, time, sys
import numpy as np
from scipy.stats import t

#Internal
import lib.tools_write as write
import lib.vissim as vissim
import lib.outputs as outputs

################################ 
#        Student test       
################################

def studentTtest(rangevalues, concat_variables, default_values, filename, InpxPath, InpxName, outputspath, graphspath, out, config, commands, running, parameters):
    '''Finds the number of iterations needed to achieve a good confidence interval
    
    Base on the ODOT specifications:
        1. run 10 simulations and calculates the median and standard deviation for the outputs
        2. run the Student t-test while fixing the confidence interval to +/- S  --> N = [t(1-alpha/2;N-1)*S]^2 with aplha = 0.975 (bivariate 95% confidence)
        3. 
    '''
   
    #Sim_lenght = config.simulation_time + config.warm_up_time
    #parameters = [config.sim_steps, config.first_seed, config.nbr_runs, int(commands.model), Sim_lenght] 
   
    #set the number of runs to 10
    first_seed = parameters[1]    
    parameters[2] = 10
    iterrations_ran = 10
    
    #renaming the inpx and moving it to the output folder
    if os.path.exists(os.path.join(outputspath, filename)) is False:
        shutil.copy(InpxPath, os.path.join(outputspath, InpxName))
        os.rename(os.path.join(outputspath, InpxName), os.path.join(outputspath, filename))
   
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
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs(outputspath, config.sim_steps, config.warm_up_time)
        print '*** Output treatment completed *** Runtime: ' + str(time.clock())
       
    #generating the needed means and std
    N1 = ( t.ppf(0.975,10) * forFMgap.cumul_all.std )**2
    N2 = ( t.ppf(0.975,10) * oppLCagap.cumul_all.std )**2
    N3 = ( t.ppf(0.975,10) * oppLCbgap.cumul_all.std )**2
    N4 = ( t.ppf(0.975,10) * manLCagap.cumul_all.std )**2
    N5 = ( t.ppf(0.975,10) * manLCbgap.cumul_all.std )**2
    
    N =  min(N1, N2, N3, N4, N5)
    
    '''
    MUST CALCULATE SCI1-SCI5
    '''
    
    out.write("Nbr_itt;N1;N2;N3;N4;N5;N;SCI1;SCI2;SCI3;SCI4;SCI5")
    out.write(iterrations_ran+";"+N1+";"+N2+";"+N3+";"+N4+";"+N5+";"+N+"\n")    
    
    while N > iterrations_ran:
        
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
        N1 = ( t.ppf(0.975,10) * forFMgap.cumul_all.std )**2
        N2 = ( t.ppf(0.975,10) * forFMgap.cumul_allstd )**2
        N3 = ( t.ppf(0.975,10) * oppLCbgap.cumul_all.std )**2
        N4 = ( t.ppf(0.975,10) * manLCagap.cumul_all.std )**2
        N5 = ( t.ppf(0.975,10) * manLCbgap.cumul_all.std )**2
        
        N =  min(N1, N2, N3, N4, N5)        
        
        '''
        MUST CALCULATE SCI1-SCI5
        '''
        
        out.write(iterrations_ran+";"+N1+";"+N2+";"+N3+";"+N4+";"+N5+";"+N+"\n")        
        
    return True        
        

################################ 
#        Sensitivity Analisis       
################################

def sensitivityAnalysis(rangevalues, concat_variables, default_values, firstrun, InpxPath, InpxName, outputspath, graphspath, out, config, commands, running, parameters):
    '''Runs the sensitivity analisys for a set of predetermined values'''    
    
    for value in range(len(rangevalues)):
        firstrun_collateral = False
        Number_of_points =  config.nbr_points           
        value_name =  concat_variables[value]            
        values = default_values[:]
        print' ================================= '
        print 'Starting work on variable ' + value_name + ' ( ' + str(value + 1) + '/' + str(len(rangevalues)) + ' )'
        print' ================================= '
        
        if firstrun is True:
            Number_of_points += 1
            firstrun_collateral = True
        elif value_name == "CoopLnChg":
            Number_of_points = 2
        for point in range(Number_of_points):            
            #all the code parts with "if firstrun == True" only serves to add a single point to compute the result with all default values
            if firstrun is True:
                current = values[value]
            elif firstrun_collateral is True:
                current =  rangevalues[value][0] + (point - 1) * (rangevalues[value][1] - rangevalues[value][0]) /  (Number_of_points -2)               
            elif value_name == "CoopLnChg":
                current = rangevalues[value][point]
            else:    
                current =  rangevalues[value][0] + point * (rangevalues[value][1] - rangevalues[value][0]) /  (Number_of_points -1)
                if value_name == "CoopLnChgSpeedDiff":
                    values[value -1] = True
                elif value_name == "CoopLnChgCollTm":
                    values[value -2] = True
                elif value_name == "LookAheadDistMin":
                    if values[value +1] < current:
                        values[value +1] = current
                        print 'LookBackDistMax was set to a value lower than the value set to LookAheadDistMin. To avoid a crash of Vissim, both values were set to the same value'
                elif value_name == "LookAheadDistMax":
                    if values[value -1] > current:
                        values[value -1] = current
                        print 'LookBackDistMin was set to a value higher than the value set to LookAheadDistMax. To avoid a crash of Vissim, both values were set to the same value'
                elif value_name == "LookBackDistMin":
                    if values[value +1] < current:
                        values[value +1] = current
                        print 'LookBackDistMax was set to a value lower than the value set to LookBackDistMin. To avoid a crash of Vissim, both values were set to the same value'
                elif value_name == "LookAheadDistMin":
                    if values[value -1] > current:
                        values[value -1] = current
                        print 'LookBackDistMin was set to a value higher than the value set to LookBackDistMax. To avoid a crash of Vissim, both values were set to the same value'
                                            
            values[value] = current          
            
            #creating a folder containing the files for that iteration
            if firstrun is True:
                filename = 'Default_values.inpx'
                folder = 'Default_values'
            else:
                filename = value_name + '_' + str(round(current,3)) + '.inpx'
                folder = value_name + '_' + str(round(current, 3))
    
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
                simulated = vissim.initializeSimulation(Vissim, parameters, values, concat_variables, commands.save_swp)
                print '*** Simulation completed *** Runtime: ' + str(time.clock())                    
                
                if simulated is False:
                    print 'could not simulate ' + filename
                
                vissim.stopVissim(Vissim) #unsure if i should stop and start vissim every iteration... to be tested.
                
                #output treatment
                flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs(folderpath, config.sim_steps, config.warm_up_time)
                print '*** Output treatment completed *** Runtime: ' + str(time.clock())
            
            if firstrun is True:
                firstrun_mean_fgap = float(forFMgap.cumul_all.mean)
                firstrun_mean_Aoppgap = float(oppLCagap.cumul_all.mean)
                firstrun_mean_Boppgap = float(oppLCbgap.cumul_all.mean)
                firstrun_mean_Amangap = float(manLCagap.cumul_all.mean)
                firstrun_mean_Bmangap = float(manLCbgap.cumul_all.mean)
                firstrun_oppLCcount = float(oppLCcount)
                firstrun_manLCcount = float(manLCcount)
            
            delta_mean_fgap = (forFMgap.cumul_all.mean - firstrun_mean_fgap)/firstrun_mean_fgap
            delta_mean_Aoppgap = (oppLCagap.cumul_all.mean - firstrun_mean_Aoppgap)/firstrun_mean_Aoppgap
            delta_mean_Boppgap = (oppLCbgap.cumul_all.mean - firstrun_mean_Boppgap)/firstrun_mean_Boppgap
            delta_mean_Amangap = (manLCagap.cumul_all.mean - firstrun_mean_Amangap)/firstrun_mean_Amangap
            delta_mean_Bmangap = (manLCbgap.cumul_all.mean - firstrun_mean_Bmangap)/firstrun_mean_Bmangap
            delta_oppLCcount = (oppLCcount - firstrun_oppLCcount)/firstrun_oppLCcount
            delta_manLCcount = (manLCcount - firstrun_manLCcount)/firstrun_manLCcount
            
            #printing graphs
            if commands.vis_save:
                variables = [forFMgap,oppLCagap,oppLCbgap,manLCagap,manLCbgap]
                variables_name =["Forward_gaps","Opportunistic_lane_change_'after'_gaps","Opportunistic_lane_change_'before'_gaps","Mandatory_lane_change_'after'_gaps","Mandatory_lane_change_'before'_gaps"]
                for var in range(len(variables)):
                    if firstrun is True:
                        name = "Default_values"
                        subpath = "Default_values"
                    else:
                        name = folder[:]
                        subpath = value_name[:]
                    
                    write.printStatGraphs(graphspath,variables[var], name, variables_name[var], commands.fig_format, subpath)
                
            #writing to file
            if firstrun is True:
                out = write.writeInFile(out, "Default_values", values, flow, oppLCcount, "---", manLCcount, "---", forFMgap.cumul_all.mean, "---", oppLCagap.cumul_all.mean, "---", oppLCbgap.cumul_all.mean, "---", manLCagap.cumul_all.mean, "---", manLCbgap.cumul_all.mean,  "---")
                firstrun = False
            else:
                out = write.writeInFile(out, value_name, values, flow, oppLCcount, delta_oppLCcount, manLCcount, delta_manLCcount, forFMgap.cumul_all.mean, delta_mean_fgap, oppLCagap.cumul_all.mean, delta_mean_Aoppgap, oppLCbgap.cumul_all.mean, delta_mean_Boppgap, manLCagap.cumul_all.mean, delta_mean_Amangap, manLCbgap.cumul_all.mean, delta_mean_Bmangap)       

    return out