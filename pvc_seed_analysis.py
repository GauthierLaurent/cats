# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:59:41 2015

@author: Laurent

call ex: -a Trace --dir C:\Users\lab\Desktop\vissim_files\A13\Combined_06_10_11_12\Seed_test_Analysis_1
"""
def commands(parser):
    parser.add_argument('-p',    type=float, nargs='*',                             dest='start_point', default = None,   help='list of float (integers will be converted) | make sure the number of floats entered correspond to the number of variables to be analysed')
    parser.add_argument('--dir',                                                    dest='dir',         default='',       help='Directory (Must be provided if Calc or Trace mode are activated)')
    parser.add_argument('-a',    choices = ['Sim', 'Calc', 'Conf', 'Trace', 'All'], dest='analysis',    default='All',    help='"Sim" only runs relevant siulations, "Calc" calculates data in the fzp files, "Trace" produces the graphics, "All" runs all of modes one after the others')
    parser.add_argument('-t',    action='store_true',                               dest='trace_conf',  default=False,    help='Trace option, enables the ploting of confidence intervals (requires the intervals to be computed first)')
    parser.add_argument('-r',                                                       dest='nbr_runs',    default=100  ,    help='Number of simulations to perform. Default = 100')
    parser.add_argument('-l',    choices = ['french', 'english'],                   dest='language',    default='french', help='Choose the language displayed in the graphics. Default = french')
    return parser.parse_args()

def main():
    import os, argparse, shutil, random, copy, sys
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.stats import t

    import pvc_mathTools  as mathTools
    import pvc_calibTools as calibTools
    import pvc_csvParse   as csvParse
    import pvc_configure  as configure
    import pvc_write      as write
    import pvc_vissim     as vissim
    import pvc_outputs    as outputs

    ################################
    #        Load settings
    ################################
    Commands = commands(argparse.ArgumentParser())
    config   = configure.Config('calib.cfg')

    ######################################
    #        Simulations
    ######################################
    if Commands.analysis == 'Sim' or Commands.analysis == 'All':
        #Checking if Vissim is already running and closing it to avoid problems latter on
        running = vissim.isVissimRunning(kill=True)
        if running is not False:
            print 'Could not close Vissim, the program may potentially have problems with the COM interface'

        ##Vissim simulation parameters
        Sim_lenght = config.simulation_time + config.warm_up_time
        sim_cores = 10

        if config.random_seed is False:
            first_seed = config.first_seed
            increments = config.increments
        else:
            first_seed = random.randint(1,700)
            increments = random.randint(1,10)
        parameters = [config.sim_steps, first_seed, Commands.nbr_runs, Sim_lenght, sim_cores, increments]

        err = 0.2

        #determining vissim, video, and corridor lists
        networks = calibTools.Network.buildNetworkObjects(config)

        if len(networks) > 1:
            multi_networks = True
        else:
            multi_networks = False

        #generating the raw variables contained in the csv
        variables = csvParse.extractParamFromCSV(config.path_to_csv, config.inpx_name.strip('inpx') + 'csv')

        ##looking for an input testing point
        if Commands.start_point is not None:
            test_point = Commands.start_point

            #checking for compatibility with the number of parameter specified
            if len(test_point) == len([i for i in variables if i.include is True]):
                for p in xrange(len(test_point)):
                    test_point[p] = float(test_point[p])
            else:
                print ('Lenght of starting point does not match the number of variables to be be processed...\n'
                       'Number of variables to process: ' + str(len([i for i in variables if i.include is True])) + '\n'
                       'Lenght of starting point given: ' + str(len(test_point)) + '\n'
                       'Aborting current evaluation\n'
                       'Please correct starting point vector')
                return
        else:
            test_point = []

        #creating an output folder for that analysis
        if not os.path.isdir(config.path_to_output_folder):
            os.makedirs(config.path_to_output_folder)

        filename, last_num =  write.defineName(config.path_to_output_folder, 'Seed_test')
        working_path = os.path.join(config.path_to_output_folder, filename)
        os.makedirs(working_path)

        #simulations
        for net in networks:

            #moving required inpx file to the test location
            if multi_networks is True:
                os.makedirs(os.path.join(working_path, net.inpx_path.split(os.sep)[-1].strip('.inpx')))
                shutil.copy(net.inpx_path, os.path.join(working_path, net.inpx_path.split(os.sep)[-1].strip('.inpx'), net.inpx_path.split(os.sep)[-1]))
                final_path = os.path.join(working_path, net.inpx_path.split(os.sep)[-1].strip('.inpx'))

            else:
                shutil.copy(net.inpx_path, os.path.join(working_path, net.inpx_path.split(os.sep)[-1]))
                final_path = copy.deepcopy(working_path)

            #running the simulations
            Vissim = vissim.startVissim()

            #retry the start vissim after having killed all vissims - only works if not in multi network mode
            if isinstance(Vissim, str) and multi_networks is False:
                vissim.isVissimRunning(True)
                Vissim = vissim.startVissim()

            #check for starting error
            if isinstance(Vissim, str):
                print 'Start Error'
                return

            #load the network
            load = vissim.loadNetwork(Vissim, os.path.join(final_path,net.inpx_path.split(os.sep)[-1]), err_file=True)

            #check for network loading error
            if load is not True:
                print 'LoadNet Error'
                return

            if test_point == []:
                values = []
                for var in variables:
                    values.append(var.vissim_default)
            else:
                values = copy.deepcopy(test_point)

            #Initializing and running the simulation
            first_seed = parameters[1]                  #saving info for later use
            increment = parameters[5]                   #saving info for later use
            run_per_itt = 20                            #vissim is blocked at 20 sim... gah
            parameters[2] = 20                          #setting the number of simulations to run at 20... THANKS VISSIM
            total_run = Commands.nbr_runs               #total number of simulations to perform
            nbr_init = total_run / run_per_itt          #total number of initialization

            #correction for modulo 20 > 0
            if total_run % run_per_itt > 0:
                nbr_init += 1

            for i in xrange(nbr_init):

                #on the first itteration of 20+ run, the parameter information is already ok
                if i == 0 and nbr_init > 1:
                    pass    #doing nothing

                else:
                    #if there are any left overs (number of runs is not a multiple of 20)
                    if total_run % run_per_itt > 0 and i == nbr_init - 1:
                        parameters[1] = first_seed + i*run_per_itt*increment
                        parameters[2] = total_run % run_per_itt

                    #normal and complete "after first itteration" pass
                    else:
                        parameters[1] = first_seed + i*run_per_itt*increment


                simulated = vissim.initializeSimulation(Vissim, parameters, values, variables, err_file_path=final_path)

                if simulated is not True:
                    print 'InitializeSimulation Error'
                    return

            vissim.stopVissim(Vissim)

        write.write_traj(working_path, 'seedAnalysis', [1, config, first_seed, increments, networks])

    ######################################
    #        Calculations
    ######################################
    if Commands.analysis == 'Calc' or Commands.analysis == 'All':

        #initializing data variables
        single_fzp_data = calibTools.ResultList()
        concat_fzp_data = calibTools.ResultList()
        concat_stu_data = calibTools.ResultList()
        dataList = []

        if Commands.analysis == 'Calc':
            if Commands.dir == '':
                print 'Directory containing .fzp file must be provided'
                sys.exit()
            else:
                working_path = Commands.dir

            if 'seedAnalysis.traj' not in os.listdir(working_path):
                print 'No seedAnalysis.traj file found in the provided directory'
                sys.exit()
            else:
                first_step_outputs = write.load_traj(os.path.join(working_path,'seedAnalysis.traj'))
                config     = first_step_outputs[1]
                first_seed = first_step_outputs[2]
                increments = first_step_outputs[3]
                networks   = first_step_outputs[4]
                otherStuff = first_step_outputs[5:]

        for net in networks:
            #looking for version errors in the traj files
            for traj in net.traj_paths:
                video_data_list = write.load_traj(traj)
                if video_data_list == 'TrajVersionError':
                    print 'traj file ' +str(traj.split(os.sep)[-1]) + 'yielded incorect version number'
                    running = vissim.isVissimRunning(True)
                    return

            if len(networks) > 1:
                final_path = os.path.join(working_path, net.inpx_path.split(os.sep)[-1].strip('.inpx'))
            else:
                final_path = copy.deepcopy(working_path)

            #generate output (empty)
            data = outputs.Derived_data()

            #gather file list
            file_list = [f for f in os.listdir(final_path) if f.endswith('fzp')]
            file_list.sort()

            #treatment loop
            for files in file_list:

                inputs = [final_path, True, net.corridors, data, config]
                data = outputs.treat_Single_VissimOutput(files, inputs)

                #student on concat data
                #if config.output_forward_gaps:
                #    t_student = t.ppf(0.975, len(data.forFMgap.cumul_all.raw) -1)
                #    N = ( t_student * data.forFMgap.cumul_all.std / (err * data.forFMgap.cumul_all.mean) )**2

                #if config.output_lane_change_gaps:
                #    t_student = t.ppf(0.975, len(data.oppLCbgap.cumul_all.raw) -1)
                #    N = ( t_student * data.oppLCbgap.cumul_all.std / (err * data.oppLCbgap.cumul_all.mean) )**2

                #concat_stu_data.addResult('Concat Student', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, N)

                #setting video values
                for traj in net.traj_paths:

                    #loading video data
                    vdata = write.load_traj(traj)

                    #treat last data
                    if config.output_forward_gaps:
                        vissim_data = data.forFMgap.distributions[-1].raw
                        video_data = outputs.makeitclean(vdata.forFMgap.distributions[-1].raw, 0.5*config.fps)

                        d_stat_1 = calibTools.checkCorrespondanceOfTwoLists(video_data, vissim_data, config.sim_steps, config.fps)
                        single_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_tiv', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, d_stat_1)
                    else:
                        d_stat_1 = None

                    if config.output_lane_change_gaps:
                        if config.cmp_opp_lcgaps:
                            vissim_data = data.oppLCbgap.distributions[-1].raw
                            video_data = vdata.oppLCbgap.distributions[-1].raw

                            d_stat_2 = calibTools.checkCorrespondanceOfTwoLists(video_data, vissim_data, config.sim_steps, config.fps)
                            single_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_opp', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, d_stat_2)
                        else:
                            d_stat_2 = None

                        if config.cmp_man_lcgaps:
                            vissim_data = data.oppLCbgap.distributions[-1].raw
                            video_data = vdata.oppLCbgap.distributions[-1].raw

                            d_stat_3 = calibTools.checkCorrespondanceOfTwoLists(video_data, vissim_data, config.sim_steps, config.fps)
                            single_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_man', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, d_stat_3)
                        else:
                            d_stat_3 = None
                    else:
                        d_stat_2 = None
                        d_stat_3 = None

                    fout = outputs.buildFout(config, d_stat_1, d_stat_2, d_stat_3)
                    single_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_fout', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, fout)

                    #treat concat data
                    if config.output_forward_gaps:
                        vissim_data = data.forFMgap.cumul_all.raw
                        video_data = outputs.makeitclean(vdata.forFMgap.cumul_all.raw, 0.5*config.fps)

                        d_stat_1 = calibTools.checkCorrespondanceOfTwoLists(video_data, vissim_data, config.sim_steps, config.fps)
                        concat_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_tiv', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, d_stat_1)

                    if config.output_lane_change_gaps:
                        if config.cmp_opp_lcgaps:
                            vissim_data = data.oppLCbgap.cumul_all.raw
                            video_data = vdata.oppLCbgap.cumul_all.raw

                            d_stat_2 = calibTools.checkCorrespondanceOfTwoLists(video_data, vissim_data, config.sim_steps, config.fps)
                            single_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_opp', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, d_stat_2)
                        else:
                            d_stat_2 = None

                        if config.cmp_man_lcgaps:
                            vissim_data = data.manLCbgap.cumul_all.raw
                            video_data = vdata.manLCbgap.cumul_all.raw

                            d_stat_3 = calibTools.checkCorrespondanceOfTwoLists(video_data, vissim_data, config.sim_steps, config.fps)
                            single_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_man', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, d_stat_3)
                        else:
                            d_stat_3 = None
                    else:
                        d_stat_2 = None
                        d_stat_3 = None

                    fout = outputs.buildFout(config, d_stat_1, d_stat_2, d_stat_3)
                    concat_fzp_data.addResult(traj.split(os.sep)[-1].strip('.traj')+'_fout', net.inpx_path.split(os.sep)[-1].strip('.inpx'), file_list.index(files) + 1, fout)

            dataList.append(data)

        write.write_traj(working_path, 'seedAnalysis', [2, config, first_seed, increments, networks, single_fzp_data, concat_fzp_data, concat_stu_data, dataList]+otherStuff)

    ######################################
    #        Confidence
    ######################################
    if Commands.analysis == 'Conf' or Commands.analysis == 'All':

        #loading data
        if Commands.analysis == 'Conf':
            if Commands.dir == '':
                print 'Directory containing seedAnalysis.traj file must be provided'
                sys.exit()
            else:
                working_path = Commands.dir

            if 'seedAnalysis.traj' not in os.listdir(working_path):
                print 'No seedAnalysis.traj file found in the provided directory'
                sys.exit()
            else:
                outputs = write.load_traj(os.path.join(working_path,'seedAnalysis.traj'))

                if outputs[0] < 2:
                    print 'You must first run the calculation phase'
                    sys.exit()

                config     = outputs[1]
                first_seed = outputs[2]
                increments = outputs[3]
                networks   = outputs[4]
                single_fzp_data = outputs[5]
                concat_fzp_data = outputs[6]
                concat_stu_data = outputs[7]
                dataList = outputs[8]

        lower_confidence = calibTools.ResultList()
        upper_confidence = calibTools.ResultList()

        for net in networks:

            print 'calculating network '+str(networks.index(net)+1)+' of '+str(len(networks))
            for traj in net.traj_paths:

                print 'calculating confidence d-stats for video '+str(net.traj_paths.index(traj)+1)+' of '+str(len(net.traj_paths))+' for network '+str(networks.index(net)+1)

                #getting vissim data
                vissim_data = dataList[networks.index(net)]

                #loading video data
                vdata = write.load_traj(traj)
                calibTools.calculateConfidenceLine(lower_confidence,upper_confidence,traj.split(os.sep)[-1].strip('.traj'), net.inpx_path.split(os.sep)[-1].strip('.inpx'),len(single_fzp_data.results[0].x),vissim_data,vdata,config)

        write.write_traj(working_path, 'seedAnalysis', [3, config, first_seed, increments, networks, single_fzp_data, concat_fzp_data, concat_stu_data, dataList, lower_confidence, upper_confidence])

    ######################################
    #        Trace
    ######################################
    if Commands.analysis == 'Trace' or Commands.analysis == 'All':

        #loading data
        if Commands.analysis == 'Trace':
            if Commands.dir == '':
                print 'Directory containing seedAnalysis.traj file must be provided'
                sys.exit()
            else:
                working_path = Commands.dir

            if 'seedAnalysis.traj' not in os.listdir(working_path):
                print 'No seedAnalysis.traj file found in the provided directory'
                sys.exit()
            else:
                outputs = write.load_traj(os.path.join(working_path,'seedAnalysis.traj'))

                if outputs[0] < 2:
                    print 'You must first run the calculation phase'
                    sys.exit()

                else:
                    config          = outputs[1]
                    first_seed      = outputs[2]
                    increments      = outputs[3]
                    single_fzp_data = outputs[5]
                    concat_fzp_data = outputs[6]
                    concat_stu_data = outputs[7]
                    data            = outputs[8]

                    if Commands.trace_conf is True:
                        if outputs[0] < 3:
                            print 'You must first run theconfidence calculation phase'
                            sys.exit()
                        else:
                            lower_confidence = outputs[9]
                            upper_confidence = outputs[10]

        from matplotlib.font_manager import FontProperties

        fontP = FontProperties()
        fontP.set_size('small')

        linestyles = ['-', '--', '-.', ':']
        colors = ['r','b','g','k']

        nets = list(set(single_fzp_data.GetNetLabels()))

        fig = plt.figure()

        #that's only to have the axis label shared by both subplot...
        ax4 = fig.add_subplot(1,1,1)
        if Commands.language == 'french':
            ax4.set_ylabel('valeur d (test de K-S)')
        if Commands.language == 'english':
            ax4.set_ylabel('d statistic (K-S test)')
        ax4.set_xticklabels('', visible=False)
        ax4.set_yticklabels('', visible=False)
        box = ax4.get_position()
        ax4.set_position([box.x0-box.width*0.05, box.y0 + box.height * 0.15, box.width, box.height * 0.8])

        ax4.xaxis.set_ticks([])
        ax4.yaxis.set_ticks([])
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)
        ax4.spines['bottom'].set_visible(False)
        ax4.spines['left'].set_visible(False)

        #subplot1: single data figure
        ax1 = fig.add_subplot(2,1,2)
        #for each network
        current_ymax = 0
        current_ymin = 1.0

        #getting the infos for that network
        single_data = single_fzp_data.GetResultForNetLabel(nets[3], nets[3]+'_fout')
        concat_data = concat_fzp_data.GetResultForNetLabel(nets[3], nets[3]+'_fout')

        if Commands.trace_conf is True:
            lConf = lower_confidence.GetResultForNetLabel(nets[3], nets[3]+'_fout')
            uConf = upper_confidence.GetResultForNetLabel(nets[3], nets[3]+'_fout')

        #we assign a color per network
        color = colors[0]

        #for j in xrange(len(single_data)):
            #if j > 0: break
        j = 0
        if Commands.language == 'french':
            plt.scatter(single_data[j].x, single_data[j].y, color = color, label = u'Valeur pour le vidéo '+str(write.defineLabel(single_data[j].label,'A13')), linestyle = linestyles[j])
        if Commands.language == 'english':
            plt.scatter(single_data[j].x, single_data[j].y, color = color, label = 'Single data point for video '+str(write.defineLabel(single_data[j].label,'A13')), linestyle = linestyles[j])
        if max(single_data[j].y) > current_ymax:
            current_ymax = max(single_data[j].y)
        if min(single_data[j].y) < current_ymin:
            current_ymin = min(single_data[j].y)

        #for k in xrange(len(concat_data)):
            #if k > 0: break
        k = 0
        if Commands.language == 'french':
            plt.plot(concat_data[k].x, concat_data[k].y, color = color, label = u'Données concaténées pour le vidéo '+str(write.defineLabel(concat_data[k].label,'A13')), linestyle = linestyles[k])
        if Commands.language == 'english':
            plt.plot(concat_data[k].x, concat_data[k].y, color = color, label = 'Concatenated data for video '+str(write.defineLabel(concat_data[k].label,'A13')), linestyle = linestyles[k])
        if max(concat_data[k].y) > current_ymax:
            current_ymax = max(concat_data[k].y)
        if min(concat_data[k].y) < current_ymin:
            current_ymin = min(concat_data[k].y)

        if Commands.trace_conf is True:
            plt.plot(lConf[k].x, lConf[k].y, color = 'k', linestyle = '--')
            plt.plot(uConf[k].x, uConf[k].y, color = 'k', linestyle = '--')

        new_ymax = mathTools.myceil(current_ymax,base=0.01,outType=float)-0.01
        new_ymin = mathTools.myfloor(current_ymin,base=0.01,outType=float)-0.01

        ax1.set_ylim(ymin = new_ymin, ymax = new_ymax)
        ax1.set_xlim(xmin = 0, xmax = 50)#max(data_line.x)+1,5))
        ax1.set_yticks(np.arange(new_ymin,new_ymax+0.001,0.01))
        ax1.set_xticks(np.arange(0,51,5))#max(data_line.x)+1,5))
        #ax1.set_ylabel('d statistic (K-S test)')
        if Commands.language == 'french':
            ax1.set_xlabel(u'Réplications')
        if Commands.language == 'english':
            ax1.set_xlabel('Replications')
        ax1.minorticks_on
        ax1.grid(True, which='both')

        box = ax1.get_position()
        ax1.set_position([box.x0+box.width*0.03, box.y0 + box.height * 0.25, box.width, box.height * 1.0])


        ###########################
        ax2 = fig.add_subplot(2,1,1)
        #for each network
        current_ymax = 0
        current_ymin = 1.0

        #getting the infos for that network
        single_data = single_fzp_data.GetResultForNetLabel(nets[2], nets[2]+'_fout')
        concat_data = concat_fzp_data.GetResultForNetLabel(nets[2], nets[2]+'_fout')

        if Commands.trace_conf is True:
            lConf = lower_confidence.GetResultForNetLabel(nets[2], nets[2]+'_fout')
            uConf = upper_confidence.GetResultForNetLabel(nets[2], nets[2]+'_fout')

        #we assign a color per network
        color = colors[1]

        j = 0
        if Commands.language == 'french':
            plt.scatter(single_data[j].x, single_data[j].y, color = color, label = u'Valeur pour le vidéo '+str(write.defineLabel(single_data[j].label,'A13')), linestyle = linestyles[j])
        if Commands.language == 'english':
            plt.scatter(single_data[j].x, single_data[j].y, color = color, label = 'Single data point for video '+str(write.defineLabel(single_data[j].label,'A13')), linestyle = linestyles[j])
        if max(single_data[j].y) > current_ymax:
            current_ymax = max(single_data[j].y)
        if min(single_data[j].y) < current_ymin:
            current_ymin = min(single_data[j].y)

        #for k in xrange(len(concat_data)):
            #if k > 0: break
        k = 0
        if Commands.language == 'french':
            plt.plot(concat_data[k].x, concat_data[k].y, color = color, label = u'Données concaténées pour le vidéo '+str(write.defineLabel(concat_data[k].label,'A13')), linestyle = linestyles[k])
        if Commands.language == 'english':
            plt.plot(concat_data[k].x, concat_data[k].y, color = color, label = 'Concatenated data for video '+str(write.defineLabel(concat_data[k].label,'A13')), linestyle = linestyles[k])
        if max(concat_data[k].y) > current_ymax:
            current_ymax = max(concat_data[k].y)
        if min(concat_data[k].y) < current_ymin:
            current_ymin = min(concat_data[k].y)

        if Commands.trace_conf is True:
            plt.plot(lConf[k].x, lConf[k].y, color = 'k', linestyle = '--')
            plt.plot(uConf[k].x, uConf[k].y, color = 'k', linestyle = '--')


        new_ymax = mathTools.myceil(current_ymax,base=0.01,outType=float) + 0.01
        new_ymin = mathTools.myfloor(current_ymin,base=0.01,outType=float) - 0.01

        ax2.set_ylim(ymin = new_ymin, ymax = new_ymax)
        ax2.set_xlim(xmin = 0, xmax = 50)#max(data_line.x)+1,5))
        ax2.set_yticks(np.arange(new_ymin,new_ymax+0.001,0.01))
        ax2.set_xticks(np.arange(0,51,5))#max(data_line.x)+1,5))
        ax2.set_xticklabels('',  visible=False)
        #ax2.set_ylabel('d statistic (K-S test)')
        #ax2.set_xlabel('Replications')
        ax2.minorticks_on
        ax2.grid(True, which='both')

        box = ax2.get_position()
        ax2.set_position([box.x0+box.width*0.03, box.y0 + box.height * 0.15, box.width, box.height * 1.0])




        #FIGURE legend and added text
        ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), frameon=False, ncol=2, prop = fontP)
        ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -1.45), frameon=False, ncol=2, prop = fontP)

        if Commands.language == 'french':
            fig.text(0.20, 0.83,u'Simulé avec:\nValeurs par défaut\nNombre aléatoire d\'amorce= '+str(first_seed)+u'\nIncrémentation = '+str(increments),style='italic',bbox=dict(boxstyle='Square,pad=0.3', fc='w'),fontsize=9)
        if Commands.language == 'english':
            fig.text(0.20, 0.83,'Simulated with:\nDefault values\nFirst seed = '+str(first_seed)+'\nIncrementation = '+str(increments),style='italic',bbox=dict(boxstyle='Square,pad=0.3', fc='w'),fontsize=9)


        '''
        #subplot 2: concat data figure
        #fig2 = plt.figure()
        ax2 = fig.add_subplot(2,1,2)
        #for each network
        current_ymax = 0
        for i in xrange(len(nets)):

            #getting the infos for that network
            concat_data = concat_fzp_data.GetResultForNetLabel(nets[i])

            #we assign a color per network
            color = colors[i]

            for data_line in concat_data:
                plt.plot(data_line.x, data_line.y, color = color, label = defineLabel(data_line.label,'A13'), linestyle = linestyles[concat_data.index(data_line)])
                if max(data_line.x) > current_ymax:
                    current_ymax = max(data_line.y)

        new_ymax = mathTools.myceil(current_ymax,base=0.1,outType=float)
        ax2.set_ylim(ymin = 0, ymax = new_ymax)
        ax2.set_xlim(xmin = 0, xmax = 60)#max(data_line.x)+1,5))
        ax2.set_yticks(np.arange(0,new_ymax+0.01,1))
        ax2.set_xticks(np.arange(0,61,5))#max(data_line.x)+1,5))
        #ax2.set_yticklabels('', visible=False)
        '''


        plt.savefig(os.path.join(working_path, 'data plot'))
        plt.clf()
        plt.close(fig)

        '''
        #student concat data figure
        fig3 = plt.figure()
        #for each network
        for i in xrange(len(nets)):

            #getting the infos for that network
            concat_stu = concat_stu_data.GetResultForNetLabel(nets[i])

            #we assign a color per network
            color = colors[i]
            for data_line in concat_stu:
                plt.plot(data_line.x, data_line.y, color = color, label = data_line.label)

        plt.xlabel('number of replications')
        plt.ylabel('d statistic (K-S test)')
        plt.title('Concat student data for test')
        plt.savefig(os.path.join(working_path, 'Concat student data for test'))
        plt.clf()
        plt.close(fig3)
        '''

###################
# Launch main
###################
if __name__ == "__main__":
    main()


