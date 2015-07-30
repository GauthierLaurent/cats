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
    return parser.parse_args()


def main():
    ################################
    #        Importing dependencies
    ################################

    #Native dependencies
    import os, copy
    import scipy.stats

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
    if os.path.isfile(os.path.join(Commands.cwd,'findBestFit.traj')):
        previous = write.load_traj(os.path.join(Commands.cwd,'findBestFit.traj'))
        vissim_results = previous[1]

        for p in reversed(points_folders):
            if p in previous[0]:
                points_folders.pop(points_folders.index(p))
    else:
        vissim_results = []

    if len(network) > 1:
        multi_networks = True
    else:
        multi_networks = False

    with open('find_best_fit.txt','w') as report:

        #setting video values
        for p in points_folders:
            point_path = os.path.join(Commands.cwd,p)

            for net in network:
                report.write(str(os.path.splitext(net.inpx_path.split(os.sep)[-1])[0])+'\n')

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
                    vissim_results.append([vissim_data,'os.path.splitext(net.inpx_path.split(os.sep)[-1])[0])_point_'+str(p)])

                for traj in net.traj_paths:

                    #loading video data
                    video_data = write.load_traj(traj)
                    if video_data == 'TrajVersionError':
                        raise ValueError('traj file data not up to the lastest version')
                    else:

                        #video best fit
                        video_data.forFMgap.cleanStats(0.5*config.fps)

                        loc, scale = scipy.stats.expon.fit(video_data.forFMgap.cumul_all.raw)
                        vid_d,vid_p = scipy.stats.kstest(video_data.forFMgap.cumul_all.raw, 'expon', (loc, scale))
                        report.write('\tvideo data:\n')
                        report.write('\t\td:'+str(vid_d)+'\n')
                        report.write('\t\tp:'+str(vid_p)+'\n')

                        #vissim best fit
                        loc, scale = scipy.stats.expon.fit(vissim_data.forFMgap.cumul_all.raw)
                        vis_d,vis_p = scipy.stats.kstest(vissim_data.forFMgap.cumul_all.raw, 'expon', (loc, scale))
                        report.write('\tvissim data:\n')
                        report.write('\t\td:'+str(vis_d)+'\n')
                        report.write('\t\tp:'+str(vis_p)+'\n')
                        report.write('\n')

    if points_folders != []:
        if os.path.isfile(os.path.join(Commands.cwd,'findBestFit.traj')):
            write.write_traj(Commands.cwd, 'findBestFit.traj', [previous[0] + points_folders, vissim_results])
        else:
            write.write_traj(Commands.cwd, 'findBestFit.traj', [points_folders, vissim_results])

    return


###################
# Launch main
###################
if __name__ == "__main__":
    main()

