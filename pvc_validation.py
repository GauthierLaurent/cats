# -*- coding: utf-8 -*-
"""
Created on Tue May 19 23:08:54 2015

@author: Laurent
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Laurent Gauthier, Ecole Polytechnique de Montreal, 2014
#  Python 2.7; (dt) Spyder Windows 7 64-bit; Vissim 6.0 64-bit
#  Dependencies listed in Libraries;2222
################################################################################
'''
to import a starting point, call with -p __list of points separated by spaces__
ex: -p 1.0 -2.0 3.0 4.5 6
'''
################################################################################

def main():
    ################################
    #        Importing dependencies
    ################################

    #Native dependencies
    import os, sys, shutil, argparse, subprocess, random

    #Internal
    import pvc_write      as write
    import pvc_vissim     as vissim
    import pvc_calibTools as calibTools
    import pvc_configure  as configure
    import pvc_csvParse   as csvParse
    import pvc_outputs    as outputs

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
    commands = configure.commands(argparse.ArgumentParser(),'Cali')
    config   = configure.Config('calib.cfg')

    ######################################
    #        Preparing  environnement
    ######################################
    #Checking if Vissim is already running and closing it to avoid problems latter on
    running = vissim.isVissimRunning(kill=True)
    if running is not False:
        print 'Could not close Vissim, the program may potentially have problems with the COM interface'

    ##Vissim simulation parameters
    Sim_lenght = config.simulation_time + config.warm_up_time
    sim_cores = 1
    if config.random_seed is False:
        first_seed = config.first_seed
        increments = config.increments
    else:
        first_seed = random.randint(1,700)
        increments = random.randint(1,10)
    parameters = [config.sim_steps, first_seed, config.nbr_runs, Sim_lenght, sim_cores, increments]

    #determining vissim, video, and corridor lists
    networks = calibTools.Network.buildNetworkObjects(config)

    #generating the raw variables contained in the csv
    variables = csvParse.extractParamFromCSV(config.path_to_csv, config.inpx_name.strip('inpx') + 'csv')

    ##looking for an input starting point
    if commands.start_point is not None:
        starting_point = commands.start_point

        #checking for compatibility with the number of parameter specified
        if len(starting_point) == len([i for i in variables if i.include is True]):
            for p in xrange(len(starting_point)):
                starting_point[p] = float(starting_point[p])
        else:
            print ('Lenght of starting point does not match the number of variables to be be processed...\n'
                   'Number of variables to process: ' + str(len([i for i in variables if i.include is True])) + '\n'
                   'Lenght of starting point given: ' + str(len(starting_point)) + '\n'
                   'Aborting current evaluation\n'
                   'Please correct starting point vector')
            return
    else:
        starting_point = [var.desired_value for var in variables if var.include is True]

    #creating an output folder for that calibration
    if not os.path.isdir(config.path_to_output_folder):
        os.makedirs(config.path_to_output_folder)

    filename, last_num =  write.defineName(config.path_to_output_folder, 'Validation')
    working_path = os.path.join(config.path_to_output_folder, filename)
    os.makedirs(working_path)

    #preparing networks for calibration
    for net in networks:

        #looking for version errors in the traj files
        for traj in net.traj_paths:
            video_data_list = write.load_traj(traj)
            if video_data_list == 'TrajVersionError':
                print 'traj file ' +str(traj.split(os.sep)[-1]) + 'yielded incorect version number'
                running = vissim.isVissimRunning(True)
                return

        #moving required inpx file to the calibration location
        shutil.copy(net.inpx_path, os.path.join(working_path, net.inpx_path.split(os.sep)[-1]))

    #moving calib.py and calib.cfg
    shutil.copy(os.path.join(os.path.curdir, 'include', 'calib.py'), os.path.join(working_path, 'calib.py'))
    shutil.copy(os.path.join(os.path.curdir,'calib.cfg'), os.path.join(working_path, 'calib.cfg'))

    #moving a copy of the csv file (needed for visualization tools)
    shutil.copy(os.path.join(config.path_to_csv, config.inpx_name.strip('inpx') + 'csv'), os.path.join(working_path, config.inpx_name.strip('inpx') + 'csv'))

    #generating a config file to be read by calib.py
    write.write_calib(working_path, parameters, variables, networks)

    #creating an history file for calib.py
    variable_names = [i.name for i in variables if i.include is True]
    write.History.create_history(working_path, 'calib_history.txt',  config.nbr_runs, variable_names, networks, outputs.ActiveConstraints.getNumberOfConstraints(config))

    point = ''
    for p in  starting_point:
        point += str(p)+'\t'

    #generating point file
    with open(os.path.join(working_path, 'validation_point.txt'), 'w') as valid_point:
        valid_point.write(point)

    #launching Calib.py
    try:
        os.chdir(working_path)
        out = open('error_file.txt','w')
        subprocess.check_call('calib.py' + ' validation_point.txt', stderr = out, shell = True)

    except subprocess.CalledProcessError:
        out.close()
        err = open('error_file.txt','r')
        for l in err:
            print l.strip()
        err.close()
        return

###################
# Launch main
###################
if __name__ == "__main__":
    main()