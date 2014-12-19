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
import os, sys, multiprocessing, shutil

################################ 
#        Misc tools     
################################
class FalseCommands:
    '''this serves only to spoof the worker function'''
    def __init__(self):
        self.verbose    = False
        self.multi_test = False
        
################################ 
#        Main       
################################
def main(argv):
    
    #Internal
    import pvc_write    as write 
    import pvc_define   as define
    import pvc_config   as pconfig
    import pvc_analysis as analysis
    import pvc_vissim   as vissim

    #load informations from pvcdata.calib
    parameters, variables, networks = write.load_calib()

    #load NOMAD points to try
    nomad_points = write.NOMAD.read_from_NOMAD(argv)
        
    #define NOMAD output name
    #output_name = argv.replace('input','output')
        
    #load last_num from history file
    #NB: because of the header line, we must substract one from the standard output of the read_history function
    last_num = write.History.read_history('calib_history.txt') - 1
    
    #add the value of the points in this new variable
    for i in xrange(len(variables)):
        if variables[i].include is True:
            variables[i].point = nomad_points[i]
        
    #verify bounds proposed by NOMADS
    chk = define.verifyDesiredPoints(variables)
    
    if not chk:
        fout = 'inf'

	#adding fail info to the networks
	for net in networks:
	    for traj in net.traj_path:
		net.addVideoComparison(['BoundingError'])

        #history
        write.History.write_history(last_num, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')
        
        #output
        print fout                 
        return 0

    #create subfolder for this point's evaluation
    filename = write.findCalibName(os.getcwd())
    point_folderpath = write.createSubFolder(os.path.join(os.getcwd(), filename), filename)

    #move all inpx files to the point folder
    for net in networks:
        shutil.copy(os.path.join(os.getcwd(),net.inpx_path.split(os.sep)[-1]), os.path.join(point_folderpath, net.inpx_path.split(os.sep)[-1]))

    config = pconfig.Config('calib.cfg')  
    #assing vissim instances to each network
    for net in networks:
        net.addVissim(vissim.startVissim())
        
    #pass data to vissim and simulate
    if len(networks) == 1:
        ##run the analysis
        parameters[5] = multiprocessing.cpu_count() - 1
        inputs = [config, variables, parameters, point_folderpath, False]
        packed_outputs = analysis.runVissimForCalibrationAnalysis(networks, inputs)

        if packed_outputs[0] is False:
            write.History.write_history(last_num, nomad_points, networks, 'crashed', os.getcwd(), 'calib_history.txt') 
            return 1
        else:
            fout = max(packed_outputs[0])
            networks = [packed_outputs[1]]

    else:
        ##run the analysis through workers -- separate with networks
        commands = FalseCommands()
        inputs = [config, variables, parameters, point_folderpath, True]
        for net in networks:            
            unpacked_outputs = define.createWorkers(networks, analysis.runVissimForCalibrationAnalysis, inputs, commands, min(len(networks),4))
        
        d_stat = []
        networks = []

        for packed in unpacked_outputs:
            d_stat += packed[0]
            networks.append(packed[1])

        if define.isbool(d_stat):
            write.History.write_history(last_num, nomad_points, networks, 'crashed', os.getcwd(), 'calib_history.txt') 
            return 1
        else:
            fout = max(d_stat)

    #write to history
    write.History.write_history(last_num, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')
    
    #output for NOMAD
    print fout 
    return 0

###################
# Launch main
###################
if __name__ == "__main__": 
   
    main(sys.argv[1])
