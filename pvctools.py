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
    import lib.sen as sen

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

    ############################ 
    #        Definition of important variables       
    ################### ########
    #Clock start
    time.clock()
    
    #Definition of required paths for the project
    MainInpxPath = config.path_to_inpx
    InpxName = config.inpx_name
    InpxPath = os.path.join(MainInpxPath, InpxName)
    
    ##Type of analysis (Sensitivity/Calibration)
    if commands.calibration:
        TypeOfAnalysis = 'Calibration'
    else:
        TypeOfAnalysis = 'Sensitivity'

    #Checking if Vissim is already running and closing it to avoid problems latter on
    running = vissim.isVissimRunning(firstTime = True)    
    if running is not False:
        print 'Could not close Vissim, the program may potentially have problems with the COM interface'
        
    ##Vissim simulation parameters
    Sim_lenght = config.simulation_time + config.warm_up_time
    parameters = [config.sim_steps, config.first_seed, config.nbr_runs, int(commands.model), Sim_lenght] 

    ################### 
    #        Student test       
    ################### 
    if TypeOfAnalysis == 'Student':
        
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
     
     
    ################### 
    #        Sensitivity Analysis       
    ###################        
    if TypeOfAnalysis == 'Sensitivity':          
        rangevalues = []
       
        ##Variables in Wiedemann 74   [min,max]
        if int(commands.model) == 74:        
            rangeW74ax        = [2.0, 4.0]                       #min = 0    
            rangeW74bxAdd  = [2.0, 4.0]
            rangeW74bxMult  = [3.0, 4.0]
            
            rangevalues.append(rangeW74ax,rangeW74bxAdd,rangeW74bxMult)
        
        ##Variables in Wiedemann 99   [min,max]
        elif int(commands.model) == 99: 
            rangeW99cc0 = [0.0    , 12.0] ; rangevalues.append(rangeW99cc0)   #min = 0
            rangeW99cc1 = [0.0    , 12.0] ; rangevalues.append(rangeW99cc1)
            rangeW99cc2 = [4.0    , 12.0] ; rangevalues.append(rangeW99cc2)   #min = 0
            rangeW99cc3 = [-8.0   , 12.0] ; rangevalues.append(rangeW99cc3)
            rangeW99cc4 = [-0.35  , 12.0] ; rangevalues.append(rangeW99cc4)
            rangeW99cc5 = [0.35   , 12.0] ; rangevalues.append(rangeW99cc5)
            rangeW99cc6 = [11.44  , 12.0] ; rangevalues.append(rangeW99cc6)
            rangeW99cc7 = [0.25   , 12.0] ; rangevalues.append(rangeW99cc7)
            rangeW99cc8 = [3.5    , 12.0] ; rangevalues.append(rangeW99cc8)
            rangeW99cc9 = [1.5    , 12.0] ; rangevalues.append(rangeW99cc9)
    
        ##Other variables for the following behavior model     
        rangeLookAheadDistMin = [0.0     , 12.0] ; rangevalues.append(rangeLookAheadDistMin)        #min = 0, max = 999999
        rangeLookAheadDistMax = [0.0     , 12.0] ; rangevalues.append(rangeLookAheadDistMax)        #min = 0, max = 999999
        rangeObsrvdVehs =       [2.0     , 12.0] ; rangevalues.append(rangeObsrvdVehs)              #min = 0, max = 10
        rangeLookBackDistMin =  [0.0     , 12.0] ; rangevalues.append(rangeLookBackDistMin)         #min = 0, max = 999999
        rangeLookBackDistMax =  [0.0     , 12.0] ; rangevalues.append(rangeLookBackDistMax)         #min = 0, max = 999999            
                             
        ##Variables for lane change behavior
        rangeMaxDecelOwn =         [-4.0  , -1.0 ] ; rangevalues.append(rangeMaxDecelOwn)           #min = -10, max = -0.01
        rangeDecelRedDistOwn =     [0.0   , 12.0 ] ; rangevalues.append(rangeDecelRedDistOwn)       #min = 0
        rangeAccDecelOwn =         [-10.0 , -1.0 ] ; rangevalues.append(rangeAccDecelOwn)           #min = -10, max = -1
        rangeMaxDecelTrail =       [-10.  , -1.0 ] ; rangevalues.append(rangeMaxDecelTrail)         #min = -10, max = -0.01
        rangeDecelRedDistTrail =   [0.0   , 12.0 ] ; rangevalues.append(rangeDecelRedDistTrail)     #min = 0
        rangeAccDecelTrail =       [-10.0 , -1.0 ] ; rangevalues.append(rangeAccDecelTrail)         #min = -10, max = -1
        rangeDiffusTm =            [0     , 100.0] ; rangevalues.append(rangeDiffusTm)
        rangeMinHdwy =             [0.5   , 12.0 ] ; rangevalues.append(rangeMinHdwy)
        rangeSafDistFactLnChg =    [0.6   , 12.0 ] ; rangevalues.append(rangeSafDistFactLnChg)
        rangeCoopLnChg =           [True  , False] ; rangevalues.append(rangeCoopLnChg)
        rangeCoopLnChgSpeedDiff =  [3.0   , 12.0 ] ; rangevalues.append(rangeCoopLnChgSpeedDiff) 
        rangeCoopLnChgCollTm =     [10.0  , 12.0 ] ; rangevalues.append(rangeCoopLnChgCollTm)
        rangeCoopDecel =           [-10.0 , 0.0  ] ; rangevalues.append(rangeCoopDecel)             #min = -10, max = 0
  
        #creating the default values from memory
        Default_FM_values, FMvariables = define.createFMValues(int(commands.model), values = [])
        Default_LC_values, LCvariables = define.createLCValues(values = [])
    
        #creating default values
        default_values =  Default_FM_values  + Default_LC_values
        concat_variables = FMvariables + LCvariables

        #opening the output file and writing the appropriate header       
        out, subdirname = write.writeHeader(MainInpxPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time)        
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
        
        #simulationChunks = define.toChunks(n,rangevalues)        
        
        #treating the simulations
        firstrun = True
        out = sen.sensitivityAnalysis(rangevalues, concat_variables, default_values, firstrun, InpxPath, InpxName, outputspath, graphspath, out, config, commands, running, parameters)
        
        out.close()
    return True

    ################### 
    #        Calibration Analysis       
    ###################  
      
    #if TypeOfAnalysis == 'Calibration': 
      
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

