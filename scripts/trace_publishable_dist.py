# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 11:47:30 2015

@author: Laurent
"""
'''
ex, 1 graph with subgraphs: --points 1 --xlim 20 --cumul --title default values
    1 graph per video:      --points 739 --xlim 20 --concat --cumul --title calibrated values
'''

import argparse, os
import pvc_mathTools as mathTools
import matplotlib.pyplot as plt
import numpy as np

#Command parser
def commands(parser):
    parser.add_argument('--points', type=int, nargs='*', dest='pts',            default=None,        help='Number of graphs per figure (Nx1)')
    parser.add_argument('--dir',                         dest='cwd',            default=os.getcwd(), help='Directory (Optional: default is current working directory)')
    parser.add_argument('--cumul',  action='store_true', dest='cumul',          default=False,       help='If called, the cumulative distributions will be traced')
    parser.add_argument('--concat', action='store_false',dest='concat',         default=True,        help='If called, individual graphs will be traced for every video')
    parser.add_argument('--hspace', type=float,          dest='hspace',         default=0.2,         help='Horizontal space between subplots')
    parser.add_argument('--xlim',   type=int,            dest='xlim',           default=30,          help='Limit of the x-axis when plotting the data. Default = 30')
    parser.add_argument('--title',  nargs='*',           dest='title',          default=None,        help='Text to add the the title ''Comparison of simulated and observed [type of output] [for]'' ')
    parser.add_argument('--valid',  nargs='*',           dest='pushValidLast',  default=None,        help='Text to add the the title ''Comparison of simulated and observed [type of output] [for]'' ')
    parser.add_argument('--type',   nargs='*', choices=['Follow','OppLC', 'ManLC'], dest='type',     default='Follow')
    parser.add_argument('--lang',              choices = ['french', 'english'],     dest='language', default='french', help='Choose the language displayed in the graphics. Default = french')
    return parser.parse_args()

def splitByGraph(vissimList,videoList,points_to_keep,validLast=None):

    splitList = []
    video_names = []
    for i in xrange(len(vissimList.GetLabels())):
        if int(vissimList.results[i].label.split('&')[1].split('_')[-1]) in points_to_keep:
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

    video_names, splitList = mathTools.sort2lists(video_names,splitList,ascending_order=True)

    if validLast is not None:
        keep = []
        keep_name = []
        for i in reversed(xrange(len(video_names))):
            if video_names[i].split('-')[1] in validLast:
                keep.append(splitList[i])
                keep_name.append(video_names[i])
                splitList.pop(i)
                video_names.pop(i)


        video_names = video_names + [n for n in reversed(keep_name)]
        splitList = splitList + [k for k in reversed(keep)]

    return splitList

def getLabel(rawLabel, Commands):
    if 'video' in rawLabel:
        if Commands.language == 'french':
            return u'Données terrain'
        else:
            return 'Field data'
    else:
        if int(rawLabel.split('&')[1].strip('point_')) == 1:
            if Commands.language == 'french':
                return u'Paramètres de départ'
            else:
                return 'Starting parameters'
        else:
            if Commands.language == 'french':
                return u'Paramètres calibrés'
            else:
                return 'Calibrated parameters'

def trace(Commands, vissim_results, video__results, graph_type):
    if Commands.title is not None:
        title = '\nfor '
        for p in xrange(len(Commands.title)):
            if p < len(Commands.title) - 1:
                title += Commands.title[p] + ' '
            else:
                title += Commands.title[p]
    else:
        title=None

    if Commands.cumul:
        histtype = 'step'
    else:
        histtype = 'stepfilled'

    video_data_list = splitByGraph(vissim_results, video__results, Commands.pts, validLast=Commands.pushValidLast)

    colors = ['r','g','b','k']

    if Commands.concat:
        fig = plt.figure()
        fig.set_size_inches(7,3.5*len(video_data_list)/2)

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
                        bins = 10000

                    if Commands.concat:
                        ax = fig.add_subplot(len(video_data_list)/2,2,(2*i+j)+1)
                    else:
                        ax = fig.add_subplot(1,1,1)

                    ax.hist(line.y, normed=True, histtype=histtype, cumulative=Commands.cumul, bins = bins, color = colors[video_data_list[2*i+j].index(line)], alpha=0.6, label=getLabel(line.label, Commands))

                ax.grid(True, which='both')
                if Commands.concat:
                    ax.set_title(video_data_list[2*i+j][0].label.split('&')[0], fontsize='small')

                #cheat to hide the end of the histogram with cumulative function 2/2
                if Commands.cumul:
                    ax.set_xlim(right=Commands.xlim, left = 0)
                    ax.set_xticks(np.arange(0,Commands.xlim+1,float(Commands.xlim)/10))

                    ax.set_ylim(top=1.0)
                    ax.set_yticks(np.arange(0,1.1,0.1))

                #labels
                if Commands.language == 'french':
                    xlabel = u'temps (s)'
                    if Commands.cumul:
                        ylabel = u'probabilité cumulée'
                    else:
                        ylabel = u'occurence'

                else:
                    xlabel = u'time (s)'
                    if Commands.cumul:
                        ylabel = u'cumulated probability'
                    else:
                        ylabel = u'occurence'

                if Commands.concat:
                    #making only the border labels appear
                    if i == len(video_data_list)/2-1:
                        ax.set_xlabel(xlabel, fontsize='small')
                    else:
                        ax.set_xticklabels('',  visible=False)

                    if (2*i+j)%2 == 0:
                        ax.set_ylabel(ylabel, fontsize='small')
                    else:
                        ax.set_yticklabels('', visible=False)

                else:
                    ax.set_xlabel(xlabel, fontsize='small')
                    ax.set_ylabel(ylabel, fontsize='small')

                plt.setp(ax.get_xticklabels(), fontsize=8)
                plt.setp(ax.get_yticklabels(), fontsize=8)

                box = ax.get_position()
                ax.set_position([box.x0, box.y0 + 0.5, box.width, box.height])

                if not Commands.concat:
                    ax.legend(loc='lower center', bbox_to_anchor=(0.0, -0.4), ncol=len(video_data_list[2*i+j]), fontsize='small', frameon=False)
                    #plt.suptitle('Comparison of simulated and observed '+dist_type+' distributions'+title+' for '+video_data_list[2*i+j][0].label.split('&')[0])

                    if Commands.cumul:
                        if Commands.language == 'french':
                            name = 'Publishable video and Vissim cumulative distributions for '+graph_type+' for '+video_data_list[2*i+j][0].label.split('&')[0]+'_fr'
                        else:
                            name = 'Publishable video and Vissim cumulative distributions for '+graph_type+' for '+video_data_list[2*i+j][0].label.split('&')[0]+'_en'
                        fig.savefig(os.path.join(Commands.cwd, name), dpi=600)
                    else:
                        if Commands.language == 'french':
                            'Publishable video and Vissim distributions for '+graph_type+' for '+video_data_list[2*i+j][0].label.split('&')[0]+'_fr'
                        else:
                            'Publishable video and Vissim distributions for '+graph_type+' for '+video_data_list[2*i+j][0].label.split('&')[0]+'_en'
                        fig.savefig(os.path.join(Commands.cwd, name), dpi=600)
                    plt.clf()
                    plt.close(fig)


    if Commands.concat:
        plt.subplots_adjust(hspace=Commands.hspace)

        ax.legend(loc='lower center', bbox_to_anchor=(-0.1, -0.45), ncol=len(video_data_list[2*i+j]), fontsize='small', frameon=False)
        #plt.suptitle('Comparison of simulated and observed '+dist_type+' distributions'+title)

        if Commands.cumul:
            if Commands.language == 'french':
                name = 'Publishable video and Vissim cumulative distributions for '+graph_type+'_fr'
            else:
                name ='Publishable video and Vissim cumulative distributions for '+graph_type+'_en'
            fig.savefig(os.path.join(Commands.cwd, name), dpi=300)
        else:
            if Commands.language == 'french':
                name = 'Publishable video and Vissim distributions for '+graph_type+'_fr'
            else:
                name ='Publishable video and Vissim distributions for '+graph_type+'_en'
            fig.savefig(os.path.join(Commands.cwd, name), dpi=300)
        plt.clf()
        plt.close(fig)
    return

def main():
    ################################
    #        Importing dependencies
    ################################

    #Native dependencies
    import os, copy

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
        forFMgap_vissim_results = previous[1]
        forFMgap_video__results = previous[2]
        oppLCgap_vissim_results = previous[3]
        oppLCgap_video__results = previous[4]
        manLCgap_vissim_results = previous[5]
        manLCgap_video__results = previous[6]

        for p in reversed(points_folders):
            if p in previous[0]:
                points_folders.pop(points_folders.index(p))
    else:
        forFMgap_vissim_results = calibTools.ResultList()
        forFMgap_video__results = calibTools.ResultList()
        oppLCgap_vissim_results = calibTools.ResultList()
        oppLCgap_video__results = calibTools.ResultList()
        manLCgap_vissim_results = calibTools.ResultList()
        manLCgap_video__results = calibTools.ResultList()

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
                    if config.cmp_for_gaps:
                        video_data.forFMgap.cleanStats(0.5*config.fps)

                        mean_list, d_stat_list = calibTools.checkCorrespondanceOfOutputs([video_data.forFMgap], [vissim_data.forFMgap], config.sim_steps, config.fps)

                        for vi in vissim_data.forFMgap.cumul_all.raw:
                            if vi/float(config.sim_steps) < 60:
                                forFMgap_vissim_results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&'+str(p),net.inpx_path.split(os.sep)[-1].strip('.inpx'),vi,vi/float(config.sim_steps), d_stat_list[0])

                        if write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video' not in forFMgap_video__results.GetLabels():
                            for vd in video_data.forFMgap.cumul_all.raw:
                                if vd/float(config.fps) < 60:
                                    forFMgap_video__results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video',net.inpx_path.split(os.sep)[-1].strip('.inpx'),vd,vd/float(config.fps))

                    if config.cmp_opp_lcgaps:
                        video_data.oppLCbgap.cleanStats(0.5*config.fps)

                        mean_list, d_stat_list = calibTools.checkCorrespondanceOfOutputs([video_data.oppLCbgap], [vissim_data.oppLCbgap], config.sim_steps, config.fps)

                        for vi in vissim_data.oppLCbgap.cumul_all.raw:
                            if vi/float(config.sim_steps) < 60:
                                oppLCgap_vissim_results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&'+str(p),net.inpx_path.split(os.sep)[-1].strip('.inpx'),vi,vi/float(config.sim_steps), d_stat_list[0])

                        if write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video' not in oppLCgap_video__results.GetLabels():
                            for vd in video_data.oppLCbgap.cumul_all.raw:
                                if vd/float(config.fps) < 60:
                                    oppLCgap_video__results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video',net.inpx_path.split(os.sep)[-1].strip('.inpx'),vd,vd/float(config.fps))

                    if config.cmp_man_lcgaps:
                        video_data.manLCbgap.cleanStats(0.5*config.fps)

                        mean_list, d_stat_list = calibTools.checkCorrespondanceOfOutputs([video_data.manLCbgap], [vissim_data.manLCbgap], config.sim_steps, config.fps)

                        for vi in vissim_data.manLCbgap.cumul_all.raw:
                            if vi/float(config.sim_steps) < 60:
                                manLCgap_vissim_results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&'+str(p),net.inpx_path.split(os.sep)[-1].strip('.inpx'),vi,vi/float(config.sim_steps), d_stat_list[0])

                        if write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video' not in manLCgap_video__results.GetLabels():
                            for vd in video_data.manLCbgap.cumul_all.raw:
                                if vd/float(config.fps) < 60:
                                    manLCgap_video__results.addResult(write.defineLabel(traj.split(os.sep)[-1],'A13')+'&video',net.inpx_path.split(os.sep)[-1].strip('.inpx'),vd,vd/float(config.fps))

    if points_folders != []:
        if os.path.isfile(os.path.join(Commands.cwd,'tracePublishableDist.traj')):
            write.write_traj(Commands.cwd, 'tracePublishableDist', [previous[0] + points_folders, forFMgap_vissim_results, forFMgap_video__results, oppLCgap_vissim_results, oppLCgap_video__results, manLCgap_vissim_results, manLCgap_video__results])
        else:
            write.write_traj(Commands.cwd, 'tracePublishableDist', [points_folders, forFMgap_vissim_results, forFMgap_video__results, oppLCgap_vissim_results, oppLCgap_video__results, manLCgap_vissim_results, manLCgap_video__results])

    ################################
    #        graph stuff
    ################################
    for graph_type in Commands.type:
        if graph_type == 'Follow':
            trace(Commands, forFMgap_vissim_results, forFMgap_video__results, graph_type)

        if graph_type == 'OppLC':
            trace(Commands, oppLCgap_vissim_results, oppLCgap_video__results, graph_type)

        if graph_type == 'ManLC':
            trace(Commands, manLCgap_vissim_results, manLCgap_video__results, graph_type)

    return


###################
# Launch main
###################
if __name__ == "__main__":
    main()

