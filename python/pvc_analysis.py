# -*- coding: utf-8 -*-
'''
Created on Thu Jul 10 14:43:44 2014

@author: Laurent
'''

################################
#        Importing dependencies
################################
#Natives
import os, shutil, sys, copy
from scipy.stats import t, chi2
import cPickle as pickle

#Internal
import pvc_write      as write
import pvc_vissim     as vissim
import pvc_outputs    as outputs
import pvc_calibTools as calibTools
import pvc_workers    as workers
import pvc_configure  as configure
import pvc_csvParse   as csvParse

################################
#        Calibration analysis
################################
def analyseVideoData(final_inpx_path, seed_nums, d_stat, network, N, vissim_data, parameters, config):

    non_dist_data = [vissim_data.oppLCcount, vissim_data.manLCcount, vissim_data.flow]
    dist_data = [vissim_data.forFMgap, vissim_data.oppLCagap, vissim_data.oppLCbgap, vissim_data.manLCagap, vissim_data.manLCbgap, vissim_data.forSpeeds]

    #setting video values
    for traj in network[N].traj_paths:

        #loading video data
        video_data = write.load_traj(traj)
        if video_data == 'TrajVersionError':
            network[N].addVideoComparison(['TrajVersionError'])
        else:
            non_dist_video_data = [video_data.oppLCcount, video_data.manLCcount, video_data.flow]
            video_data.forFMgap.cleanStats(0.5*config.fps)
            video_data.oppLCbgap.cleanStats(0.5*config.fps); vissim_data.oppLCbgap.cleanStats(0.5*config.fps)
            video_data.manLCbgap.cleanStats(0.5*config.fps); vissim_data.manLCbgap.cleanStats(0.5*config.fps)
            dist_video_data = [video_data.forFMgap, video_data.oppLCagap, video_data.oppLCbgap, video_data.manLCagap, video_data.manLCbgap, video_data.forSpeeds]
            #starting the building of the secondary values outputs
            #for the first 3 variables, which are intergers, we use:
            #                       PE = (M-V)/V
            #       with:    V = number from video
            #                M = mean from modelisation
            # of course this would fail is V = 0, in which case we must turn to
            #                       AE = M-V...   with V = 0: AE = M
            #to which we will add a ' * '
            secondary_values = []
            for d in xrange(len(non_dist_data)):
                if non_dist_video_data[d].mean != 0:
                    secondary_values.append([non_dist_data[d].mean, (non_dist_data[d].mean-non_dist_video_data[d].mean)/non_dist_video_data[d].mean])
                else:
                    if non_dist_data[d].mean is not None and non_dist_data[d].mean != 0:
                        secondary_values.append([non_dist_data[d].mean, str(non_dist_data[d].mean)+'*'])
                    else:
                        secondary_values.append(['0.00', '0.00*'])

            #comparing video_values with output values
            mean_list, d_stat_list = calibTools.checkCorrespondanceOfOutputs(dist_video_data, dist_data, parameters[0], config.fps)
            secondary_values += calibTools.buildReportList(mean_list, d_stat_list)

            #adding video comparison data to the network
            network[N].addVideoComparison(secondary_values)

            #determining main p_value
            #
            #at this point, secondary_value looks like:
            #    [[oppLCgap, oppLCgap_delta], [manLCgap, manLCgap_delta], [flow, flow_delta], ...
            #         0-0          0-1            1-0          1-1         2-0      2-1
            #
            #      forFMgap, forFMgap_KS_d, oppLCagap, oppLCagap_KS_d, oppLCbgap, oppLCbgap_KS_d, ...
            #         3            4              5          6              7          8
            #
            #      manLCagap, manLCagap_KS_d, manLCbgap, manLCbgap_KS_d, speeds, speeds_KS_d]
            #         9           10             11         12             13         14
            #

            fout = outputs.buildFout(config, secondary_values[4], secondary_values[8], secondary_values[12], None) #forward_gaps, oppLCbgaps, manLCbgaps
            d_stat.append([fout]+vissim_data.getConstraints())
            if config.output_forward_gaps:
                #if secondary_values[4] == 'DNE':
                #    d_stat.append(['inf'] + vissim_data.getConstraints())
                #else:
                #    d_stat.append([secondary_values[4]] + vissim_data.getConstraints())
                write.plot_dists(final_inpx_path, 'car-following gaps for ' + str(traj.split(os.sep)[-1].strip('.traj')), dist_video_data[0], dist_data[0], secondary_values[4], parameters[0], config.fps, seed_nums)

            if config.output_lane_change_gaps:
                #if secondary_values[8] == 'DNE':        #using the before gap to calibrate
                #    d_stat.append(['inf'] + vissim_data.getConstraints())
                #else:
                #    d_stat.append([secondary_values[8]] + vissim_data.getConstraints())
                if config.cmp_opp_lcgaps:
                    write.plot_dists(final_inpx_path, 'opportunistic lane change gaps for ' + str(traj.split(os.sep)[-1].strip('.traj')), dist_video_data[2], dist_data[2], secondary_values[8], parameters[0], config.fps, seed_nums)
                if config.cmp_man_lcgaps:
                    write.plot_dists(final_inpx_path, 'mandatory lane change gaps for ' + str(traj.split(os.sep)[-1].strip('.traj')), dist_video_data[4], dist_data[4], secondary_values[12], parameters[0], config.fps, seed_nums)

    return d_stat, network

