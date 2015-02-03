#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
call exemples:
   to draw aligments:            -i -s -v GP130001.sqlite
   to draw many aligments:       -i -s -k
   to process all sqlite:        -M 9000 -g 30 -a process
   to process specified (2):     -M 9000 -g 30 -a process -v GP130001.sqlite GP020001.sqlite
   to proocess all individually: -M 9000 -g 30 -a process -o
   to diagnose a single video:   -M 9000 -g 30 -a diagnose -d 130 -v GP130001.sqlite
'''

##################
# Import Native Libraries
##################

import os, sys, time, argparse
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
def traceAndclick(objects, pixelUnitRatio = 1, imgPath = None):
    '''Pops-up the drawing interface and converts the results to Traffic Intelligence point
       list format for futur conversion into Traffic Intelligence alignement data'''

    fig = plt.figure()
    
    if imgPath is not None:
        img = plt.imread(imgPath)
        plt.imshow(img)

    for i in range(len(objects)):
        if imgPath is not None:               
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
            Points.append(moving.Point(p[0]/pixelUnitRatio,p[1]/pixelUnitRatio))
        Alignments.append(Points)
        
    return Alignments

def processVideolist(config, video_names, save, loadImage, keep_align):
        
    for v in xrange(len(video_names)):
        
        if keep_align is True and v > 0:
            pass
        else:
            objects = storage.loadTrajectoriesFromSqlite(os.path.join(config.path_to_sqlite, video_names[v]), 'object')
            
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
            print '>> Saving data for '+str(video_names[v])+' to the CSV file'
            define.writeAlignToCSV(config.path_to_csv, config.inpx_name, video_names[v], alignments)
            print '>> Saving successfull'
        else:
            print '>> No-Saving option chosen, here are the data for manual copy-pasting:'
            print video_names[v]
            for a in xrange(len(alignments)):
                formated = str(alignments[a][0])
                for part in xrange(1,len(alignments[a])):
                    formated += ',' + str(alignments[a][part])
                print str(a)+';'+formated
            
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
        cut_objects.append(moving.MovingObject(num, moving.TimeInterval(time_interval[0], time_interval[1]), moving.Trajectory([[row[0] for row in positions],[row[1] for row in positions]]), velocities = moving.Trajectory([[row[0] for row in velocities],[row[1] for row in velocities]]), geometry = geometry, userType = userType))
    return cut_objects

def filter_direction(objects):
    for o in reversed(xrange(len(objects))):
        if objects[o].curvilinearPositions.getXCoordinates()[-1] - objects[o].curvilinearPositions.getXCoordinates()[0] < 0:
            objects.pop(o)
    return objects
    
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

def compute_align_mid_point(align):
    s_list = []
    for a in xrange(1,len(align)):
        s_list.append(((align[a][0]-align[a-1][0])**2 + (align[a][1]-align[a-1][1])**2)**0.5)
    return sum(s_list)/2

def defName(partial_filename, ana_type, min_time, max_time):            
    name = 'Video_'+str(ana_type)+'_of_'+str(partial_filename) + '_'
    if min_time or max_time is not None:
        if min_time is None:
            name += 'for_t0_to_t'+str(max_time)
        elif max_time is None:
            name += 'for t'+str(min_time)+'_till_end'
        else:
            name += 'for t'+str(min_time)+'_to_t'+str(max_time)  
    return '{}/'+ name + '.csv'
    
def turnSqliteIntoTraj(config, min_time, max_time, fps, video_list, diagnosis, maxSpeed):
    '''process function - saves data into traj files that can be loaded by the calibration algorithm'''
    #loading user defined information from [inpxname].csv
    VissimCorridors, trafIntCorridors = define.extractVissimCorridorsFromCSV(config.path_to_inpx, config.inpx_name)
    video_infos = define.extractAlignmentsfromCSV(config.path_to_inpx, config.inpx_name)

    #keeping only video_infos that are in video_list
    if video_list != 'all':    
        for v in reversed(xrange(len(video_infos))):
            if video_infos[v].video_name not in video_list:
                video_infos.pop(v)
    
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
    all_count = []
    
    #checking for incorrect input video_names
    valid_names = [video_infos[v].video_name for v in xrange(len(video_infos))]
    for invid in video_list:
        if invid not in valid_names:
            print '\n>> No files were found for ' + str(invid) + ' <<'
    
    if video_infos == []:
        print '>> No valid videos to process, interrupting program <<'
        sys.exit()
    else:
        for i in xrange(len(video_infos)):
            print '\n >> starting work on ' + str(video_infos[i].video_name) + ' <<'
            
            objects = storage.loadTrajectoriesFromSqlite(os.path.join(config.path_to_sqlite,video_infos[i].video_name), 'object')
    
            #filtering objects by time of appearence
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
                #a.plot('k', linewidth = 2, hold = True)
                #line = np.array(a)
                #plt.plot(line[:,0], line[:,1], 'k', linewidth = 2)
            
            problems = []
            excess_speed  = []
            invert_speed  = []
            for o in objects:
                o.projectCurvilinear(alignments)           
                
                if len(o.curvilinearPositions.getXCoordinates()) > 0:
                    o.curvilinearVelocities = o.curvilinearPositions.differentiate(True)
                    
                    if diagnosis is True:
                        if np.mean(np.asarray(o.curvilinearVelocities)[:,0]) > maxSpeed:
                            excess_speed.append(o)
                        if np.mean(np.asarray(o.curvilinearVelocities)) < 0:
                            invert_speed.append(o)
                else:
                    problems.append(o)
            
            #discarding problematic objects
            for prob in reversed(problems):
                objects.pop(prob.getNum())
                
            if diagnosis is True:
                for excess in reversed(excess_speed):
                    objects.pop(excess.getNum())
                for invert in reversed(invert_speed):
                    objects.pop(invert.getNum())
                    
            #saving a figure for the run, highlighting discarded objects        
            fig = plt.figure()
               
            for o in objects:
                #object
                plt.plot(o.getXCoordinates(), o.getYCoordinates(), color = '0.75')
                #origine
                plt.plot(o.getXCoordinates()[0], o.getYCoordinates()[0], 'ro', color = '0.75')
    
            for p in problems:                
                #object
                plt.plot(p.getXCoordinates(), p.getYCoordinates(), color = 'b')
                #origine
                plt.plot(p.getXCoordinates()[0], p.getYCoordinates()[0], 'ro', color = 'b')
                #text
                plt.text(p.getXCoordinates()[0], p.getYCoordinates()[0], str(p.getNum()))
                
            for a in alignments:
                plt.plot([row[0] for row in a], [row[1] for row in a], 'k', linewidth = 2)
                plt.text(a[0][0], a[0][1], str(alignments.index(a)))

            if diagnosis is True:
                for exc in excess_speed:                
                    #object
                    plt.plot(exc.getXCoordinates(), exc.getYCoordinates(), color = 'red')
                    #origine
                    plt.plot(exc.getXCoordinates()[0], exc.getYCoordinates()[0], 'ro', color = 'red')
                    #text
                    plt.text(exc.getXCoordinates()[0], exc.getYCoordinates()[0], str(exc.getNum()))

                for inv in invert_speed:                
                    #object
                    plt.plot(inv.getXCoordinates(), inv.getYCoordinates(), color = 'g')
                    #origine
                    plt.plot(inv.getXCoordinates()[0], inv.getYCoordinates()[0], 'ro', color = 'g')
                    #text
                    plt.text(inv.getXCoordinates()[0], inv.getYCoordinates()[0], str(inv.getNum()))                           
                
                plt.savefig(os.path.join(config.path_to_inpx, 'Diagnosis of trajectories for video ' + str(video_infos[i].video_name.strip('.sqlite'))))
            else:
                plt.savefig(os.path.join(config.path_to_inpx, 'Visualisation of trajectories for video ' + str(video_infos[i].video_name.strip('.sqlite'))))
            
            plt.clf()
            plt.close(fig)
            
            if diagnosis is True:
                filename = defName(video_infos[i].video_name, 'diagnosis', min_time, max_time)
                write.writeDisgnosedReport(config.path_to_inpx, filename, video_infos[i].video_name,  config.inpx_name, min_time, max_time, maxSpeed, excess_speed, invert_speed, fps)
                
            else:
                #flow
                counts = [ 0 for c in xrange(len(alignments))]
                for o in objects:
                    counts[o.curvilinearPositions.getLanes()[0]] += 1
        
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
                            #[snappedSpline, snappedSplineLeadingPoint, snappedPoint, subsegmentDistance, S, Y] = moving.getSYfromXY(moving.Point.midPoint(lane[0], lane[1]), alignments, 0.5)
                            sorted_instants, raw_speeds = outputs.calculateInstants(objects, compute_align_mid_point(alignments[index]), index)                      
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
                all_count = list(define.merge_vectors(np.asarray(all_count),np.asarray(counts)))

    if diagnosis is True:
        pass
    else:           
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
        
        ##creating the report filename
        if len(video_infos) == 1:
            partial_filename = str(video_infos[0].video_name).strip('.sqlite')
        elif len(video_infos) > 1:
            partial_filename = str(video_infos[0].video_name).strip('.sqlite') + '_to_' + str(video_infos[-1].video_name).strip('.sqlite')

        filename = defName(partial_filename, 'analysis', min_time, max_time)
        
        ##building the other_info list to print
        other_info = [['flow:', flow],
                      ['count by lane:', all_count],
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
        write.writeRealDataReport(config.path_to_inpx, filename, video_names, config.inpx_name, min_time, max_time, [percentages,values_at_p], other_info)
        
        #dumping serialised data
        print ' == Dumping to ' +str(config.inpx_name.strip('.inpx') + '.traj')+' ==  |' + str(time.clock())
        write.write_traj(config.path_to_inpx, config.inpx_name.strip('.inpx'), opportunisticLC, mandatoryLC, flow, forward_followgap, opportunistic_LCagap, opportunistic_LCbgap, mandatory_LCagap, mandatory_LCbgap, forward_speeds)
     
    
################################ 
#        Main       
################################

def main(argv):
    time.clock()

    commands = pvc_config.commands(argparse.ArgumentParser(), 'Video')

    #process options
    min_time = commands.min_time
    max_time = commands.max_time
    fps      = commands.fps
    all_once = commands.video_all_once
    #trace options
    video_names = commands.video_names
    save        = commands.save
    loadImage   = commands.loadImage
    keep_align  = commands.keep_align

    print '== Starting work for the following network : ' + str(config.inpx_name) +' | Concatenation = True =='
    
    if commands.analysis == 'process' or commands.analysis == 'diagnose':
        
        if commands.analysis == 'diagnose':
            diagnosis = True
            maxSpeed = commands.maxSpeed/(3.6*fps)
        else:
            diagnosis = False
            maxSpeed = 0
            
        if all_once is True:
            if video_names is None:
                print '== Processing sqlite list contained in the csv file for ' + str(config.inpx_name)  +' | Concatenation = True =='
                video_list = 'all'
            else:
                print '== Processing specified sqlites for ' + str(config.inpx_name)  +' =='
                video_list = video_names[:]
                
            turnSqliteIntoTraj(config, min_time, max_time, fps, video_list, diagnosis, maxSpeed)
            
        else:
            if video_names is None:
                print '== Processing sqlite list contained in the csv file for ' + str(config.inpx_name)  +' | Concatenation = False =='
                video_list = define.extractAlignmentsfromCSV(config.path_to_inpx, config.inpx_name)
                video_list = [v.video_name for v in video_list]
            else:
                print '== Processing specified sqlites for ' + str(config.inpx_name)  +' | Concatenation = False =='
                video_list = video_names[:]
                
            for v in video_list:
                turnSqliteIntoTraj(config, min_time, max_time, fps, [v], diagnosis, maxSpeed)
                
        print ' == Processing for ' + str(config.inpx_name) + ' done <<'
        
        
    elif commands.analysis == 'trace':
        if video_names is not None:
            for v in reversed(xrange(len(video_names))):
                if not os.path.isfile(os.path.join(config.path_to_sqlite, video_names[v])):
                    video_names.pop(video_names[v])
                    print 'video " ' + str(video_names) + ' " not found'

        else:
            video_names = [f for f in os.listdir(config.path_to_sqlite) if f.endswith('.sqlite')]
            
        if video_names == []:
            print 'No valid video specified'
            return 100

        print '== Loading sqlites from ' + str(config.path_to_sqlite) +' =='
        string = video_names[0]
        for i in xrange(len(video_names)-1):
            string = string +', '+ str(video_names[i+1])
        print '== Enabling alignment drawing for the following videos: '+str(string) +' =='  

        processVideolist(config, video_names, save, loadImage, keep_align)

    else:
        return 100
       
    
if __name__ == '__main__': sys.exit(main(sys.argv))