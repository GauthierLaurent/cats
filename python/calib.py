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

################################ 
#        Native dependencies      
################################
import os, sys, multiprocessing
import cPickle as pickle

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

    #load informations from pvcdata.calib
    parameters, variables, networks = write.load_calib()

    #load NOMAD points to try
    nomad_points = write.read_from_NOMAD(argv)
        
    #define NOMAD output name
    output_name = argv.replace('input','output')

    #load last_num from history file
    last_num = write.read_history('calib_history.txt')
    
    #add the value of the points in this new variable
    for i in xrange(len(variables)):
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
        write.write_history(last_num, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')        
        write.write_for_NOMAD(output_name, fout)                
        return 0

    #create subfolder for this point's evaluation
    filename = write.findCalibName(os.getcwd())
    point_folderpath = write.createSubFolder(os.path.join(os.getcwd(), filename), filename)

    config = pconfig.Config('calib.cfg')  
        
    #pass data to vissim and simulate
    if len(networks) == 1:
        ##run the analysis
        parameters[5] = multiprocessing.cpu_count() - 1
        inputs = [config, variables, parameters, point_folderpath, os.getcwd(), False]
        packed_outputs = analysis.runVissimForCalibrationAnalysis(networks, inputs)

        if packed_outputs[0] is False:
            write.write_history(last_num, nomad_points, networks, 'crashed', os.getcwd(), 'calib_history.txt') 
            return 1
        else:
            fout = packed_outputs[0]
            networks = packed_outputs[1]

    else:
        ##run the analysis through workers -- separate with networks
        commands = FalseCommands()
        inputs = [config, variables, parameters, point_folderpath, os.getcwd(), True]
        for net in networks:            
            unpacked_outputs = define.createWorkers(networks, analysis.runVissimForCalibrationAnalysis, inputs, commands, min(len(networks),4))
        
        p_values = []
        networks = []

        for packed in unpacked_outputs:
            p_values += packed[0]
            networks.append(packed[1])

        if define.isbool(p_values):
            write.write_history(last_num, nomad_points, networks, 'crashed', os.getcwd(), 'calib_history.txt') 
            return 1
        else:
            fout = max(p_values)

    #write to history
    write.write_history(last_num, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')
    
    #write for NOMAD
    write.write_for_NOMAD(output_name, fout) 

    return 0

###################
# Launch main
###################
if __name__ == "__main__": 
   
    main(sys.argv[1])
