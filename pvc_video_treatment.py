#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
call exemples:
   to draw aligmeents:  -i -s -v GP060001.sqlite -a trace
   to process sqlite:   -M 9000 -g 30 -a process
'''

##################
# Import Native Libraries
##################
import os, sys, time, getopt, optparse
import matplotlib.pyplot as plt
import numpy as np

##################
# Import Traffic Intelligence
##################
#disabling outputs
import nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import moving, storage
sys.stdout = oldstdout
#Re-enable output

##################
# Import Internal Libraries
##################
import pvc_define  as define
import pvc_write   as write
import pvc_outputs as outputs
import pvc_config

################################ 
#        Load settings       
################################    
config   = pvc_config.Config('pvc.cfg')
    
################################ 
#        Trace functions       
################################
def traceAndclick(objects, pixelUnitRatio = None, imgPath = None):
    '''Pops-up the drawing interface and converts the results to Traffic Intelligence point
       list format for futur conversion into Traffic Intelligence alignement data'''

    fig = plt.figure()
    
    if imgPath is not None:
        img = plt.imread(imgPath)
        plt.imshow(img)

    for i in range(len(objects)):
        if pixelUnitRatio is not None:
            objects[i].plotOnWorldImage(float(pixelUnitRatio), withOrigin = True, color = '0.75')
            
        else:
            #object
            plt.plot(objects[i].getXCoordinates(), objects[i].getYCoordinates(), color = '0.75')
            #origine
            plt.plot(objects[i].getXCoordinates()[0], objects[i].getYCoordinates()[0], 'ro', color = '0.75')
    
    alignments = write.drawAlign(fig)
    plt.close()
    
    #transforming to moving.Point() form
    Alignments = []
    for points in alignments:
        Points = []
        for p in points:
            Points.append(moving.Point(p[0],p[1]))
        Alignments.append(Points)
        
    return Alignments

def processVideolist(config, video_names, save, loadImage):
        
    for video_name in video_names:
        objects = storage.loadTrajectoriesFromSqlite(os.path.join(config.path_to_sqlite, video_name), 'object')
        
        if loadImage:
            points = traceAndclick(objects, config.pixel_to_unit_ratio, os.path.join(config.path_to_image, config.image_name))
        else:
            points = traceAndclick(objects)
                    
        alignments = []
        for p in points:
            alignments.append(moving.Trajectory.fromPointList(p))         
        
        for a in alignments:
            print a

        if save is True:
            print '>> Saving data to the CSV file'
            define.writeAlignToCSV(config.path_to_inpx, config.inpx_name, video_name, alignments)
            print '>> Saving successfull'
        else:
            print '>> No-Saving option chosen, here are the data for manual copy-pasting:'
            print video_name
            for a in xrange(len(alignments)):
                print str(a)+';'+str(alignments[a])
            
################################ 
#        Process functions       
################################        
def cutTrajectories(uncut_objects, time_min, time_max):
    '''cut trajectories to keep only the positions between time_min and time_max'''
    cut_objects = []
    
    for o in uncut_objects:
        num = o.num
        geometry = o.geometry
        userType = o.userType
        positions = []
        velocities = []
        
        if o.getFirstInstant() > time_min:
            firstInstant = o.getFirstInstant()
        else:
            firstInstant = time_min     
        if time_max is None or o.getLastInstant() < time_max:
            lastInstant = o.getLastInstant()
        else:
            lastInstant = time_max     
        time_interval = [firstInstant,lastInstant]
    
        for pos in xrange(len(o.positions)):
            if o.getFirstInstant() + pos >= firstInstant and o.getFirstInstant() + pos <= lastInstant:
                positions.append(o.positions[pos])
                velocities.append(o.velocities[pos])    

        cut_objects.append(moving.MovingObject(num, moving.TimeInterval(time_interval[0], time_interval[1]), positions, velocities, geometry, userType))
    return cut_objects
 
def filterObjectsbyTime(unfiltered_objects, time_min, time_max):
    '''cuts the list of objects to keep only the information between time_min and time_max'''    
    if time_min is None: time_min = 0    
    filtered_objects = []
    for o in unfiltered_objects:
        if time_max is None:            
            if o.getFirstInstant() < time_max:
                filtered_objects.append(o)
        else:
            if o.getFirstInstant() < time_max and o.getLastInstant() > time_min:
                filtered_objects.append(o)   

    return cutTrajectories(filtered_objects, time_min, time_max)
    
def turnSqliteIntoTraj(config, min_time, max_time, fps):
    '''process function - saves data into traj files that can be loaded by the calibration algorithm'''
    #loading user defined information from [inpxname].csv
    VissimCorridors, trafIntCorridors = define.extractVissimCorridorsFromCSV(config.path_to_inpx, config.inpx_name)
    video_infos = define.extractAlignmentsfromCSV(config.path_to_inpx, config.inpx_name)
    
    #variable declaration
    opportunisticLC = 0
    mandatoryLC = 0
    flow = 0
    forward_gaps = []
    forward_speeds = []
    man_agaps = []
    man_bgaps = []
    opp_agaps = []
    opp_bgaps = []

    for i in xrange(len(video_infos)):
        print ' >> starting work on ' + str(video_infos[i].video_name) + ' <<'
        
        objects = storage.loadTrajectoriesFromSqlite(os.path.join(config.path_to_sqlite,video_infos[i].video_name), 'object')

        if min_time is not None or max_time is not None:        
            objects = filterObjectsbyTime(objects, min_time, max_time)

        alignments = []
        alignNames = []
        for a in xrange(len(video_infos[i].alignments)):
            alignments.append(moving.Trajectory.fromPointList(video_infos[i].alignments[a].point_list))
            alignNames.append(video_infos[i].alignments[a].name)
            
        #Assignments of alignments
        for a in alignments:
            a.computeCumulativeDistances()
            a.plot('k', linewidth = 2, hold = True)
            #line = np.array(a)
            #plt.plot(line[:,0], line[:,1], 'k', linewidth = 2)
        
        for o in objects:
            o.projectCurvilinear(alignments)
            o.curvilinearVelocities = o.curvilinearPositions.differentiate(True)
        
        #flow
        onevid_flow = len(objects)
        
        #lane change count by type        
        oppObjDict, manObjDict, laneDict = outputs.laneChange(objects,trafIntCorridors)
        onevid_opportunisticLC = sum([len(oppObjDict[j]) for j in oppObjDict])
        onevid_mandatoryLC = sum([len(manObjDict[j]) for j in manObjDict])
        print ' == Lane change compilation done ==  |' + str(time.clock())
            
        #Calculation of stats stuff
        onevid_forward_gaps = []
        onevid_forward_speeds = []

        #dictionnary of corridor name per alignement number
        align_corr_dict = {}        
        for corridor in trafIntCorridors:
            for align in corridor.to_eval:
                if align not in align_corr_dict.keys():
                    align_corr_dict[align] = corridor.name

        #plot s/t graph
        write.plot_st(objects, align_corr_dict, alignNames, fps, config.path_to_inpx, video_infos[i].video_name)
        
        for c in xrange(len(trafIntCorridors)):                              
            #Forward gaps and speeds calculations        
            graph_inst = []
            graph_gaps = []
            for index,lane in enumerate(alignments):
                if index in trafIntCorridors[c].to_eval:
                    [snappedSpline, snappedSplineLeadingPoint, snappedPoint, subsegmentDistance, S, Y] = moving.getSYfromXY(moving.Point.midPoint(lane[0], lane[1]), alignments, 0.5)
                    sorted_instants, raw_speeds = outputs.calculateInstants(objects, S, index)                              
                    raw_gaps = outputs.calculateGaps(sorted_instants)
                    onevid_forward_gaps += list(raw_gaps)
                    onevid_forward_speeds += list(raw_speeds)
                    graph_inst += sorted_instants[:-1]
                    graph_gaps += list(raw_gaps)
                    
                    print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(alignments)) + ' ==  |' + str(time.clock())
           
            #trace graph: flow vs time during video
            sorted_graph_inst, sorted_graph_gaps = define.sort2lists(graph_inst,graph_gaps)
            if len(sorted_graph_inst) > 0:
                write.plot_qt(sorted_graph_inst, sorted_graph_gaps, config.path_to_inpx, video_infos[i].video_name, trafIntCorridors[c].name, fps, min_time, max_time)
           
        #mandatory lane change gaps
        onevid_man_agaps, onevid_man_bgaps = outputs.laneChangeGaps(manObjDict, laneDict, objects)
        print ' == Mandatory lane change gaps calculation done  ==  |' + str(time.clock())
        
        #opportunistic lane change gaps
        onevid_opp_agaps, onevid_opp_bgaps = outputs.laneChangeGaps(oppObjDict, laneDict, objects)
        print ' == Opportunistic lane change gaps calculation done ==  |' + str(time.clock())
    
        #variable concatenation
        opportunisticLC += onevid_opportunisticLC 
        mandatoryLC += onevid_mandatoryLC
        flow += onevid_flow
        forward_gaps += onevid_forward_gaps
        forward_speeds += onevid_forward_speeds
        man_agaps += list(onevid_man_agaps)
        man_bgaps += list(onevid_man_bgaps)
        opp_agaps += list(onevid_opp_agaps)
        opp_bgaps += list(onevid_opp_bgaps)
       
    #statistical distribution treatment
    forward_followgap = outputs.stats([forward_gaps])
    opportunistic_LCagap = outputs.stats([opp_agaps])
    opportunistic_LCbgap = outputs.stats([opp_bgaps])
    mandatory_LCagap = outputs.stats([man_agaps])
    mandatory_LCbgap = outputs.stats([man_bgaps])
    forward_speeds = outputs.stats([forward_speeds])

    #from forward TIV, calculate flow:
    raw_flow_dist = []
    for dist in forward_followgap.distributions:
        raw_flow_dist.append(list(3600*fps/np.asarray(dist.raw)))    
    flowDist = outputs.stats(raw_flow_dist)

    #putting the calculated information into a report file
    ##calculating 13 usefull centiles for tracing speeds in vissim
    percentages = []
    values_at_p = []
    for i in [0,2.5,5]+range(10,31,10)+[50]+range(70,91,10)+[95, 97.5,100]:
        percentages.append(i)
        values_at_p.append( np.percentile(forward_speeds.cumul_all.raw,i) )
        
    ##building the video_name list
    video_names = ''
    for i in xrange(len(video_infos)):
        if i == len(video_infos) -1:
            video_names += video_infos[i].video_name
        else:
            video_names += video_infos[i].video_name + ', '
       
    ##building the other_info list to print
    other_info = [['flow:', flow],
                  ['number of opportunistic lane changes:', opportunisticLC],
                  ['number of mandatory lane changes:', mandatoryLC],
                  ['variable_name','mean','25th centile','median','75th centile','standard deviation'],
                  ['Forward follow gaps:',          forward_followgap.cumul_all.mean,    forward_followgap.cumul_all.firstQuart,    forward_followgap.cumul_all.median,    forward_followgap.cumul_all.thirdQuart,    forward_followgap.cumul_all.std],                                  
                  ['Flow distribution (3600/gap):', flowDist.cumul_all.mean,             flowDist.cumul_all.firstQuart,             flowDist.cumul_all.median,             flowDist.cumul_all.thirdQuart,             flowDist.cumul_all.std],
                  ['Opportunistic gaps (after):',   opportunistic_LCagap.cumul_all.mean, opportunistic_LCagap.cumul_all.firstQuart, opportunistic_LCagap.cumul_all.median, opportunistic_LCagap.cumul_all.thirdQuart, opportunistic_LCagap.cumul_all.std],
                  ['Opportunistic gaps (before):',  opportunistic_LCbgap.cumul_all.mean, opportunistic_LCbgap.cumul_all.firstQuart, opportunistic_LCbgap.cumul_all.median, opportunistic_LCbgap.cumul_all.thirdQuart, opportunistic_LCbgap.cumul_all.std],
                  ['Mandatory gaps (after):',       mandatory_LCagap.cumul_all.mean,     mandatory_LCagap.cumul_all.firstQuart,     mandatory_LCagap.cumul_all.median,     mandatory_LCagap.cumul_all.thirdQuart,     mandatory_LCagap.cumul_all.std],
                  ['Mandatory gaps (before):',      mandatory_LCbgap.cumul_all.mean,     mandatory_LCbgap.cumul_all.firstQuart,     mandatory_LCbgap.cumul_all.median,     mandatory_LCbgap.cumul_all.thirdQuart,     mandatory_LCbgap.cumul_all.std],
                  ['Speeds:',                       forward_speeds.cumul_all.mean,       forward_speeds.cumul_all.firstQuart,       forward_speeds.cumul_all.median,       forward_speeds.cumul_all.thirdQuart,       forward_speeds.cumul_all.std],                 
                 ]
    ##generating the output    
    write.writeRealDataReport(config.path_to_inpx, video_names, config.inpx_name, min_time, max_time, [percentages,values_at_p], other_info)
    
    #dumping serialised data
    print ' == Dumping to ' +str(config.inpx_name.strip('.inpx') + '.traj')+' ==  |' + str(time.clock())
    write.write_traj(config.path_to_inpx, config.inpx_name.strip('.inpx'), opportunisticLC, mandatoryLC, flow, forward_followgap, opportunistic_LCagap, opportunistic_LCbgap, mandatory_LCagap, mandatory_LCbgap, forward_speeds)        
 
    print ' == Processing of video ' + str(video_infos[i].video_name) + ' done <<'
    
################################ 
#        Options       
################################
def usage():
    print ('usage: %s\n'
           '\tprocess options:    [-m min_time] [-M max_time] [-g fps_factor]\n'
           '\ttrace options:      [-s] [-v single_video_name] [-i]\n'
           '\tanalysis choice... -a process/trace?' % sys.argv[0])
    return 100
    
################################ 
#        Main       
################################

def main(argv):
    time.clock()

    commands = pvc_config.commands(optparse.OptionParser(), 'Video')

    import pdb;pdb.set_trace()
    if not commands.mode: return usage()

    #process options
    min_time = commands.min_time
    max_time = commands.max_time
    fps      = commands.fps
    #trace options
    video_name = commands
    video_names = []
    save       = commands.save
    loadImage  = commands.loadImage


    print '== Starting work for the following network : ' + str(config.inpx_name) +' =='
    
    if commands.mode == 'process':
        print '== Processing sqlite list contained in the csv file for ' + str(config.inpx_name)  +' =='
        turnSqliteIntoTraj(config, min_time, max_time, fps)
        
    elif commands.mode == 'trace':
        if video_name is not None:
            if os.path.isfile(os.path.join(config.path_to_sqlite, video_name)):
                video_names = [video_name]
            else:
                print 'video " ' + str(video_name) + ' " not found'
                return usage()
        else:
            video_names = [f for f in os.listdir(config.path_to_sqlite) if f.endswith('.sqlite')]
            
        if video_names == []:
            print 'No video specified'
            return usage()

        print '== Loading sqlites from ' + str(config.path_to_sqlite) +' =='
        string = video_names[0]
        for i in xrange(len(video_names)-1):
            string = string +', '+ str(video_names[i+1])
        print '== Enabling alignment drawing for the following videos: '+str(string) +' =='  

        processVideolist(config, video_names, save, loadImage)

    else:
        return usage()
       
    
if __name__ == '__main__': sys.exit(main(sys.argv))