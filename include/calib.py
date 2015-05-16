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
import os, sys, multiprocessing, shutil, random, traceback

################################
#        Main
################################
def main(argv):

    #Internal
    import pvc_write     as write
    import pvc_workers   as workers
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
    filename = write.findCalibName(os.getcwd())
    point_folderpath = write.createSubFolder(os.path.join(os.getcwd(), filename), filename)

    #load last_num from history file
    #NB: because of the header line, we must substract one from the standard output of the find_last_number function
    #last_num = write.History.find_last_number('calib_history.txt') - 1
    last_num = filename.split('_')[-1]

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
    for net in networks:
        shutil.copy(os.path.join(os.getcwd(),net.inpx_path.split(os.sep)[-1]), os.path.join(point_folderpath, net.inpx_path.split(os.sep)[-1]))

    #pass data to vissim and simulate

    if len(networks) == 1:

        '''
        #TEST NEEDS TO BE OUT OF TRY/EXCEPT
        ##run the analysis
        parameters[4] = multiprocessing.cpu_count() - 1
        inputs = [config, variables, parameters, point_folderpath, False]
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
            inputs = [config, variables, parameters, point_folderpath, False]
            unpacked_outputs = analysis.runVissimForCalibrationAnalysis(networks, inputs)

            if mathTools.isbool(list(unpacked_outputs)):
                seeds = [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)]
                write.History.write_history(last_num, seeds, nomad_points, networks, ['crashed', 'NaN', 'NaN', 'NaN', 'NaN'], os.getcwd(), 'calib_history.txt')
                return 1
            else:
                fout = outputs.sort_fout_and_const(unpacked_outputs[0])
                networks = [unpacked_outputs[1]]
                seeds = [store[0]+(i-1)*store[1] for i in unpacked_outputs[2]]

        except:
            for net in networks:
                net.addVideoComparison([sys.exc_info()[0]])

            seeds = [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)] + ['|']

            fout = ['inf', 1, 1, 1, 1]

            write.History.write_history(last_num, seeds, nomad_points, networks, ['err', 'NaN', 'NaN', 'NaN', 'NaN'], os.getcwd(), 'calib_history.txt')

            with open('run_'+str(last_num)+'.err','w') as err:
                err.write(traceback.format_exc())


            print '{} {} {} {} {}'.format(fout[0], fout[1], fout[2], fout[3], fout[4])
            return 1

    else:
        try:
            ##run the analysis through workers -- separate with networks
            commands = workers.FalseCommands()
            inputs = [config, variables, parameters, point_folderpath, True]
            packed_outputs = workers.createWorkers(networks, analysis.runVissimForCalibrationAnalysis, inputs, commands, defineNbrProcess = min(len(networks),4))

            d_stat = []
            networks = []
            seed_num_list = []

            for unpacked in packed_outputs:
                networks.append(unpacked[1])

                if isinstance(unpacked[0], bool):
                    d_stat.append(unpacked[0])
                else:
                    for t in xrange(len(unpacked[1].traj_paths)): #traj
                        d_stat.append(unpacked[0][t])

            #ordering by network number
            net_order = []
            for i in xrange(len(networks)):
                if networks[i].inpx_path == config.path_to_inpx_file_1: net_order.append(1)
                if networks[i].inpx_path == config.path_to_inpx_file_2: net_order.append(2)
                if networks[i].inpx_path == config.path_to_inpx_file_3: net_order.append(3)
                if networks[i].inpx_path == config.path_to_inpx_file_4: net_order.append(4)

            net_order, d_stat, networks, seed_num_list = mathTools.sortManyLists(net_order, d_stat, networks, seed_num_list)

            if mathTools.isbool(d_stat):
                seeds = []
                for j in xrange(len(seed_num_list)):
                    if seed_num_list[j][0] == 'N/A':
                        seeds += seed_num_list[j] + ['|']
                    else:
                        seeds += [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)]
                    if j < len(seed_num_list)-1:
                        seeds += ['|']

                write.History.write_history(last_num, seeds, nomad_points, networks, ['crashed', 'NaN', 'NaN', 'NaN', 'NaN'], os.getcwd(), 'calib_history.txt')
                return 1
            else:
                fout = outputs.sort_fout_and_const(d_stat)[0]
                seeds = []
                for j in xrange(len(seed_num_list)):
                    seeds += [store[0]+(i-1)*store[1] for i in seed_num_list[j]]
                    if j < len(seed_num_list)-1:
                        seeds += ['|']
        except:
            for net in networks:
                net.addVideoComparison([sys.exc_info()[0]])

            seeds = []
            for j in xrange(parameters[2]):
                seeds += [parameters[1]] + [parameters[1]+i*parameters[5] for i in range(1,config.nbr_runs)]
                if j < parameters[2]-1:
                    seeds += ['|']
            #might need to be bigger???
            fout = ['inf', 1, 1, 1, 1]

            write.write_history(last_num, seeds, nomad_points, networks, os.getcwd(), ['err', 'NaN', 'NaN', 'NaN', 'NaN'], 'calib_history.txt')

            print '{} {} {} {} {}'.format(fout[0], fout[1], fout[2], fout[3], fout[4])
            return 1

    #write to history
    write.History.write_history(last_num, seeds, nomad_points, networks, fout, os.getcwd(), 'calib_history.txt')

    #output for NOMAD
    print '{} {} {} {} {}'.format(fout[0], fout[1], fout[2], fout[3], fout[4])
    return 0

###################
# Launch main
###################
if __name__ == "__main__":

    main(sys.argv[1])
