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
    import os, sys, time, argparse, random

    #Internal
    import pvc_vissim     as vissim
    import pvc_write      as write
    import pvc_workers    as workers
    import pvc_configure  as configure
    import pvc_analysis   as analysis
    import pvc_calibTools as calibTools
    import pvc_csvParse   as csvParse

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
    commands = configure.commands(argparse.ArgumentParser(),'Sensi')
    config   = configure.Config('pvc.cfg')

    #overrides default inpx file if command -f was used and Updating the default inpx name to match the file
    if commands.file:
        if not commands.file.endswith('inpx'):
            config.inpx_name = commands.file + str('.inpx')
        else:
            config.inpx_name = commands.file

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
    if not os.path.isdir(os.path.join(MainInpxPath,'Analysis_on__' + InpxName.strip('.inpx'))):
        os.makedirs(os.path.join(MainInpxPath,'Analysis_on__' + InpxName.strip('.inpx')))

    WorkingPath = os.path.join(MainInpxPath,'Analysis_on__' + InpxName.strip('.inpx'))

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
        first_seed = random.randint(1,1000)
        increments = random.randint(1,100)
    parameters = [config.sim_steps, first_seed, config.nbr_runs, Sim_lenght, sim_cores, increments]
    VissimCorridors = csvParse.extractCorridorsFromCSV(InpxPath, InpxName, 'vissim')

    ######################################
    #        One at a time Sensitivity Analysis
    ######################################
    if commands.analysis == 'OAT':
        TypeOfAnalysis = 'Sensitivity'

        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)

        #building the model values ranges
        if commands.verbose is True:
            print '-> Generating the range values and default values from memory'

        #generating the raw variables contained in the csv
        variables = csvParse.extractParamFromCSV(InpxPath,InpxName)

        #gathering the variables that need to be analysed
        working_variables = [i for i in variables if i.include is True]

        #creating default values
        default_values =  [variables[i].vissim_default for i in xrange(len(variables))]
        concat_variables = [variables[i].vissim_name for i in xrange(len(variables))]

        #opening the output file and writing the appropriate header
        if commands.verbose is True:
            print '-> Generating relevant subfolders for the analysis\n'

        out, subdirname = write.writeSensitivityHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName)

        #creating appropriate output folder and graphic folder (if option is "on")
        graphspath = None
        if commands.vis_save:
            graphspath = write.createSubFolder(os.path.join(subdirname,'graphs'), 'graphs')
            write.createSubFolder(os.path.join(graphspath, 'cumul_dist_graphs'), 'cumul_dist_graphs')
            write.createSubFolder(os.path.join(graphspath, 'distribution_graphs'), 'distribution_graphs')
            for i in range(len(variables) +1):
                if i == 0:
                    write.createSubFolder(os.path.join(graphspath, 'cumul_dist_graphs', 'Default_values'), 'cumul_dist_graphs' + os.sep + 'Default_values')
                    write.createSubFolder(os.path.join(graphspath, 'distribution_graphs', 'Default_values'), 'cumul_dist_graphs' + os.sep + 'Default_values')
                else:
                    write.createSubFolder(os.path.join(graphspath, 'cumul_dist_graphs', variables[i-1].name), 'cumul_dist_graphs' + os.sep + variables[i-1].name)
                    write.createSubFolder(os.path.join(graphspath, 'distribution_graphs', variables[i-1].name), 'cumul_dist_graphs' + os.sep + variables[i-1].name)
        outputspath = write.createSubFolder(os.path.join(subdirname,'outputs'), 'outputs')

        #treating the simulations
        ##calculating the default values
        inputs = [variables, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, commands.verbose, VissimCorridors]
        text, firstrun_results = analysis.OAT_sensitivity(workers.intelligentChunks(len(variables), variables, concat_variables), inputs, default = True)

        ##Running the rest of the simulations
        if commands.multi is True:
            #TODO: transform analysis.sensitivityAnalysis to accomodate for more than 4 process
            '''for minChunkSize: there is a max number of 4 vissim instances that can be ran at the same time...
               the min 4 is to make sure not more than 4 instances are processed at the same time.
               A way to deal with this would be to generate the simulations, than have a crawler reach through the
               folders to deal with the outputs - possibly while the next simulations are being processed'''

            minChunkSize = min(4,workers.countPoints(concat_variables, config.nbr_points, config.nbr_runs))
            inputs = [variables, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, False, VissimCorridors, firstrun_results]
            unpacked_outputs = workers.createWorkers(working_variables, analysis.OAT_sensitivity, inputs, commands, minChunkSize, concat_variables)
            #unpacking the outputs -- the outputs here come back with 3 layers: nbr of chunk/runs in the chunk/text -- ie: text = unpacked_outputs[0][0]
            for i in unpacked_outputs:
                for j in i:
                    text.append(j)

        else:
            inputs = [variables, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters, commands.verbose, VissimCorridors, firstrun_results]
            packed_outputs = analysis.OAT_sensitivity(workers.intelligentChunks(len(working_variables), working_variables, concat_variables), inputs)
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
    if commands.analysis == 'MC':
        TypeOfAnalysis = 'Monte Carlo'

        if commands.verbose is True: write.verboseIntro(commands, config, TypeOfAnalysis)


        #building the model values ranges
        if commands.verbose is True:
            print '-> Generating the range values and default values from memory'

        #generating the raw variables contained in the csv
        variables = csvParse.extractParamFromCSV(InpxPath,InpxName)

        #removing unwanted variables for this weidemann model
        working_variables = [i for i in variables if i.include is True]

        print('       WARNING - THE MODULE IS PRESENTLY NON-FUNCTIONAL - WARNING \n'
              ' \n'
              'reason: working_variables contains only the desired variables for this run. \n'
              'variables contains the whole set \n'
              ' \n'
              'ie: if we do not want to test for variable x, we can still aply a fixed point \n'
              '    via the default value. this ensures that we control the other variables so  \n'
              '    that no unexpected variations occurs outside of what we are actualy testing  \n'
              ' \n'
              '   this needs to be implemented. \n')
        sys.exit()

        #creating default values
        default_values =  [variables[i].vissim_default for i in xrange(len(variables))]
        concat_variables = [variables[i].vissim_name for i in xrange(len(variables))]

        #opening the output file and writing the appropriate header
        if commands.verbose is True:
            print '-> Generating relevant subfolders for the analysis'

        out, subdirname = write.writeSensitivityHeader(WorkingPath, concat_variables, TypeOfAnalysis, config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName)

        #creating appropriate output folder and graphic folder (if option is "on")
        outputspath = write.createSubFolder(os.path.join(subdirname,'outputs'), 'outputs')
        if commands.verbose is True:
            print '-> Name of the report file: ' + subdirname.split(os.sep)[-1] + '.csv\n'

        #creating 1000 random values
        valuesVector = calibTools.genMCsample(variables, 1000)

        #treating the simulations
        if commands.verbose:
            print '=== Starting the modelisations of the ' + str(len(valuesVector)) + ' points ==='

        if commands.multi is True:
            cores_per_process, number_of_process, unused_cores = workers.cpuPerVissimInstance()
            minChunkSize = number_of_process
            parameters[5] = cores_per_process
            out_valuesVector = []
            inputs = [variables, InpxPath, InpxName, outputspath, commands, running, parameters, valuesVector]
            unpacked_outputs = workers.createWorkers(valuesVector, analysis.monteCarlo_vissim, inputs, commands, minChunkSize)
            #unpacking the outputs -- the outputs here come back with 3 layers: nbr of chunk/runs in the chunk/text -- ie: text = unpacked_outputs[0][0]
            for k in unpacked_outputs:
                out_valuesVector += k

        else:
            inputs = [variables, InpxPath, InpxName, outputspath, commands, running, parameters]
            out_valuesVector = analysis.monteCarlo_vissim(valuesVector, inputs)

        #treating the outputs
        if commands.verbose:
            print '\n=== Starting the treatments of the ' + str(len(valuesVector)) + ' points simulated ==='

        text = []
        ##note: data is now passed as [[list of values], path_to_folder]
        if commands.multi is True:
            minChunkSize = workers.monteCarloCountPoints(len(valuesVector), config.nbr_runs)
            inputs = [variables, parameters, outputspath, config, commands, VissimCorridors, InpxName]
            unpacked_outputs = workers.createWorkers(out_valuesVector, analysis.monteCarlo_outputs, inputs, commands, minChunkSize)

            for k in unpacked_outputs:
                for j in k:
                    text.append(j)

        else:
            inputs = [variables, parameters, outputspath, config, commands, VissimCorridors, InpxName]
            packed_outputs = analysis.monteCarlo_outputs(out_valuesVector, inputs)

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
if __name__ == '__main__':

    main()

