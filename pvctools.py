#!/usr/bin/env python
#  Laurent Gauthier, Ecole Polytechnique de Montreal, 2014
#  Python 2.7; (dt) Spyder Windows 7 64-bit; Vissim 6.0 64-bit
#  Dependencies listed in Libraries; 
Version = 'R1.0.1.2 u. 22-07-2014'
################################################################################
'''Dev stuff
import pdb; pdb.set_trace()
'''
################################################################################

#################### 
#        Main       
#################### 

def main():
    
    ################################ 
    #        Importing dependencies       
    ################################ 
    
    #Native dependencies
    import os, sys, time, optparse
    
    #Internal
    import lib.vissim as vissim
    import lib.tools_write as write 
    import lib.define as define
    import lib.tools_config as config
    import lib.analysis as analysis

    ################################ 
    #        Os verification       
    ################################        
    if os.name != 'nt':
        print '****************************************************************'        
        print '*           Vissim 6.0 and older requires Windows              *'
        print '*               ==== Closing program ===                       *'
        print '****************************************************************'
        sys.exit()
    
    ################################ 
    #        Load settings       
    ################################    
    commands = config.commands(optparse.OptionParser())
    config   = config.Config()
    
    #overrides default inpx file if command -f was used and Updating the default inpx name to match the file
    if commands.file:
        if not commands.file.endswith('inpx'):
            config.inpx_name = commands.file + str('.inpx')
        else:
            config.inpx_name = commands.file                

    ################################ 
    #        Car following model verification        
    ################################
    if commands.model not in ['74','99']:
        commands.model = '99'
        
        print '****************************************************************'
        print '*   The car-following model has to be one of the following:    *'
        print '*                                                              *'        
        print '*           -> Wiedemann 99 (-w 99 or nothing)                 *'
        print '*           -> Wiedemann 74 (-w 74)                            *'
        print '*                                                              *'
        print '*           Reverting to the default value (99)                *'        
        print '****************************************************************'
        
    ################################ 
    #        Module verifications       
    ################################
    '''as -s is on by default, this is presently useless. It will become usefull
       in the futur when -s is turned off by default '''
       
    if not (commands.sensitivity or commands.student or commands.calibration):
        print '****************************************************************'     
        print '*   No module was chosen, please use:                          *'
        print '*                                                              *'
        print '*        -c to start the Calibration Analysis,                 *'
        print '*        -d to start the Statistical precision Analysis,       *'
        print '*   or                                                         *'
        print '*        -s to start the Sensitivity Analysis                  *'
        print '*                                                              *'
        print '*                 ==== Closing program ===                     *'
        print '****************************************************************'
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

    #creating an output folder for that named inpx being studied
    if not os.path.isdir(os.path.join(MainInpxPath,"Analysis_on__" + InpxName.strip(".inpx"))):
        os.makedirs(os.path.join(MainInpxPath,"Analysis_on__" + InpxName.strip(".inpx"))) 
        
    WorkingPath = os.path.join(MainInpxPath,"Analysis_on__" + InpxName.strip(".inpx"))
    
    #Checking if Vissim is already running and closing it to avoid problems latter on
    running = vissim.isVissimRunning(firstTime = True)    
    if running is not False:
        print 'Could not close Vissim, the program may potentially have problems with the COM interface'
        
    ##Vissim simulation parameters
    Sim_lenght = config.simulation_time + config.warm_up_time
    parameters = [config.sim_steps, config.first_seed, config.nbr_runs, int(commands.model), Sim_lenght]
                    
    ###################################### 
    #        Statistical precision Analysis       
    ###################################### 
    if commands.student:
        TypeOfAnalysis = 'Statistical-precision'
        
        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)
           
        #creating the default values from memory
        Default_FM_values, FMvariables = define.createFMValues(int(commands.model) )
        Default_LC_values, LCvariables = define.createLCValues()        
        
        #creating default values
        default_values =  Default_FM_values  + Default_LC_values
        concat_variables = FMvariables + LCvariables

        #opening the output file and writing the appropriate header       
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, default_values)        
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
                
        text = analysis.statistical_ana(concat_variables, default_values, filename, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters)        

        #Adding a time marker and performance indicators
        report = write.timeStamp([1], 1, text[-1][0]) 
        report.pop(2)        
        for i in report: text.append(i)
        
        #filling the report
        for i in range(len(text)):
            write.writeInFile(out, text[i])  
        out.close()        
     
     
    ###################################### 
    #        Sensitivity Analysis       
    ######################################        
    if commands.sensitivity:
        TypeOfAnalysis = 'Sensitivity'
        
        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)                 
       
        #building the model values ranges
        if commands.verbose is True:
            print '-> Generating the range values and default values from memory'
            
        rangevalues = define.buildRanges(commands.model)

        #creating the default values from memory
        Default_FM_values, FMvariables = define.createFMValues(int(commands.model))
        Default_LC_values, LCvariables = define.createLCValues()
    
        #creating default values
    
        default_values =  Default_FM_values  + Default_LC_values
        concat_variables = FMvariables + LCvariables

        #verifying the ranges
        define.verifyRanges(rangevalues, concat_variables)

        #opening the output file and writing the appropriate header       
        if commands.verbose is True:
            print '-> Generating relevant subfolders for the analysis'

        out, subdirname = write.writeHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time)        

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
        if commands.multi is True:
            inputs = [concat_variables, default_values, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, False, firstrun_results]            
            unpacked_outputs = define.createWorkers(rangevalues, analysis.sensitivityAnalysis, inputs, commands, concat_variables)                  
            #unpacking the outputs -- the outputs here come back with 3 layers: nbr of chunk/runs in the chunk/text -- ie: text = unpacked_outputs[0][0]
            for i in unpacked_outputs:
                for j in i:
                    text.append(j)

        else:   
            inputs = [concat_variables, default_values, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, commands.verbose, firstrun_results]                             
            packed_outputs = analysis.sensitivityAnalysis(define.intelligentChunks(len(rangevalues), rangevalues, concat_variables), inputs)           
            #unpacking the outputs -- the outputs here come back with 2 layers: runs/text -- ie: text = packed_outputs[0]
         
            for i in packed_outputs:
                text.append(i)
                
        #Adding a time marker and performance indicators
        report = write.timeStamp(rangevalues, config.nbr_points, config.nbr_runs) 
        for i in report: text.append(i)
        
        #filling the report
        for i in range(len(text)):
            write.writeInFile(out, text[i])        
        out.close()

    ###################################### 
    #        Calibration Analysis       
    ######################################  
      
    
    if commands.calibration: 
        TypeOfAnalysis = 'Calibration'     
        
        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)
            
        #building the model values ranges - these serve as boundaries for the calculation universe        
        if commands.verbose is True:
            print '-> Generating the range values and default values from memory'
        rangevalues = define.buildRanges(commands.model)
    
        #creating the default values from memory
        Default_FM_values, FMvariables = define.createFMValues(int(commands.model))
        Default_LC_values, LCvariables = define.createLCValues()    
        
        #creating default values - Default values are the starting point of the algorythm
        default_values =  Default_FM_values  + Default_LC_values
        concat_variables = FMvariables + LCvariables

        #creating the universe boundaries        
        hard_bounds = define.hard_boundaries(commands.model)
        
        #verifying the ranges
        define.verifyRanges(rangevalues, concat_variables)
        
        #opening the output file and writing the appropriate header
        if commands.verbose is True:
            print '-> Generating relevant subfolders for the analysis'
            
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, default_values)
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
		
        ######### HERE MUST BE ADDED THE REAL VALUES FROM THE VIDEO
        ## probably a loadTrajectoryfromSQLITE function from traffic intelligence
        import lib.outputs as outputs
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
        video_values = [forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap]        
        
        nbr_iterations, total_points = analysis.simplex_search_81(out, config, commands, hard_bounds, default_values, concat_variables, video_values, outputspath, parameters, InpxName, InpxPath, running, filename)
        
        #Adding a time marker and performance indicators
        report = write.timeStamp(default_values, total_points, config.nbr_runs, nbr_iterations)        
        
        #filling the report
        for i in range(len(report)):
            write.writeInFile(out, report[i])  
        out.close()
    '''
    ##default values of computed parameters - obtained from video analysis
    #default_forFMgap = np.asarray([NUMBERS])
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

