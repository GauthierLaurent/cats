#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Laurent Gauthier, Ecole Polytechnique de Montreal, 2014
#  Python 2.7; (dt) Spyder Windows 7 64-bit; Vissim 6.0 64-bit
#  Dependencies listed in Libraries; 
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
    import os, sys, time, optparse, random
    
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
    config   = config.Config('pvc.cfg')
    
    #overrides default inpx file if command -f was used and Updating the default inpx name to match the file
    if commands.file:
        if not commands.file.endswith('inpx'):
            config.inpx_name = commands.file + str('.inpx')
        else:
            config.inpx_name = commands.file                

    ################################ 
    #        Car following model verification        
    ################################
    if config.wiedemann not in [74,99]:
        config.wiedemann = 99
        
        print '****************************************************************'
        print '*   The car-following model has to be one of the following:    *'
        print '*                                                              *'        
        print '*           -> Wiedemann 99 (99 or nothing)                    *'
        print '*           -> Wiedemann 74 (74)                               *'
        print '*                                                              *'
        print '*           Reverting to the default value (99)                *'        
        print '****************************************************************'
        
    ################################ 
    #        Module verifications       
    ################################
    '''as -s is on by default, this is presently useless. It will become usefull
       in the futur when -s is turned off by default '''
       
    if not (commands.sensitivity or commands.student or commands.calibration or commands.montecarlo):
        print '****************************************************************'     
        print '*   No module was chosen, please use:                          *'
        print '*                                                              *'
        print '*        -d to start the Statistical precision Analysis,       *'
        print '*        -o to start the Sensitivity Monte Carlo Analysis,     *'        
        print '*   or                                                         *'
        print '*        -s to start the Sensitivity One-at-a-time Analysis    *'
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
    running = vissim.isVissimRunning(True)    
    if running is not False:
        print 'Could not close Vissim, the program may potentially have problems with the COM interface'
        
    ##Vissim simulation parameters
    Sim_lenght = config.simulation_time + config.warm_up_time
    sim_cores = 1
    parameters = [config.sim_steps, config.first_seed, config.nbr_runs, int(config.wiedemann), Sim_lenght, sim_cores]
    VissimCorridors, trafIntCorridors = define.extractVissimCorridorsFromCSV(InpxPath, InpxName)
                
    ###################################### 
    #        Statistical precision Analysis       
    ###################################### 
    if commands.student:
        TypeOfAnalysis = 'Statistical-precision'
        
        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)
           
        #generating the raw variables contained in the csv
        variables = define.extractParamFromCSV(InpxPath,InpxName)
        
        #removing unwanted variables for this weidemann model
        variables = vissim.weidemannCheck(config.wiedemann, variables)
    
        #creating default values    
        default_values =  [variables[i].vissim_default for i in xrange(len(variables))]
        concat_variables = [variables[i].vissim_name for i in xrange(len(variables))]

        #opening the output file and writing the appropriate header       
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName, default_values)        
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
                
        text = analysis.statistical_ana(concat_variables, default_values, filename, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, VissimCorridors)        

        #Adding a time marker and performance indicators
        report = write.timeStamp([1], 1, text[-1][0]) 
        report.pop(2)        
        for i in report: text.append(i)
        
        #filling the report
        for i in range(len(text)):
            write.writeInFile(out, text[i])  
        out.close()        
     
     
    ###################################### 
    #        One at a time Sensitivity Analysis       
    ######################################        
    if commands.sensitivity:
        TypeOfAnalysis = 'Sensitivity'
        
        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)                 
       
        #building the model values ranges
        if commands.verbose is True:
            print '-> Generating the range values and default values from memory'
        
        #generating the raw variables contained in the csv
        variables = define.extractParamFromCSV(InpxPath,InpxName)
        
        #removing unwanted variables for this weidemann model
        variables = vissim.weidemannCheck(config.wiedemann, variables)
    
        #creating default values    
        default_values =  [variables[i].vissim_default for i in xrange(len(variables))]
        concat_variables = [variables[i].vissim_name for i in xrange(len(variables))]

        #opening the output file and writing the appropriate header       
        if commands.verbose is True:
            print '-> Generating relevant subfolders for the analysis\n'

        out, subdirname = write.writeHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName)        

        #creating appropriate output folder and graphic folder (if option is "on")
        graphspath = None        
        if commands.vis_save:
            graphspath = write.createSubFolder(os.path.join(subdirname,"graphs"), "graphs")
            write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs"), "cumul_dist_graphs")
            write.createSubFolder(os.path.join(graphspath, "distribution_graphs"), "distribution_graphs")
            for i in range(len(variables) +1):            
                if i == 0:
                    write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs", "Default_values"), "cumul_dist_graphs" + os.sep + "Default_values")
                    write.createSubFolder(os.path.join(graphspath, "distribution_graphs", "Default_values"), "cumul_dist_graphs" + os.sep + "Default_values")
                else:                    
                    write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs", variables[i-1].name), "cumul_dist_graphs" + os.sep + variables[i-1].name)
                    write.createSubFolder(os.path.join(graphspath, "distribution_graphs", variables[i-1].name), "cumul_dist_graphs" + os.sep + variables[i-1].name)
        outputspath = write.createSubFolder(os.path.join(subdirname,"outputs"), "outputs")        
        
        #treating the simulations        
        ##calculating the default values
        inputs = [variables, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, commands.verbose, VissimCorridors]
        text, firstrun_results = analysis.sensitivityAnalysis(define.intelligentChunks(len(variables), variables, concat_variables), inputs, default = True)
        
        ##Running the rest of the simulations
        if commands.multi is True:
            #TODO: transform analysis.sensitivityAnalysis to accomodate for more than 4 process
            '''for minChunkSize: there is a max number of 4 vissim instances that can be ran at the same time...
               the min 4 is to make sure not more than 4 instances are processed at the same time.
               A way to deal with this would be to generate the simulations, than have a crawler reach through the
               folders to deal with the outputs - possibly while the next simulations are being processed'''
            minChunkSize = min(4,define.countPoints(concat_variables, config.nbr_points, config.nbr_runs))
            inputs = [variables, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, False, VissimCorridors, firstrun_results]            
            unpacked_outputs = define.createWorkers(variables, analysis.sensitivityAnalysis, inputs, commands, minChunkSize, concat_variables)                  
            #unpacking the outputs -- the outputs here come back with 3 layers: nbr of chunk/runs in the chunk/text -- ie: text = unpacked_outputs[0][0]
            for i in unpacked_outputs:
                for j in i:
                    text.append(j)

        else:   
            inputs = [variables, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, commands.verbose, VissimCorridors, firstrun_results]                             
            packed_outputs = analysis.sensitivityAnalysis(define.intelligentChunks(len(variables), variables, concat_variables), inputs)           
            #unpacking the outputs -- the outputs here come back with 2 layers: runs/text -- ie: text = packed_outputs[0]
         
            for i in packed_outputs:
                text.append(i)
                
        #Adding a time marker and performance indicators
        report = write.timeStamp(variables, config.nbr_points, config.nbr_runs) 
        for i in report: text.append(i)
        
        #filling the report
        for i in range(len(text)):
            write.writeInFile(out, text[i])        
        out.close()

    ###################################### 
    #        Monte Carlo Sensitivity Analysis       
    ######################################        
    if commands.montecarlo:
        TypeOfAnalysis = 'Monte Carlo'
        
        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)                 
        
        
        #building the model values ranges
        if commands.verbose is True:
            print '-> Generating the range values and default values from memory'
            
        #generating the raw variables contained in the csv
        variables = define.extractParamFromCSV(InpxPath,InpxName)
        
        #removing unwanted variables for this weidemann model
        variables = vissim.weidemannCheck(config.wiedemann, variables)
    
        #creating default values    
        default_values =  [variables[i].vissim_default for i in xrange(len(variables))]
        concat_variables = [variables[i].vissim_name for i in xrange(len(variables))]

        #opening the output file and writing the appropriate header       
        if commands.verbose is True:
            print '-> Generating relevant subfolders for the analysis\n'

        out, subdirname = write.writeHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName)        

        #creating appropriate output folder and graphic folder (if option is "on")
        outputspath = write.createSubFolder(os.path.join(subdirname,"outputs"), "outputs")        

        #creating 1000 random values
        valuesVector = []
        for i in xrange(0,10):
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
            
        #treating the simulations
        if commands.verbose:
            print '\n=== Starting the modelisations of the ' + str(len(valuesVector)) + ' points ==='
            
        for i in range(1):
            values = valuesVector[len(valuesVector)/1*i:len(valuesVector)/1*i+10]
            lowerbound = len(valuesVector)/1*i
            
            if commands.multi is True:
                cores_per_process, number_of_process, unused_cores = define.cpuPerVissimInstance()
                minChunkSize = number_of_process
                parameters[5] = cores_per_process
                out_valuesVector = []
                inputs = [variables, InpxPath, InpxName, outputspath, commands, running, parameters, lowerbound, valuesVector]            
                unpacked_outputs = define.createWorkers(values, analysis.monteCarlo_vissim, inputs, commands, minChunkSize)                  
                #unpacking the outputs -- the outputs here come back with 3 layers: nbr of chunk/runs in the chunk/text -- ie: text = unpacked_outputs[0][0]
                for k in unpacked_outputs:
                    out_valuesVector += k
                        
            else:   
                inputs = [variables, InpxPath, InpxName, outputspath, commands, running, parameters, lowerbound]                             
                out_valuesVector = analysis.monteCarlo_vissim(values, inputs)           
        #import pdb;pdb.set_trace()        
        #treating the outputs
        if commands.verbose:
            print '\n=== Starting the treatments of the ' + str(len(valuesVector)) + ' points simulated ==='
            
        text = []
        ##note: data is now passed as [[list of values], path_to_folder]
        for i in range(1):
            values = out_valuesVector[len(out_valuesVector)/1*i:len(out_valuesVector)/1*i+10]
            if commands.multi is True:
                minChunkSize = define.monteCarloCountPoints(len(values), config.nbr_runs)
                inputs = [variables, parameters, outputspath, config, commands, VissimCorridors, InpxName]            
                unpacked_outputs = define.createWorkers(values, analysis.monteCarlo_outputs, inputs, commands, minChunkSize)
                
                for k in unpacked_outputs:
                    for j in k:
                        text.append(j)

            else:
                inputs = [variables, parameters, outputspath, config, commands, VissimCorridors, InpxName]                             
                packed_outputs = analysis.monteCarlo_outputs(values, inputs)
                
                for k in packed_outputs:
                    text.append(k)    

        #Adding a time marker and performance indicators
        report = write.timeStamp(valuesVector, config.nbr_points, config.nbr_runs) 
        for i in report: text.append(i)

        #filling the report
        for i in range(len(text)):
            write.writeInFile(out, text[i]) 

        out.close()

###################
# Launch main
###################
if __name__ == "__main__": 

    main()
