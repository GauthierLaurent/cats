#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Laurent Gauthier, Ecole Polytechnique de Montreal, 2014
#  Python 2.7; (dt) Spyder Windows 7 64-bit; Vissim 6.0 64-bit;
#  NOMAD 3.6.2 https://www.gerad.ca/nomad/Project/Home.html 
#  Dependencies listed in Libraries; 
################################################################################
'''Dev stuff
import pdb; pdb.set_trace()

IMPORTANT INFORMATION:
except in the function write.write_for_NOMAD, **no** print command
must be present in any part of this code or any of it's function calls. Such a
print would give NOMAD an erronous result of the called point
'''
################################################################################

################################ 
#        Native dependencies      
################################
import os, sys, multiprocessing, shutil, random

       
################################ 
#        Main       
################################
def main(argv):

    #Internal
    import pvc_write    as write 
    import pvc_define   as define
    import pvc_config
    import pvc_analysis as analysis
    import pvc_vissim   as vissim
    import pvc_outputs  as outputs

    config = pvc_config.Config('calib.cfg')

    #load informations from pvcdata.calib
    parameters, variables, networks = write.load_calib()
       
    #define NOMAD output name
    #output_name = argv.replace('input','output')

    #create subfolder for this point's evaluation
    filename = write.findCalibName(os.getcwd())
    point_folderpath = write.createSubFolder(os.path.join(os.getcwd(), filename), filename)
        
    #load last_num from history file
    #NB: because of the header line, we must substract one from the standard output of the find_last_number function
    #last_num = write.History.find_last_number('calib_history.txt') - 1
    last_num = filename.split('_')[-1]

    if config.random_seed is True:
        parameters[1] = random.randint(1,700)
        parameters[5] = random.randint(1,100)
        
        seeds = [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)]
        
    #gathering the variables that need to be analysed
    to_include_list = [i for i in variables if i.include is True]

    #load NOMAD points to try
    nomad_points = write.NOMAD.read_from_NOMAD(argv)

    #add the value of the points in this new variable
    for i in xrange(len(variables)):
        if variables[i].include is True:
            variables[i].point = nomad_points[to_include_list.index(variables[i])]
        else:
            variables[i].point = variables[i].desired_value
    
    #verify bounds proposed by NOMADS
    chk = define.verifyDesiredPoints(variables)    
    
    if not chk:
        fout = ['inf', 1, 1, 1]

	#adding fail info to the networks
	for net in networks:
	    for traj in net.traj_paths:
		net.addVideoComparison(['BoundingError'])

        #history
        write.History.write_history(last_num, seeds, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')
        
        #output
        print  '{} {} {} {}'.format(fout[0], fout[1], fout[2], fout[3])    
        return 0

    #move all inpx files to the point folder
    for net in networks:
        shutil.copy(os.path.join(os.getcwd(),net.inpx_path.split(os.sep)[-1]), os.path.join(point_folderpath, net.inpx_path.split(os.sep)[-1]))
  
    #assing vissim instances to each network
    for net in networks:
        net.addVissim(vissim.startVissim())
        
    #pass data to vissim and simulate
    if len(networks) == 1:
        ##run the analysis
        parameters[4] = multiprocessing.cpu_count() - 1
        inputs = [config, variables, parameters, point_folderpath, False]
        unpacked_outputs = analysis.runVissimForCalibrationAnalysis(networks, inputs)

        if define.isbool(list(unpacked_outputs)):
            write.History.write_history(last_num, seeds, nomad_points, networks, ['crashed', 'NaN', 'NaN', 'NaN'], os.getcwd(), 'calib_history.txt') 
            return 1
        else:
            fout = outputs.sort_fout_and_const(unpacked_outputs[0])
            networks = [unpacked_outputs[1]]

    else:
        ##run the analysis through workers -- separate with networks
        commands = define.FalseCommands()
        inputs = [config, variables, parameters, point_folderpath, True]
        for net in networks:            
            packed_outputs = define.createWorkers(networks, analysis.runVissimForCalibrationAnalysis, inputs, commands, min(len(networks),4))
        
        d_stat = []
        networks = []

        for unpacked in packed_outputs:
            d_stat.append(unpacked[0])
            networks.append(unpacked[1])

        if define.isbool(d_stat):
            write.History.write_history(last_num, seeds, nomad_points, networks, ['crashed', 'NaN', 'NaN', 'NaN'], os.getcwd(), 'calib_history.txt') 
            return 1
        else:
            fout = outputs.sort_fout_and_const(d_stat)

    #write to history
    write.History.write_history(last_num, seeds, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')
    
    #output for NOMAD
    print '{} {} {} {}'.format(fout[0], fout[1], fout[2], fout[3]) 
    return 0

###################
# Launch main
###################
if __name__ == "__main__": 
   
    main(sys.argv[1])
