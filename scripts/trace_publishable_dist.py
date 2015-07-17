# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 11:47:30 2015

@author: Laurent
"""
import argparse, os

'''
ex, 1 graph with subgraphs: --points 1 --xlim 20 --cumul --title default values
    1 graph per video:      --points 739 --xlim 20 --concat --cumul --title calibrated values
'''

#Command parser
def commands(parser):
    parser.add_argument('--points', type=int, nargs='*', dest='pts',    default=None,        help='Number of graphs per figure (Nx1)')
    parser.add_argument('--dir',                         dest='cwd',    default=os.getcwd(), help='Directory (Optional: default is current working directory)')
    parser.add_argument('--cumul',  action='store_true', dest='cumul',  default=False,       help='If called, the cumulative distributions will be traced')
    parser.add_argument('--concat', action='store_false',dest='concat', default=True,        help='If called, individual graphs will be traced for every video')
    parser.add_argument('--hspace', type=float,          dest='hspace', default=0.2,         help='Horizontal space between subplots')
    parser.add_argument('--xlim',   type=int,            dest='xlim',   default=30,          help='Limit of the x-axis when plotting the data. Default = 30')
    parser.add_argument('--title',  nargs='*',           dest='title',  default=None,        help='Text to add the the title ''Comparison of simulated and observed [type of output] [for]'' ')
    return parser.parse_args()

def splitByGraph(vissimList,videoList):

    splitList = []
    video_names = []
    for i in xrange(len(vissimList.GetLabels())):
        name = vissimList.results[i].label.split('&')[0]
        if name in video_names:
            splitList[video_names.index(name)].append(vissimList.results[i])
        else:
            splitList.append([vissimList.results[i]])
            video_names.append(name)
    for j in xrange(len(videoList.GetLabels())):
        name = videoList.results[j].label.split('&')[0]
        if name in video_names:
            splitList[video_names.index(name)].append(videoList.results[j])
        else:
            splitList.append([videoList.results[j]])
            video_names.append(name)

    return splitList

def getLabel(rawLabel):
    if 'video' in rawLabel:
        return 'Field data'
    else:
        if int(rawLabel.split('&')[1].strip('point_')) == 1:
            return 'Starting parameters'
        else:
            return 'Calibrated parameters'

def main():
    ################################
    #        Importing dependencies
    ################################

    #Native dependencies
    import os, copy
    import matplotlib.pyplot as plt
    import numpy as np

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
        points_folders = []
        for pts in Commands.pts:
            if os.path.isdir(os.path.join(Commands.cwd,'point_'+str(pts))):
                points_folders.append('point_'+str(pts))

            else:
                raise ValueError('Point folder '+str(p)+' specified does no exist in the current directory')

    ################################
    #        Output treatment
    ################################
    #looking for already produced data
    if os.path.isfile(os.path.join(Commands.cwd,'tracePublishableDist.traj')):
        previous = write.load_traj(os.path.join(Commands.cwd,'tracePublishableDist.traj'))
        vissim_results = previous[1]
        video__results = previous[2]

        for p in reversed(points_folders):
            if p in previous[0]:
                points_folders.pop(points_folders.index(p))
    else:
        vissim_results = calibTools.ResultList()
        video__results = calibTools.ResultList()

    if len(network) > 1:
        multi_networks = True
    else:
        multi_networks = False

    #setting video values


    for p in points_folders:
        point_path = os.path.join(Commands.cwd,p)

        for net in network:

            if multi_networks is True:
                final_inpx_path = os.path.join(point_path,os.path.splitext(net.inpx_path.split(os.sep)[-1])[0])

            else:
                final_inpx_path = copy.deepcopy(point_path)

            vissim_data = outputs.Derived_data()
            vissim_data.activateConstraints(config)

            inputs = [final_inpx_path, True, net.corridors, vissim_data, config]
            file_list = [f for f in os.listdir(final_inpx_path) if f.endswith('fzp')]
            if len(file_list) > 1 and multi_networks is False:
                packedStatsLists = workers.createWorkers(file_list, outputs.treatVissimOutputs, inputs, workers.FalseCommands(), defineNbrProcess = config.nbr_process)

                vissim_data = packedStatsLists[0]

                for stat in xrange(1,len(packedStatsLists)):
                    outputs.Derived_data.concat(vissim_data, packedStatsLists[stat])

            else:
                vissim_data = outputs.treatVissimOutputs(file_list, inputs)

            for traj in net.traj_paths:

                #loading video data
                video_data = write.load_traj(traj)
                if video_data == 'TrajVersionError':
                    raise ValueError('traj file data not up to the lastest version')
                else:
                    video_data.forFMgap.cleanStats(0.5*config.fps)

                    mean_list, d_stat_list = calibTools.checkCorrespondanceOfOutputs([video_data.forFMgap], [vissim_data.forFMgap], config.sim_steps, config.fps)

                    for vi in vissim_data.forFMgap.cumul_all.raw:
                        if vi/float(config.sim_steps) < 60:
                            vissim_results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&'+str(p),net.inpx_path.split(os.sep)[-1].strip('.inpx'),vi,vi/float(config.sim_steps), d_stat_list[0])

                    if write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video' not in video__results.GetLabels():
                        for vd in video_data.forFMgap.cumul_all.raw:
                            if vd/float(config.fps) < 60:
                                video__results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video',net.inpx_path.split(os.sep)[-1].strip('.inpx'),vd,vd/float(config.fps))

    if points_folders != []:
        write.write_traj(Commands.cwd, 'tracePublishableDist', [points_folders, vissim_results, video__results])

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

    if Commands.concat:
        fig = plt.figure()
        fig.set_size_inches(7,7)

    if Commands.cumul:
        histtype = 'step'
    else:
        histtype = 'stepfilled'

    video_data_list = splitByGraph(vissim_results, video__results)

    colors = ['r','g','b','k']

    for j in xrange(2):
        for i in xrange(len(video_data_list)/2):
            if (2*i+j) <= len(video_data_list):

                if not Commands.concat:
                    fig = plt.figure()
                    fig.set_size_inches(7,7)

                for line in video_data_list[2*i+j]:
                    #cheat to hide the end of the histogram with cumulative function 1/2
                    if Commands.cumul:
                        line.y.append(70)

                    bins = 100
                    if Commands.cumul:
                        bins = 1000

                    if Commands.concat:
                        ax = fig.add_subplot(len(video_data_list)/2,2,(2*i+j)+1)
                    else:
                        ax = fig.add_subplot(1,1,1)

                    ax.hist(line.y, normed=True, histtype=histtype, cumulative=Commands.cumul, bins = bins, color = colors[video_data_list[2*i+j].index(line)], alpha=0.6, label=getLabel(line.label))

                ax.grid(True, which='both')
                if Commands.concat:
                    ax.set_title(video_data_list[2*i+j][0].label.split('&')[0], fontsize='small')

                #cheat to hide the end of the histogram with cumulative function 2/2
                if Commands.cumul:
                    ax.set_xlim(right=Commands.xlim)
                    ax.set_xticks(np.arange(0,Commands.xlim+1,float(Commands.xlim)/10))

                    ax.set_ylim(top=1.0)
                    ax.set_yticks(np.arange(0,1.1,0.1))

                if Commands.concat:
                    #making only the border labels appear
                    if i == len(video_data_list)/2-1:
                        ax.set_xlabel('time (sec)', fontsize='small')
                    else:
                        ax.set_xticklabels('',  visible=False)

                    if (2*i+j)%2 == 0:
                        if Commands.cumul:
                            ax.set_ylabel('cumulated probability', fontsize='small')
                        else:
                            ax.set_ylabel('occurrence', fontsize='small')
                    else:
                        ax.set_yticklabels('', visible=False)
                else:
                    ax.set_xlabel('time (sec)', fontsize='small')
                    if Commands.cumul:
                        ax.set_ylabel('cumulated probability', fontsize='small')
                    else:
                        ax.set_ylabel('occurrence', fontsize='small')
                plt.setp(ax.get_xticklabels(), fontsize=8)
                plt.setp(ax.get_yticklabels(), fontsize=8)

                if not Commands.concat:
                    ax.legend(loc='lower center', bbox_to_anchor=(0.0, -0.3), ncol=len(video_data_list[2*i+j]), fontsize='small', frameon=False)
                    #plt.suptitle('Comparison of simulated and observed '+dist_type+' distributions'+title+' for '+video_data_list[2*i+j][0].label.split('&')[0])

                    if Commands.cumul:
                        plt.savefig(os.path.join(Commands.cwd, 'Publishable video and Vissim cumulative distributions for '+video_data_list[2*i+j][0].label.split('&')[0]))
                    else:
                        plt.savefig(os.path.join(Commands.cwd, 'Publishable video and Vissim distributions for '+video_data_list[2*i+j][0].label.split('&')[0]))
                    plt.clf()
                    plt.close(fig)


    if Commands.concat:
        plt.subplots_adjust(hspace=Commands.hspace)
        ax.legend(loc='lower center', bbox_to_anchor=(0.0, -0.3), ncol=len(video_data_list[2*i+j]), fontsize='small', frameon=False)
        #plt.suptitle('Comparison of simulated and observed '+dist_type+' distributions'+title)

        if Commands.cumul:
            plt.savefig(os.path.join(Commands.cwd, 'Publishable video and Vissim cumulative distributions'))
        else:
            plt.savefig(os.path.join(Commands.cwd, 'Publishable video and Vissim distributions'))
        plt.clf()
        plt.close(fig)

    return


###################
# Launch main
###################
if __name__ == "__main__":
    main()

