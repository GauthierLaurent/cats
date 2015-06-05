# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 11:47:30 2015

@author: Laurent
"""
import argparse, os

#Command parser
def commands(parser):
    parser.add_argument('--points', type=int,            dest='pts',    default=None,        help='Number of graphs per figure (Nx1)')
    parser.add_argument('--dir',                         dest='cwd',    default=os.getcwd(), help='Directory (Optional: default is current working directory)')
    parser.add_argument('--cumul',  action='store_true', dest='cumul',  default=False,       help='If called, the cumulative distributions will be traced')
    parser.add_argument('--hspace', type=float,          dest='hspace', default=0.2,        help='Horizontal space between subplots')
    parser.add_argument('--xlim',   type=int,            dest='xlim',   default=30,          help='Limit of the x-axis when plotting the data. Default = 30')
    parser.add_argument('--title',  nargs='*',           dest='title',  default=None,          help='Limit of the x-axis when plotting the data. Default = 30')
    return parser.parse_args()

def main():
    ################################
    #        Importing dependencies
    ################################

    #Native dependencies
    import os, copy
    import matplotlib.pyplot as plt

    #Internal
    import pvc_write      as write
    import pvc_calibTools as calibTools
    import pvc_configure  as configure
    import pvc_outputs    as outputs
    import pvc_workers    as workers

    ################################
    #        Load settings
    ################################
    Commands = commands(argparse.ArgumentParser())
    config   = configure.Config('calib.cfg')

    #determining vissim, video, and corridor lists
    network = calibTools.Network.buildNetworkObjects(config)
    if Commands.pts is None:
        points_folders = [p for p in os.listdir(Commands.cwd) if 'point' in p and os.path.isdir(p)]
    else:
        if os.path.isdir(os.path.join(Commands.cwd,'point_'+str(Commands.pts))):
            points_folders = ['point_'+str(Commands.pts)]

        else:
            raise ValueError('Point folder specified does no exist in the current directory')

    ################################
    #        Output treatment
    ################################
    for p in points_folders:
        point_path = os.path.join(Commands.cwd,p)

        if len(network) > 1:
            multi_networks = True
        else:
            multi_networks = False

        for i in xrange(len(network)):

            if multi_networks is True:
                final_inpx_path = os.path.join(point_path,os.path.splitext(network[i].inpx_path.split(os.sep)[-1])[0])

            else:
                final_inpx_path = copy.deepcopy(point_path)

            vissim_data = outputs.Derived_data()
            vissim_data.activateConstraints(config)

            inputs = [final_inpx_path, False, network[i].corridors, vissim_data, config]
            file_list = [f for f in os.listdir(final_inpx_path) if f.endswith('fzp')]
            if len(file_list) > 1 and multi_networks is False:
                packedStatsLists = workers.createWorkers(file_list, outputs.treatVissimOutputs, inputs, workers.FalseCommands(), defineNbrProcess = config.nbr_process)

                vissim_data = packedStatsLists[0]

                for stat in xrange(1,len(packedStatsLists)):
                    outputs.Derived_data.concat(vissim_data, packedStatsLists[stat])

            else:
                vissim_data = outputs.treatVissimOutputs(file_list, inputs)

            ################################
            #        graph stuff
            ################################
            if Commands.title is not None:
                title = '\nfor '
                for p in xrange(len(Commands.title)):
                    if p < len(Commands.title) - 1:
                        title += Commands.title[p] + ' '
                    else:
                        title += Commands.title[p]
            else:
                title=None

            if config.output_forward_gaps:
                vissim_toplot = copy.deepcopy(vissim_data.forFMgap)
                dist_type = 'forward headway'

            if config.output_lane_change_gaps:
                vissim_toplot = copy.deepcopy(vissim_data.oppLCbgap)
                dist_type = 'lane change headway'

            #setting video values
            video_data_list = []
            video_name_list = []
            fout_list = []
            for traj in network[i].traj_paths:

                if 'gp06' in traj.split(os.sep)[-1]:
                    video_name_list.append('A13-06')
                elif 'gp10' in traj.split(os.sep)[-1]:
                    video_name_list.append('A13-10')
                elif 'gp11' in traj.split(os.sep)[-1]:
                    video_name_list.append('A13-11')
                elif 'gp12' in traj.split(os.sep)[-1]:
                    video_name_list.append('A13-12')
                else:
                    raise ValueError('Check the names of the videos before tracing!')

                #loading video data
                video_data = write.load_traj(traj)
                if video_data == 'TrajVersionError':
                    raise ValueError('traj file data not up to the lastest version')
                else:
                    if config.output_forward_gaps:
                        video_data_list.append(video_data.forFMgap)
                        mean_list, d_stat_list = calibTools.checkCorrespondanceOfOutputs([video_data.forFMgap], [vissim_data.forFMgap], config.sim_steps, config.fps)
                        fout_list += d_stat_list

                    if config.output_lane_change_gaps:
                        video_data_list.append(video_data.oppLCbgap)
                        mean_list, d_stat_list = calibTools.checkCorrespondanceOfOutputs([video_data.oppLCbgap], [vissim_data.oppLCbgap], config.sim_steps, config.fps)
                        fout_list += d_stat_list

            fig = plt.figure()
            fig.set_size_inches(7,7)

            if Commands.cumul:
                histtype = 'step'
            else:
                histtype = 'stepfilled'

            vissim_p_list = [vi/float(config.sim_steps) for vi in vissim_toplot.cumul_all.raw if vi/float(config.sim_steps) < 60]
            for j in xrange(2):
                for i in xrange(len(video_data_list)/2):
                    if (2*i+j) <= len(video_data_list):

                        video_p_list  = [vd/float(config.fps) for vd in video_data_list[2*i+j].cumul_all.raw if vd/float(config.fps) < 60]

                        #cheat to hide the end of the histogram with cumulative function 1/2
                        if Commands.cumul:
                            video_p_list.append(70)
                            vissim_p_list.append(70)

                        ax = fig.add_subplot(len(video_data_list)/2,2,(2*i+j)+1)
                        ax.hist(video_p_list, normed=True, histtype=histtype, cumulative=Commands.cumul, bins = 100, color = 'b', alpha=0.6, label='video data')
                        ax.hist(vissim_p_list, normed=True, histtype=histtype, cumulative=Commands.cumul, bins = 100, color = 'r', alpha=0.6, label='vissim data')
                        ax.set_title(video_name_list[2*i+j] + ', d = ' + str(round(fout_list[2*i+j],3)), fontsize='small')

                        #cheat to hide the end of the histogram with cumulative function 2/2
                        if Commands.cumul:
                            ax.set_xlim(right=Commands.xlim)


                        #making only the border labels appear
                        if i == len(video_data_list)/2-1:
                            ax.set_xlabel('time (sec)', fontsize='small')
                        else:
                            ax.set_xticklabels('',  visible=False)

                        if (2*i+j)%2 == 0:
                            ax.set_ylabel('occurrence', fontsize='small')
                        else:
                            ax.set_yticklabels('', visible=False)

            plt.subplots_adjust(hspace=Commands.hspace)
            ax.legend(loc='lower center', bbox_to_anchor=(0.0, -0.3), ncol=2, fontsize='small', frameon=False)
            plt.suptitle('Comparison of simulated and observed '+dist_type+' distributions'+title)

            if Commands.cumul:
                plt.savefig(os.path.join(final_inpx_path, 'Publishable video and Vissim cumulative distributions'))#, bbox_extra_artists=(lgd,), bbox_inches='tight')
            else:
                plt.savefig(os.path.join(final_inpx_path, 'Publishable video and Vissim distributions'))#, bbox_extra_artists=(lgd,), bbox_inches='tight')
            plt.clf()
            plt.close(f)

    return

###################
# Launch main
###################
if __name__ == "__main__":
    main()

