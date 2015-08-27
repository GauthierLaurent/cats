#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Laurent Gauthier, Ecole Polytechnique de Montreal, 2014
#  Python 2.7; (dt) Spyder Windows 7 64-bit; Vissim 6.0 64-bit;
#  NOMAD 3.7.1 https://www.gerad.ca/nomad/Project/Home.html
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
import os, sys, multiprocessing, shutil, random, traceback, copy, subprocess

################################
#        Main
################################
def main(argv):

    #Internal
    import pvc_write     as write
    import pvc_mathTools as mathTools
    import pvc_configure as configure
    import pvc_csvParse  as csvParse
    import pvc_analysis  as analysis
    import pvc_outputs   as outputs

    config = configure.Config('calib.cfg')

    #load informations from pvcdata.calib
    parameters, variables, networks = write.load_calib()

    #define NOMAD output name
    #output_name = argv.replace('input','output')

    #create subfolder for this point's evaluation
    if 'Validation' not in str(os.getcwd()).split(os.sep)[-1]:
        filename = write.findCalibName(os.getcwd())
        point_folderpath = write.createSubFolder(os.path.join(os.getcwd(), filename), filename)
    else:
        point_folderpath = copy.deepcopy(os.getcwd())

    #load last_num from history file
    #NB: because of the header line, we must substract one from the standard output of the find_last_number function
    #last_num = write.History.find_last_number('calib_history.txt') - 1
    if 'Validation' not in str(os.getcwd()).split(os.sep)[-1]:
        last_num = filename.split('_')[-1]
    else:
        last_num = 1

    if config.random_seed is True:
        parameters[1] = random.randint(1,700)
        parameters[5] = random.randint(1,100)

    store = [parameters[1], parameters[5]] #first seed, increment

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
    chk = csvParse.verifyDesiredPoints(variables)

    if not chk:
        fout = ['inf', 1, 1, 1]

        #adding fail info to the networks
        for net in networks:
            for traj in net.traj_paths:
                net.addVideoComparison(['BoundingError'])

        #history
        seeds = [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)]
        write.History.write_history(last_num, seeds, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')

        #output
        return 1

    #move all inpx files to the point folder
    if 'Validation' not in str(os.getcwd()).split(os.sep)[-1]:
        for net in networks:
            shutil.copy(os.path.join(os.getcwd(),net.inpx_path.split(os.sep)[-1]), os.path.join(point_folderpath, net.inpx_path.split(os.sep)[-1]))

            #moving any rbc file found
            files = [f for f in os.listdir(os.getcwd()) if 'rbc' in f]
            for f in files:
                shutil.copy(os.path.join(os.getcwd(), f), os.path.join(point_folderpath, f))

    #pass data to vissim and simulate

    '''
    #TEST NEEDS TO BE OUT OF TRY/EXCEPT
    ##run the analysis
    parameters[4] = multiprocessing.cpu_count() - 1
    inputs = [config, variables, parameters, point_folderpath]
    unpacked_outputs = analysis.runVissimForCalibrationAnalysis(networks, inputs)
    if mathTools.isbool(list(unpacked_outputs)):
        print 'end crashed'
        import pdb;pdb.set_trace()
    else:
        fout = outputs.sort_fout_and_const(unpacked_outputs[0])
        print fout
        import pdb;pdb.set_trace()
    #'''

    try:
        ##run the analysis
        parameters[4] = multiprocessing.cpu_count() - 1
        inputs = [config, variables, parameters, point_folderpath]
        unpacked_outputs = analysis.runVissimForCalibrationAnalysis(networks, inputs)

        if mathTools.isbool(list(unpacked_outputs)):
            seeds = [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)]
            write.History.write_history(last_num, seeds, nomad_points, networks, ['crashed', 'NaN', 'NaN', 'NaN', 'NaN'], 'Unfeasible', os.getcwd(), 'calib_history.txt')
            return 1
        else:
            fout = outputs.sort_fout_and_const(unpacked_outputs[0])
            networks = unpacked_outputs[1]
            seeds = [store[0]+(i-1)*store[1] for i in unpacked_outputs[2]]
            feasability = 'Feasible'
            for net in networks:
                if net.feasibility == 'Unfeasible':
                    feasability = 'Unfeasible'

    except:
        for net in networks:
            net.addVideoComparison([sys.exc_info()[0]])

        seeds = [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)]

        tmp = outputs.Derived_data()
        tmp.activateConstraints(config)
        fout = ['inf'] + [1 for i in tmp.getActiveConstraintNames()]

        write.History.write_history(last_num, seeds, nomad_points, networks, ['err', 'NaN', 'NaN', 'NaN', 'NaN'], 'Unfeasible', os.getcwd(), 'calib_history.txt')

        with open('run_'+str(last_num)+'.err','w') as err:
            err.write(traceback.format_exc())

        out = ''
        for f in fout:
            out += str(f)+' '
        print out
        return 1

    #write to history
    write.History.write_history(last_num, seeds, nomad_points, networks, fout, feasability, os.getcwd(), 'calib_history.txt')

    #output for NOMAD
    out = ''
    for f in fout:
        out += str(f)+' '
    print out

    #cleanpointFolder
    subprocess.Popen([sys.executable, os.path.join(os.getcwd(),'cleanPointFolder.py'), last_num], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return 0

###################
# Launch main
###################
if __name__ == "__main__":

    main(sys.argv[1])
