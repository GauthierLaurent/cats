#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Laurent Gauthier, Ecole Polytechnique de Montreal, 2014
#  Python 2.7; (dt) Spyder Windows 7 64-bit; Vissim 6.0 64-bit
#  Dependencies listed in Libraries; 
################################################################################
'''
to import a starting point, call with -p __list of points separated by comma__
ex: -p 1.0,-2.0,3.0,4.5,6  | the list may or may not be enclosed in brackets
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
    commands = config.commands(optparse.OptionParser(),'Cali')
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

    ##looking for an input starting point
    if commands.start_point is not None:    
        starting_point = commands.start_point.replace('[','').replace(']','').split(',')
        
        #checking for compatibility with the number of parameter specified
        if len(starting_point) == len(variables):
            for p in xrange(len(starting_point)):
                starting_point[p] = float(starting_point[p])            
        else:
            print ('Lenght of startign point does not match the number of variables to be be processed...\n'
                   'Aborting current evaluation\n'
                   'Please correct starting point vector')
            return
    else:
        starting_point = []
        
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
                return

        #launching a vissim instance for each network object
        ### currently there is a maximum of 4 networks objects because of the maximum of 4 vissim instances....
        vissim.startVissim()
                        
        #moving required inpx file to the calibration location
        shutil.copy(net.inpx_path, os.path.join(working_path, net.inpx_path.split(os.sep)[-1]))
        
    #moving calib.py and calib.cfg
    shutil.copy('.\include\calib.py', os.path.join(working_path, 'calib.py'))
    shutil.copy('.\calib.cfg', os.path.join(working_path, 'calib.cfg'))
    
    #making sure the param file exists and is well suited to the present task
    write.NOMAD.verify_params(config.path_to_NOMAD_param, variables, starting_point)    
    write.NOMAD.set_BB_path(config.path_to_NOMAD_param, 'calib.py')
    
    #moving NOMAD and param.txt
    param_file = config.path_to_NOMAD_param.split(os.sep)[-1]        
    shutil.copy(config.path_to_NOMAD, os.path.join(working_path,'nomad.exe'))
    shutil.copy(config.path_to_NOMAD_param,os.path.join(working_path,param_file))
     
    #generating a config file to be read by calib.py
    write.write_calib(working_path, parameters, variables, networks)
		
    #creating an history file for calib.py
    write.History.create_history(working_path, 'calib_history.txt', networks)    
    
    #launching NOMADS
    try:
        os.chdir(working_path)
        out = open('this_file.txt','w')
        subprocess.check_call('nomad.exe' + ' ' + param_file, stderr = out, shell = True) 
        
    except subprocess.CalledProcessError:
        out.close()
        err = open('this_file.txt','r')
        for l in err:
            print l.strip()
        err.close()
        return

    #delete copied files ... NOMAD, NOMAD_param, inpx, calib.py   
    os.remove(os.path.join(working_path,'nomad.exe'))                                       #NOMAD
    os.remove(os.path.join(working_path,config.path_to_NOMAD_param.split(os.sep)[-1]))      #NOMAD param.txt
    os.remove(os.path.join(working_path,'pvcdata.calib'))                                   #Serialized data
    os.remove(os.path.join(working_path,'calib.py'))                                        #calib.py
    os.remove(os.path.join(working_path,'calib.cfg'))                                       #calib config file
    for net in networks:    
        os.remove(os.path.join(working_path,net.inpx_path.split(os.sep)[-1]))               #main inpx
    
    return

###################
# Launch main
###################
if __name__ == "__main__": 
    main()