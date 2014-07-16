# -*- coding: utf-8 -*-
"""
Created on Mon Jun 09 16:20:16 2014

@author: Laurent
"""

def main():
    
    ################################ 
    #        Importing dependencies       
    ################################ 
    
    #Native dependencies
    import os, shutil, sys, time, optparse
    import numpy as np
    import multiprocessing
    
    #from scipy.stats.mstats import kruskalwallis
    
    #import pdb; pdb.set_trace()
    #Internal
    import lib.vissim as vissim
    import lib.outputs as outputs
    import lib.tools_write as write 
    import lib.define as define
    import lib.tools_config as config
    import lib.analysis as analysis

    ################################ 
    #        Os verification       
    ################################        
    if os.name != 'nt':
        print '**************************************************************'        
        print 'Vissim 6.0 and older do not work with an other OS than Windows'
        print '            ==== Closing program ===                          '
        print '**************************************************************'
        sys.exit()
    
    ################################ 
    #        Load settings       
    ################################    
    commands = config.commands(optparse.OptionParser())
    config   = config.Config()
    
    ################################ 
    #        Module verifications       
    ################################
    '''as -s is on by default, this is presently useless. It will become usefull
       in the futur when -s is turned off by default '''
       
    if not (commands.sensitivity or commands.student or commands.calibration):
        print '**************************************************************'        
        print '     No module was chosen, please use -c, -d or -s'
        print '            ==== Closing program ===                          '
        print '**************************************************************'
        sys.exit()
        
    ############################################### 
    #        Definition of important variables       
    ###############################################
    #Clock start
    time.clock()
    
    #Definition of required paths for the project
    MainInpxPath = config.path_to_inpx
    InpxName = config.inpx_name
    InpxPath = os.path.join(MainInpxPath, InpxName)
    
    #Checking if Vissim is already running and closing it to avoid problems latter on
    running = vissim.isVissimRunning(firstTime = True)    
    if running is not False:
        print 'Could not close Vissim, the program may potentially have problems with the COM interface'
        
    ##Vissim simulation parameters
    Sim_lenght = config.simulation_time + config.warm_up_time
    parameters = [config.sim_steps, config.first_seed, config.nbr_runs, int(commands.model), Sim_lenght] 

    ###################################### 
    #        Student t-test       
    ###################################### 
    if commands.student:
        TypeOfAnalysis = 'Student'
        
        #creating the default values from memory
        Default_FM_values, FMvariables = define.createFMValues(int(commands.model), values = [])
        Default_LC_values, LCvariables = define.createLCValues(values = [])        
        
        #creating default values
        default_values =  Default_FM_values  + Default_LC_values
        concat_variables = FMvariables + LCvariables

        #opening the output file and writing the appropriate header       
        out, subdirname = write.writeHeader(MainInpxPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, default_values)        
        filename = subdirname.split(os.sep)[-1]        
        
        #generating the graphic and output folder
        graphspath = None        
        '''        
        if commands.vis_save:
            graphspath = write.createSubFolder(os.path.join(subdirname,"graphs"), "graphs")
            write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs"), "cumul_dist_graphs")
            write.createSubFolder(os.path.join(graphspath, "distribution_graphs"), "distribution_graphs")
            for i in range(len(default_values) +1):            
                if i == 0:
                    write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs", "Default_values"), "cumul_dist_graphs" + os.sep + "Default_values")
                    write.createSubFolder(os.path.join(graphspath, "distribution_graphs", "Default_values"), "cumul_dist_graphs" + os.sep + "Default_values")
                else:                    
                    write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs", concat_variables[i-1]), "cumul_dist_graphs" + os.sep + concat_variables[i-1])
                    write.createSubFolder(os.path.join(graphspath, "distribution_graphs", concat_variables[i-1]), "cumul_dist_graphs" + os.sep + concat_variables[i-1])
        '''
        outputspath = write.createSubFolder(os.path.join(subdirname,"outputs"), "outputs")
        
        analysis.studentTtest(concat_variables, default_values, filename, InpxPath, InpxName, outputspath, graphspath, out, config, commands, running, parameters)        
        
        out.close()        
     
     
    ###################################### 
    #        Sensitivity Analysis       
    ######################################        
    if commands.sensitivity:
        TypeOfAnalysis = 'Sensitivity'          

        #building the model values ranges        
        rangevalues = define.buildRanges(commands.model)        

        #creating the default values from memory
        Default_FM_values, FMvariables = define.createFMValues(int(commands.model))
        Default_LC_values, LCvariables = define.createLCValues()
    
        #creating default values
        default_values =  Default_FM_values  + Default_LC_values
        concat_variables = FMvariables + LCvariables

        #opening the output file and writing the appropriate header       
        out, subdirname = write.writeHeader(MainInpxPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time)        

        #creating appropriate output folder and graphic folder (if option is "on")        
        graphspath = None        
        if commands.vis_save:
            graphspath = write.createSubFolder(os.path.join(subdirname,"graphs"), "graphs")
            write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs"), "cumul_dist_graphs")
            write.createSubFolder(os.path.join(graphspath, "distribution_graphs"), "distribution_graphs")
            for i in range(len(rangevalues) +1):            
                if i == 0:
                    write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs", "Default_values"), "cumul_dist_graphs" + os.sep + "Default_values")
                    write.createSubFolder(os.path.join(graphspath, "distribution_graphs", "Default_values"), "cumul_dist_graphs" + os.sep + "Default_values")
                else:                    
                    write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs", concat_variables[i-1]), "cumul_dist_graphs" + os.sep + concat_variables[i-1])
                    write.createSubFolder(os.path.join(graphspath, "distribution_graphs", concat_variables[i-1]), "cumul_dist_graphs" + os.sep + concat_variables[i-1])
        outputspath = write.createSubFolder(os.path.join(subdirname,"outputs"), "outputs")        
        
        #treating the simulations        
        ##calculating the default values
        inputs = [concat_variables, default_values, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters]
        text, firstrun_results = analysis.sensitivityAnalysis(rangevalues, inputs, default = True)
        
        ##Running the rest of the simulations
        inputs = [concat_variables, default_values, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, firstrun_results]
        if commands.multi is True:
            #the outputs here comes back with 3 layers: nbr of chunk/runs in the chunk/text -- ie: text = packed_outputs[0][0]            
            packed_outputs = define.createWorkers(rangevalues, analysis.sensitivityAnalysis, inputs, concat_variables)       
            for i in packed_outputs:
                for j in i:
                    text.append(j)
        else:
            #the outputs here are passed as one chunks, so they comes back with 2 layers: runs in the chunk/text -- ie: text = packed_outputs[0]            
            unpacked_outputs = analysis.sensitivityAnalysis(rangevalues, inputs)           
            for i in unpacked_outputs:
                text.append(j)
        
        #filling the report
        for i in range(len(text)):
            out = write.writeInFile(out, text[i])        
        out.close()


    ###################################### 
    #        Calibration Analysis       
    ######################################  
      
    #if commands.calibration: 
      #TypeOfAnalysis = 'Calibration' 
      
    '''
    ##default values of computed parameters - obtained from video analysis
    # default_forFMgap = np.asarray([NUMBERS])
    #default_oppLCgap = np.asarray([NUMBERS])
    #default_manLCgap = np.asarray([NUMBERS])     
    #
    #To call the statistical function:
    #H-statistic, p-value = kruskalwallis(default_value, calculated_value)
    #if p<0.05 then first array is statistically different from second array
    #normally len(array) must be >= 5
    '''

###################
# Launch main
###################
if __name__ == "__main__":

    main()