def analyseCSVData(final_inpx_path, d_stat, network, N, vissim_data, config):

    fout_list = []
    secondary_values = []
    if config.output_travel_times:

        vissimNum_TTms = [TTms.info for TTms in vissim_data.travelTms]

        dirname = final_inpx_path.strip(final_inpx_path.split(os.sep)[-1])
        filename = [f for f in os.listdir(dirname) if f.endswith('.csv')][0]
        csv_TTms = csvParse.extractDataFromCSV(dirname, filename, 'Travel Times Data')

        for ttms in csv_TTms:
            vissim_time = vissim_data.travelTms[vissimNum_TTms.index(float(ttms.vissim_num))].cumul_all.mean
            csv_time = float(ttms.observedTT)

            fout_list.append(abs(csv_time - vissim_time)/csv_time*100)
            secondary_values.append([csv_time, vissim_time, abs(csv_time - vissim_time)/csv_time])

    fout = max(fout_list)

    network[N].addVideoComparison(secondary_values)

    d_stat.append([fout]+vissim_data.getConstraints())

    return d_stat, network

def runVissimForCalibrationAnalysis(network, inputs):
    '''
    '''

    #unpacking inputs
    config           = inputs[0]
    variables        = inputs[1]
    parameters       = inputs[2]
    point_folderpath = inputs[3]

    Vissim = vissim.startVissim()

    #retry the start vissim after having killed all vissims - only works if not in multi network mode
    if isinstance(Vissim, str):
        vissim.isVissimRunning(True)
        Vissim = vissim.startVissim()

    d_stat = []
    for N in xrange(len(network)):

        if len(network) > 1:
            #if we are treating more than one network, than we subdivide the point folder into network folders
            if not os.path.isdir(os.path.join(point_folderpath,os.path.splitext(network[N].inpx_path.split(os.sep)[-1])[0])):
                os.mkdir(os.path.join(point_folderpath,os.path.splitext(network[N].inpx_path.split(os.sep)[-1])[0]))

            final_inpx_path = os.path.join(point_folderpath,os.path.splitext(network[N].inpx_path.split(os.sep)[-1])[0])
            shutil.move(os.path.join(point_folderpath,network[N].inpx_path.split(os.sep)[-1]),os.path.join(final_inpx_path,network[N].inpx_path.split(os.sep)[-1]))

            #copy sqlite3.exe to the final_inpx_path
            shutil.copy(os.path.join(point_folderpath, 'sqlite3.exe'), os.path.join(final_inpx_path, 'sqlite3.exe'))

        else:
            final_inpx_path = copy.deepcopy(point_folderpath)

        #check for starting error
        if isinstance(Vissim, str):
            for traj in network[N].traj_paths:
                network[N].addVideoComparison(['StartError'])
                return False, network[N], ['N/A' for i in xrange(parameters[2])], 'Unfeasible'

        #load the network
        load = vissim.loadNetwork(Vissim, os.path.join(final_inpx_path,network[N].inpx_path.split(os.sep)[-1]), err_file_path=final_inpx_path)

        #check for network loading error
        if load is not True:
            for traj in network[N].traj_paths:
                network[N].addVideoComparison(['LoadNetError'])
                return False, network[N], ['N/A' for i in xrange(parameters[2])], 'Unfeasible'

        values = []
        for var in variables:
            values.append(var.point)

        #Initializing and running the simulation
        simulated = vissim.initializeSimulation(Vissim, parameters, values, variables, err_file_path=final_inpx_path, rsr=config.cmp_travel_times)

        if simulated is not True:
            for traj in network[N].traj_paths:
                network[N].addVideoComparison(['SimulationError'])
                vissim.stopVissim(Vissim)
            return False, network[N], ['N/A' for i in xrange(parameters[2])]

        else:
            #getting needed info from vissim
            VI = vissim.getVehicleInputs(Vissim, parameters[3])
            VI = [csvParse.create_class(vi, 'VehiclesInputs') for vi in VI]
            SH = vissim.getSignalHeads(Vissim)

            #treating the outputs
            vissim_data = outputs.Derived_data()
            vissim_data.activateConstraints(config)
            inputs = [final_inpx_path, False, network[N].corridors, vissim_data, config, VI, SH]
            file_list = [f for f in os.listdir(final_inpx_path) if f.endswith('fzp')]
            if len(file_list) > 1:
                packedStatsLists = workers.createWorkers(file_list, outputs.treatVissimOutputs, inputs, workers.FalseCommands(), defineNbrProcess = config.nbr_process)

                vissim_data = packedStatsLists[0]

                for stat in xrange(1,len(packedStatsLists)):
                    outputs.Derived_data.concat(vissim_data, packedStatsLists[stat])

            else:
                vissim_data = outputs.treatVissimOutputs(file_list, inputs)

            seed_nums = outputs.extract_num_from_fzp_list(file_list)

            if config.CALIBDATA_video:
                d_stat, network = analyseVideoData(final_inpx_path, seed_nums, d_stat, network, N, vissim_data, parameters, config)

            if config.CALIBDATA_in_csv:
                d_stat, network = analyseCSVData(final_inpx_path, d_stat, network, N, vissim_data, config)

            network[N].feasibility = vissim_data.testConstraints()

        #TODO: delete sqlite3.exe in the network folder...
        #os.remove(os.path.join(folderpath, 'sqlite3.exe'))

    #stop Vissim
    vissim.stopVissim(Vissim)

    #remove sqlite3.exe from the point folder
    if os.path.isfile(os.path.join(point_folderpath, 'sqlite3.exe')):
        os.remove(os.path.join(point_folderpath, 'sqlite3.exe'))

    #save data in a serialized file
    write.write_traj(point_folderpath, 'derived_data', [vissim_data, seed_nums, parameters])

    return d_stat, network, seed_nums

