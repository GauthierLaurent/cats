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

def main():
    ################################ 
    #        Importing dependencies       
    ################################ 
    
    #Native dependencies
    import os, sys, shutil, optparse, subprocess
    
    #Internal
    import pvc_write  as write
    import pvc_vissim as vissim
    import pvc_define as define
    import pvc_config as config
    
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
    config   = config.Config('calib.cfg')      
            
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
                 
    ###################################### 
    #        Preparing  environnement       
    ######################################     
    #Checking if Vissim is already running and closing it to avoid problems latter on
    running = vissim.isVissimRunning(True)    
    if running is not False:
        print 'Could not close Vissim, the program may potentially have problems with the COM interface'
        
    ##Vissim simulation parameters
    Sim_lenght = config.simulation_time + config.warm_up_time
    sim_cores = 1
    parameters = [config.sim_steps, config.first_seed, config.nbr_runs, int(config.wiedemann), Sim_lenght, sim_cores]
    
    #determining vissim, video, and corridor lists
    networks = define.buildNetworkObjects(config)      
        
    #generating the raw variables contained in the csv
    variables = define.extractParamFromCSV(config.path_to_calib_csv, 'calib.csv')
    
    #TODO: allow different wiedemann model to cohabit and to modify only the one we are truly working on      
    
    #creating an output folder for that calibration
    if not os.path.isdir(config.path_to_output_folder):
        os.makedirs(config.path_to_output_folder)

    filename, last_num =  write.defineName(config.path_to_output_folder, 'Calibration')
    working_path = os.path.join(config.path_to_output_folder, filename)
    os.makedirs(working_path)

    #preparing networks for calibration
    for net in networks:        

        #looking for version errors in the traj files
        for traj in net.traj_paths:
            video_data_list = write.load_traj(traj)
            if video_data_list[0] == 'TrajVersionError':
                print 'traj file ' +str(traj.split(os.sep)[-1]) + 'yielded incorect version number'
                running = vissim.isVissimRunning(True)
                sys.exit()

        #launching a vissim instance for each network object
        ### currently there is a maximum of 4 networks objects because of the maximum of 4 vissim instances....
        vissim.startVissim()
                        
        #moving required inpx file to the calibration location
        shutil.copy(net.inpx_path, os.path.join(working_path, net.inpx_path.split(os.sep)[-1]))
        
    #moving calib.py
    calib_path = os.path.join(working_path, 'calib.py')
    shutil.copy('.\include\calib.py', calib_path)
    
    #moving NOMAD and param.txt
    #TODO: parse param file to adjust:
    #                           DIMENSION     = len(variables)
    #                           X0            = variables.vissim_default OR a sampling method with a loop on the calling of NOMAD to search the space
    #                           LOWER_BOUNDS  = variables.vissim_min
    #                           UPPER_BOUNDS  = variables.vissim_max
    #                           SOLUTION_FILE = decide the path to make it consistant with the printing
    shutil.copy(config.path_to_NOMAD, os.path.join(working_path,'nomad.exe'))
    shutil.copy(config.path_to_NOMAD_param,os.path.join(working_path,config.path_to_NOMAD_param.split(os.sep)[-1]))

    ##TODO: this is where i stoped the debugging so far        
    #generating a config file to be read by calib.py
    write.write_calib(working_path, parameters, variables, networks)
		
    #creating an history file for calib.py
    write.create_history(working_path, 'calib_history.txt', networks)
    
    #launching NOMADS
    try:    
        call = subprocess.call('cd ' + str(working_path), shell = True )
        call = subprocess.check_call('nomad.exe ' + str(config.path_to_NOMAD_param.split(os.sep)[-1]), shell = True) 
    except subprocess.CalledProcessError as c:
        print ('The call ' + str(c.cmd) + ' raised an exception \n'
               'Nomad does not permit error capture from the cmd line... \n'
               'Please open a command window and start Nomad... and type: \n'
               '...\n'
               '   cd ' + str(working_path) + '\n'
               '   nomad.exe ' + str(config.path_to_NOMAD_param.split(os.sep)[-1]) + '\n'
               '...\n'
               'Look for the error and correct it before relaunching pvc_calibration \n')
        sys.exit()
        

    #load and print NOMAD output
    if config.NOMAD_solution_filename != '':
        if os.path.isfile(os.path.join(os.sep(),config.NOMAD_solution_filename)):
            with open(os.path.join(working_path,config.NOMAD_solution_filename), 'w') as solution:
                for l in solution:
                    print l.strip()
        else:
            print 'no solution file found, see history file'

    #delete copied files ... NOMAD, NOMAD_param, inpx, calib.py
    os.remove(os.path.join(working_path,'nomad.exe'))   #NOMAD
    os.remove(os.path.join(working_path,config.path_to_NOMAD_param.split(os.sep)[-1]))    #NOMAD param.txt
    os.remove(os.path.join(working_path,'pvcdata.calib'))    #Serialized data
    os.remove(os.path.join(working_path,config.inpx_path.split(os.sep)[-1]))    #main inpx
    

###################
# Launch main
###################
if __name__ == "__main__":
    main()