################################
#        Sensitivity Analisis
################################

def setCalculatingValues(default_values, current_name, nbr_points, current_range = [], default = False):
    '''Creates the working array to work with for the current iteration
       NB: current_range = [[min, max], pos]  | for default_values = True, current_range is not needed'''

    working_values = copy.deepcopy(default_values)
    if default is True:
        points_array = [default_values[0]]
    else:
        if current_name == 'CoopLnChg':
            points_array = current_range
        else:
            points_array = []
            if nbr_points > 1:
                for point in range(nbr_points):
                    points_array.append(current_range[0] + point * (current_range[1] - current_range[0]) /  (nbr_points - 1) )
            else:
                points_array.append((current_range[0] + current_range[1]) / 2)

    return working_values, points_array

def varDict(variable_names, default_values):
    '''creates a dictionary for faster search of variables'''

    var_dict = {}
    for i in range(len(variable_names)):
       var_dict[variable_names[i]] = [default_values[i], i]

    return var_dict

def correctingValues(default_values, current_value, current_name, var_dict):
    '''Checks if the value is in the following list and corrects the linked values accordingly'''

    message = []
    working_values = copy.deepcopy(default_values)
    if current_name == 'CoopLnChgSpeedDiff':
        working_values[var_dict['CoopLnChg'][1]] = True
    elif current_name == 'CoopLnChgCollTm':
        working_values[var_dict['CoopLnChg'][1]] = True
    elif current_name == 'LookAheadDistMin':
        if working_values[var_dict['LookAheadDistMax'][1]] < current_value:
            working_values[var_dict['LookAheadDistMax'][1]] = current_value + 0.1
            message.append('LookAheadDistMax was set to a value lower than the value set to LookAheadDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == 'LookAheadDistMax':
        if working_values[var_dict['LookAheadDistMin'][1]] > current_value:
            working_values[var_dict['LookAheadDistMin'][1]] = current_value - 0.1
            message.append('LookAheadDistMin was set to a value higher than the value set to LookAheadDistMax. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == 'LookBackDistMin':
        if working_values[var_dict['LookBackDistMax'][1]] < current_value:
            working_values[var_dict['LookBackDistMax'][1]] = current_value + 0.1
            message.append('LookBackDistMax was set to a value lower than the value set to LookBackDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == 'LookBackDistMax':
        if working_values[var_dict['LookBackDistMin'][1]] > current_value:
            working_values[var_dict['LookBackDistMin'][1]] = current_value - 0.1
            message.append('LookBackDistMin was set to a value higher than the value set to LookBackDistMax. To avoid a crash of Vissim, the value was adjusted')

    return working_values, message

def prepareFolderforVissimAnalysis(outputspath, folder_name, InpxName, InpxPath, default = False):
    '''creating a folder containing the files for that iteration'''
    if default is True:
        filename = 'Default_values.inpx'
        folder = 'Default_values'
    else:
        filename = folder_name + '.inpx'
        folder = folder_name

    folderpath = os.path.join(outputspath, folder)
    newfolderpath = write.createSubFolder(folderpath, folder)

    if newfolderpath is False:
        print 'Newfolderpath = False, must find a way to handle this issue'
        sys.exit()

    #renaming the inpx and moving it to the new folder
    if os.path.exists(os.path.join(folderpath, filename)) is False:
        shutil.copy(InpxPath, os.path.join(folderpath, InpxName))
        os.rename(os.path.join(folderpath, InpxName), os.path.join(folderpath, filename))

    return folderpath, filename

def monteCarlo_vissim(valuesVector, inputs):
    parameters     = inputs [0]
    InpxPath       = inputs [1]
    InpxName       = inputs [2]
    outputspath    = inputs [3]
    commands       = inputs [4]
    running        = inputs [5]
    sim_parameters = inputs [6]

    if commands.multi:
        all_values = inputs [7]
        #find the index of the first vector included in the chunk, and compares its position with lowerbound
        lowerbound = all_values.index(valuesVector[0])
    else:
        lowerbound = 0

    #preparing the output
    out_valuesVector = []

    #analysing the values
    for value in range(len(valuesVector)):
        #creating a folder containing the files for that iteration

        folderpath, filename = prepareFolderforVissimAnalysis(outputspath, 'Point_' + str(value+lowerbound), InpxName, InpxPath)

        if not commands.mode:  #this serves to bypass Vissim while testing the code

            #Starting a Vissim instance
            if running is False:
                Vissim = vissim.startVissim()
                running = True

            #loading the network
            loaded = vissim.loadNetwork(Vissim, os.path.join(folderpath, filename), err_file_path=folderpath)

            if loaded != 'LoadNetError':
                #Vissim initialisation and simulation running
                vissim.initializeSimulation(Vissim, sim_parameters, valuesVector[value], parameters, commands.save_swp, err_file_path=folderpath)

        out_valuesVector.append([valuesVector[value], folderpath, lowerbound])

    #closing Vissim
    if not commands.mode:
        closed = vissim.stopVissim(Vissim)
        if not closed:
            print 'Warning, vissim instance could not be closed, potential hold of a required vissim instance'

    return out_valuesVector

def monteCarlo_outputs(valuesVector, other_inputs):
    parameters     = other_inputs [0]
    sim_parameters = other_inputs [1]
    outputspath    = other_inputs [2]
    config         = other_inputs [3]
    commands       = other_inputs [4]
    corridors      = other_inputs [5]
    InpxName       = other_inputs [6]

    concat_variables = [parameters[i].vissim_name for i in xrange(len(parameters))]
    lowerbound = valuesVector[0][2]

    if commands.multi is True:
        #opening a process output file
        if not os.path.isdir(os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles')):
            os.makedirs(os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles'))
        WorkingPath = os.path.join(outputspath.strip(os.sep+'outputs'),'tempfiles')
        multiProcTempFile = outputspath.split(os.sep)[-2] + '_ProcTempFile_points_' + str(lowerbound) + '_to_' + str(len(valuesVector)+lowerbound)
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, 'Monte Carlo', config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName, None, multiProcTempFile)

    #preparing the outputs
    text = []

    for value in xrange(len(valuesVector)):
        if commands.mode:
            Outputs = outputs.generateRandomOutputs(sim_parameters, rand_seed_shake = value + lowerbound)
            success = True
        else:
            if os.path.isdir(valuesVector[value][1]):
                if [f for f in os.listdir(valuesVector[value][1]) if f.endswith('fzp')] != []:
                    #output treatment
                    inputs = [valuesVector[value][1], commands.verbose, corridors, outputs.Derived_data(), config]
                    Outputs = outputs.treatVissimOutputs([f for f in os.listdir(valuesVector[value][1]) if f.endswith('fzp')], inputs)
                    success = True
                else:
                    success = False
            else:
                success = False

        #writing to file
        if success == True:
            text.append([value+lowerbound, valuesVector[value][0],Outputs.flow.mean,Outputs.oppLCcount.mean,Outputs.manLCcount.mean,
                         Outputs.forFMgap.cumul_all.mean,  Outputs.forFMgap.cumul_all.firstQuart,  Outputs.forFMgap.cumul_all.median,  Outputs.forFMgap.cumul_all.thirdQuart,  Outputs.forFMgap.cumul_all.std,
                         Outputs.oppLCagap.cumul_all.mean, Outputs.oppLCagap.cumul_all.firstQuart, Outputs.oppLCagap.cumul_all.median, Outputs.oppLCagap.cumul_all.thirdQuart, Outputs.oppLCagap.cumul_all.std,
                         Outputs.oppLCbgap.cumul_all.mean, Outputs.oppLCbgap.cumul_all.firstQuart, Outputs.oppLCbgap.cumul_all.median, Outputs.oppLCbgap.cumul_all.thirdQuart, Outputs.oppLCbgap.cumul_all.std,
                         Outputs.manLCagap.cumul_all.mean, Outputs.manLCagap.cumul_all.firstQuart, Outputs.manLCagap.cumul_all.median, Outputs.manLCagap.cumul_all.thirdQuart, Outputs.manLCagap.cumul_all.std,
                         Outputs.manLCbgap.cumul_all.mean, Outputs.manLCbgap.cumul_all.firstQuart, Outputs.manLCbgap.cumul_all.median, Outputs.manLCbgap.cumul_all.thirdQuart, Outputs.manLCbgap.cumul_all.std,
                         Outputs.forSpeeds.cumul_all.mean, Outputs.forSpeeds.cumul_all.firstQuart, Outputs.forSpeeds.cumul_all.median, Outputs.forSpeeds.cumul_all.thirdQuart, Outputs.forSpeeds.cumul_all.std])

        else:
            #printing the exception in the csv file
            text.append([value+lowerbound, valuesVector[value][0],'No files found for this point. This error may be the result of an error while launching Vissim, while loading the Network or while running the simulation'])

    #security writing of chunk results while in multiprocessing
    if commands.multi is True:
        for i in range(len(text)):
            write.writeInFile(out, text[i])
        out.close()

    #dumping data into a traj file for futur retrival
    ##creating folder
    if not os.path.isdir(os.path.join(outputspath.strip(os.sep+'outputs'),'traj_files')):
        os.makedirs(os.path.join(outputspath.strip(os.sep+'outputs'),'traj_files'))

    ## naming file
    trajfilename = outputspath.strip(os.sep+'outputs').split(os.sep)[-1] + '_points_' + str(lowerbound) + '_to_' + str(len(valuesVector)+lowerbound)

    ##dumping serialised data
    with open(os.path.join(outputspath.strip(os.sep+'outputs'),'traj_files', trajfilename), 'wb') as output:
        pickle.dump(configure.Version(), output, protocol=2)
        pickle.dump(Outputs, output, protocol=2)

    return text

def createFirstRun_results(firstrun_results, variable):
    if variable.cumul_all.mean is not None:
        firstrun_results.append(float(variable.cumul_all.mean))
        firstrun_results.append(float(variable.cumul_all.firstQuart))
        firstrun_results.append(float(variable.cumul_all.median))
        firstrun_results.append(float(variable.cumul_all.thirdQuart))
        firstrun_results.append(float(variable.cumul_all.std))
    else:
        firstrun_results.append('---')
        firstrun_results.append('---')
        firstrun_results.append('---')
        firstrun_results.append('---')
        firstrun_results.append('---')
    return firstrun_results

def createDelta(firstrun_results, variable):
    if firstrun_results != '---' and variable is not None:
        return  (variable - firstrun_results)/firstrun_results
    else:
        return '---'

def OAT_sensitivity(values, inputs, default = False):
    '''Runs the sensitivity analysis for a set of predetermined values

       note: rangevalues = [range, position in the complete list]
    '''
    if isinstance(values[0], list) is False:
        values = [values]

    #unpacking inputs - should eventually be changed directly in the code
    all_values          = inputs [0]
    InpxPath            = inputs [1]
    InpxName            = inputs [2]
    outputspath         = inputs [3]
    graphspath          = inputs [4]
    config              = inputs [5]
    commands            = inputs [6]
    running             = inputs [7]
    sim_parameters      = inputs [8]
    verbose             = inputs [9]
    corridors           = inputs [10]
    if default is False:
        firstrun_results = inputs[11]

    default_values =  [all_values[i].vissim_default for i in xrange(len(all_values))]
    concat_variables = [all_values[i].vissim_name for i in xrange(len(all_values))]
    parameters = [all_values[i] for i in xrange(len(all_values))]
    all_names = [all_values[i].name for i in xrange(len(all_values))]

    #preparing the outputs
    text = []

    if commands.multi is True and default is False:
        #opening a process output file
        WorkingPath = outputspath.strip(os.sep+'outputs')
        multiProcTempFile = outputspath.split(os.sep)[-2] + '_ProcTempFile_' + values[0][0].name
        out, subdirname = write.writeHeader(WorkingPath, concat_variables, 'Sensitivity', config.first_seed, config.nbr_runs, config.warm_up_time, config.simulation_time, InpxName, default_values, multiProcTempFile)

    #creating a dictionnary
    var_dict = varDict(concat_variables, default_values)

    #treating the values given in rangevalues
    for value in xrange(len(values)):

        #defining the variable being worked on and the range of values it can take
        if default is True:
            current_range = []
            value_name = 'Default'
            position = 0
        else:
            current_range = [values[value][0].desired_min,values[value][0].desired_max]
            value_name = values[value][0].name
            position = all_names.index(value_name)

        #defining the values needed for the current cycle
        working_values, points_array = setCalculatingValues(default_values, value_name, config.nbr_points, current_range, default)

        #iterating on the number points
        for point in points_array:
            iteration_values = copy.deepcopy(working_values)
            iteration_values[position] = point

            #correcting the value array for variables that need to interact with others
            corrected_values, message = correctingValues(iteration_values, point, value_name, var_dict)

            if message != []:
                print'*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'
                print message
                print' occured for variable ' + str(value_name) + ' = ' + str(point)
                print'*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'

            #creating a folder containing the files for that iteration
            folderpath, filename = prepareFolderforVissimAnalysis(outputspath, value_name + '_' + str(round(point,3)), InpxName, InpxPath, default)

            #Starting a Vissim instance
            if commands.mode:  #this serves to bypass Vissim while testing the code
                if default is False:
                    rand_seed_shake = 100*points_array.index(point)+value
                else:
                    rand_seed_shake = 0
                Outputs = outputs.generateRandomOutputs(sim_parameters, rand_seed_shake)

            else:
                #Vissim starting and loading network block
                if running is False: Vissim = vissim.startVissim()
                if Vissim == 'StartError':
                    if default is True:
                        print 'Could not start Vissim for default values, shutting down the analysis'
                        sys.exit()
                    else:
                        text.append([value_name, corrected_values,'Could not start Vissim'])
                        continue

                else:
                    loaded = vissim.loadNetwork(Vissim, os.path.join(folderpath, filename), err_file_path=folderpath)

                    if loaded == 'LoadNetError':
                        if default is True:
                            print 'Could not load the Network for default values, shutting down the analysis'
                            sys.exit()
                        else:
                            text.append([value_name, corrected_values,'Could not load the Network'])
                            continue

                    else:
                        #preventing a new loading of Vissim for that iteration
                        running = True

                        #Vissim initialisation and simulation running
                        simulated = vissim.initializeSimulation(Vissim, sim_parameters, corrected_values, parameters, commands.save_swp,err_file_path=folderpath)

                        if simulated is not True:
                            text.append([value_name, corrected_values,''.join(str(simulated))])    #printing the exception in the csv file
                            if default is True: firstrun_results = []
                            continue
                        else:
                            #output treatment
                            inputs = [folderpath, verbose, corridors, outputs.Derived_data(), config]
                            Outputs = outputs.treatVissimOutputs([f for f in os.listdir(folderpath) if f.endswith('fzp')], inputs)
                            #print '*** Output treatment completed *** Runtime: ' + str(time.clock())


            if default is True:
                firstrun_results = []
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.forFMgap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.oppLCagap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.oppLCbgap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.manLCagap)
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.manLCbgap)
                firstrun_results.append(float(Outputs.flow.mean))
                firstrun_results.append(float(Outputs.oppLCcount.mean))
                firstrun_results.append(float(Outputs.manLCcount.mean))
                firstrun_results = createFirstRun_results(firstrun_results, Outputs.forSpeeds)

            else:
                delta_mean_fgap           = createDelta(firstrun_results[0], Outputs.forFMgap.cumul_all.mean)
                delta_firstQuart_fgap     = createDelta(firstrun_results[1], Outputs.forFMgap.cumul_all.firstQuart)
                delta_median_fgaps        = createDelta(firstrun_results[2], Outputs.forFMgap.cumul_all.median)
                delta_thirdQuart_fgaps    = createDelta(firstrun_results[3], Outputs.forFMgap.cumul_all.thirdQuart)
                delta_std_fgaps           = createDelta(firstrun_results[4], Outputs.forFMgap.cumul_all.std)

                delta_mean_Aoppgap        = createDelta(firstrun_results[5], Outputs.oppLCagap.cumul_all.mean)
                delta_firstQuart_Aoppgap  = createDelta(firstrun_results[6], Outputs.oppLCagap.cumul_all.firstQuart)
                delta_median_Aoppgap      = createDelta(firstrun_results[7], Outputs.oppLCagap.cumul_all.median)
                delta_thirdQuart_Aoppgap  = createDelta(firstrun_results[8], Outputs.oppLCagap.cumul_all.thirdQuart)
                delta_std_Aoppgap         = createDelta(firstrun_results[9], Outputs.oppLCagap.cumul_all.std)

                delta_mean_Boppgap        = createDelta(firstrun_results[10], Outputs.oppLCbgap.cumul_all.mean)
                delta_firstQuart_Boppgap  = createDelta(firstrun_results[11], Outputs.oppLCbgap.cumul_all.firstQuart)
                delta_median_Boppgap      = createDelta(firstrun_results[12], Outputs.oppLCbgap.cumul_all.median)
                delta_thirdQuart_Boppgap  = createDelta(firstrun_results[13], Outputs.oppLCbgap.cumul_all.thirdQuart)
                delta_std_Boppgap         = createDelta(firstrun_results[14], Outputs.oppLCbgap.cumul_all.std)

                delta_mean_Amangap        = createDelta(firstrun_results[15], Outputs.manLCagap.cumul_all.mean)
                delta_firstQuart_Amangap  = createDelta(firstrun_results[16], Outputs.manLCagap.cumul_all.firstQuart)
                delta_median_Amangap      = createDelta(firstrun_results[17], Outputs.manLCagap.cumul_all.median)
                delta_thirdQuart_Amangap  = createDelta(firstrun_results[18], Outputs.manLCagap.cumul_all.thirdQuart)
                delta_std_Amangap         = createDelta(firstrun_results[19], Outputs.manLCagap.cumul_all.std)

                delta_mean_Bmangap        = createDelta(firstrun_results[20], Outputs.manLCbgap.cumul_all.mean)
                delta_firstQuart_Bmangap  = createDelta(firstrun_results[21], Outputs.manLCbgap.cumul_all.firstQuart)
                delta_median_Bmangap      = createDelta(firstrun_results[22], Outputs.manLCbgap.cumul_all.median)
                delta_thirdQuart_Bmangap  = createDelta(firstrun_results[23], Outputs.manLCbgap.cumul_all.thirdQuart)
                delta_std_Bmangap         = createDelta(firstrun_results[24], Outputs.manLCbgap.cumul_all.std)

                if firstrun_results[25] != 0:
                    delta_flow = (Outputs.flow.mean - firstrun_results[25])/firstrun_results[25]
                else:
                    delta_flow = '---'

                if firstrun_results[26] != 0:
                    delta_oppLCcount = (Outputs.oppLCcount.mean - firstrun_results[26])/firstrun_results[26]
                else:
                    delta_oppLCcount = '---'

                if firstrun_results[27] != 0:
                    delta_manLCcount = (Outputs.manLCcount.mean - firstrun_results[27])/firstrun_results[27]
                else:
                    delta_manLCcount = '---'

                delta_mean_Speeds         = createDelta(firstrun_results[28], Outputs.forSpeeds.cumul_all.mean)
                delta_firstQuart_Speeds   = createDelta(firstrun_results[29], Outputs.forSpeeds.cumul_all.firstQuart)
                delta_median_Speeds       = createDelta(firstrun_results[30], Outputs.forSpeeds.cumul_all.median)
                delta_thirdQuart_Speeds   = createDelta(firstrun_results[31], Outputs.forSpeeds.cumul_all.thirdQuart)
                delta_std_Speeds          = createDelta(firstrun_results[32], Outputs.forSpeeds.cumul_all.std)

            #printing graphs
            if commands.vis_save:
                variables = [Outputs.forFMgap,Outputs.oppLCagap,Outputs.oppLCbgap,Outputs.manLCagap,Outputs.manLCbgap]
                variables_name = ['Forward_gaps','Opportunistic_lane_change_after_gaps','Opportunistic_lane_change_before_gaps','Mandatory_lane_change_after_gaps','Mandatory_lane_change_before_gaps']
                for var in xrange(len(variables)):
                    if default is True:
                        name = 'Default_values'
                        subpath = 'Default_values'
                    else:
                        name = filename.strip('.inpx')
                        subpath = value_name[:]

                    write.printStatGraphs(graphspath,variables[var], name, variables_name[var], commands.fig_format, config.nbr_runs, subpath)

            #writing to file
            if default is True:
                text.append(['Default_values', corrected_values, Outputs.flow.mean, '---',  Outputs.oppLCcount.mean, '---', Outputs.manLCcount.mean, '---',
                             Outputs.forFMgap.cumul_all.mean,  '---', Outputs.forFMgap.cumul_all.firstQuart,  '---', Outputs.forFMgap.cumul_all.median,  '---', Outputs.forFMgap.cumul_all.thirdQuart,  '---', Outputs.forFMgap.cumul_all.std,  '---',
                             Outputs.oppLCagap.cumul_all.mean, '---', Outputs.oppLCagap.cumul_all.firstQuart, '---', Outputs.oppLCagap.cumul_all.median, '---', Outputs.oppLCagap.cumul_all.thirdQuart, '---', Outputs.oppLCagap.cumul_all.std, '---',
                             Outputs.oppLCbgap.cumul_all.mean, '---', Outputs.oppLCbgap.cumul_all.firstQuart, '---', Outputs.oppLCbgap.cumul_all.median, '---', Outputs.oppLCbgap.cumul_all.thirdQuart, '---', Outputs.oppLCbgap.cumul_all.std, '---',
                             Outputs.manLCagap.cumul_all.mean, '---', Outputs.manLCagap.cumul_all.firstQuart, '---', Outputs.manLCagap.cumul_all.median, '---', Outputs.manLCagap.cumul_all.thirdQuart, '---', Outputs.manLCagap.cumul_all.std, '---',
                             Outputs.manLCbgap.cumul_all.mean, '---', Outputs.manLCbgap.cumul_all.firstQuart, '---', Outputs.manLCbgap.cumul_all.median, '---', Outputs.manLCbgap.cumul_all.thirdQuart, '---', Outputs.manLCbgap.cumul_all.std, '---',
                             Outputs.forSpeeds.cumul_all.mean, '---', Outputs.forSpeeds.cumul_all.firstQuart, '---', Outputs.forSpeeds.cumul_all.median, '---', Outputs.forSpeeds.cumul_all.thirdQuart, '---', Outputs.forSpeeds.cumul_all.std, '---'])

            else:
                text.append([value_name, corrected_values, Outputs.flow.mean, delta_flow, Outputs.oppLCcount.mean, delta_oppLCcount, Outputs.manLCcount.mean, delta_manLCcount,
                             Outputs.forFMgap.cumul_all.mean,  delta_mean_fgap,    Outputs.forFMgap.cumul_all.firstQuart,  delta_firstQuart_fgap,    Outputs.forFMgap.cumul_all.median,  delta_median_fgaps,   Outputs.forFMgap.cumul_all.thirdQuart,  delta_thirdQuart_fgaps,   Outputs.forFMgap.cumul_all.std,  delta_std_fgaps,
                             Outputs.oppLCagap.cumul_all.mean, delta_mean_Aoppgap, Outputs.oppLCagap.cumul_all.firstQuart, delta_firstQuart_Aoppgap, Outputs.oppLCagap.cumul_all.median, delta_median_Aoppgap, Outputs.oppLCagap.cumul_all.thirdQuart, delta_thirdQuart_Aoppgap, Outputs.oppLCagap.cumul_all.std, delta_std_Aoppgap,
                             Outputs.oppLCbgap.cumul_all.mean, delta_mean_Boppgap, Outputs.oppLCbgap.cumul_all.firstQuart, delta_firstQuart_Boppgap, Outputs.oppLCbgap.cumul_all.median, delta_median_Boppgap, Outputs.oppLCbgap.cumul_all.thirdQuart, delta_thirdQuart_Boppgap, Outputs.oppLCbgap.cumul_all.std, delta_std_Boppgap,
                             Outputs.manLCagap.cumul_all.mean, delta_mean_Amangap, Outputs.manLCagap.cumul_all.firstQuart, delta_firstQuart_Amangap, Outputs.manLCagap.cumul_all.median, delta_median_Amangap, Outputs.manLCagap.cumul_all.thirdQuart, delta_thirdQuart_Amangap, Outputs.manLCagap.cumul_all.std, delta_std_Amangap,
                             Outputs.manLCbgap.cumul_all.mean, delta_mean_Bmangap, Outputs.manLCbgap.cumul_all.firstQuart, delta_firstQuart_Bmangap, Outputs.manLCbgap.cumul_all.median, delta_median_Bmangap, Outputs.manLCbgap.cumul_all.thirdQuart, delta_thirdQuart_Bmangap, Outputs.manLCbgap.cumul_all.std, delta_std_Bmangap,
                             Outputs.forSpeeds.cumul_all.mean, delta_mean_Speeds,  Outputs.forSpeeds.cumul_all.firstQuart, delta_firstQuart_Speeds,  Outputs.forSpeeds.cumul_all.median, delta_median_Speeds,  Outputs.forSpeeds.cumul_all.thirdQuart, delta_thirdQuart_Speeds,  Outputs.forSpeeds.cumul_all.std, delta_std_Speeds])

        #breaking the outer loop because the default only needs to be ran once
        if default is True:
            break

    if not commands.mode:
        closed = vissim.stopVissim(Vissim)
        if not closed:
            print 'Warning, vissim instance could not be closed, potential hold of a required vissim instance'

    #security writing of chunk results while in multiprocessing
    if commands.multi is True and default is False:
        for i in range(len(text)):
            write.writeInFile(out, text[i])
        out.close()

    if default is True:
        return text, firstrun_results
    else:
        return text