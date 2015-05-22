#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
call exemples:
   to draw aligments on world image: -s -v GP130001.sqlite
   to draw many aligments:           -s -k
   to process all sqlite:            -M 9000 -g 30 -a process
   to process specified (2):         -M 9000 -g 30 -a process -v GP130001.sqlite GP020001.sqlite
   to proocess all individually:     -M 9000 -g 30 -a process -o
   to diagnose a single video:       -M 9000 -g 30 -a diagnose -d 130 -v GP130001.sqlite
   load old data, draw and process:  -l -M 9000 -g 30 -a both -v GP100001.sqlite
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
import pvc_write     as write
import pvc_outputs   as outputs
import pvc_configure as configure
import pvc_mathTools as mathTools
import pvc_csvParse  as csvParse

################################ 
#        Load settings       
################################    
config   = configure.Config('pvc.cfg')
    
################################ 
#        Trace functions       
################################
def traceAndclick(objects, loadOld = False, pixelUnitRatio = 1, imgPath = None):
    '''Pops-up the drawing interface and converts the results to Traffic Intelligence point
       list format for futur conversion into Traffic Intelligence alignement data'''

    fig = plt.figure()
    
    if imgPath is not None:
        img = plt.imread(imgPath)
        plt.imshow(img)

    if loadOld is not False:
        video_infos = csvParse.extractAlignmentsfromCSV(config.path_to_inpx, config.inpx_name)
        
        for v in reversed(xrange(len(video_infos))):
            if video_infos[v].video_name != loadOld:
                video_infos.pop(v)
                
        if video_infos == []:
            loadOld = False
        
        else:
            print '== Loading old alignment information from csv ==' 
            old_alignments = []
            for old_a in xrange(len(video_infos[0].alignments)):
                old_alignments.append(moving.Trajectory.fromPointList(video_infos[0].alignments[old_a].point_list))

            #Assignments of alignments
            for old_a in old_alignments:
                old_a.computeCumulativeDistances()
                
            for o in objects:
                o.projectCurvilinear(old_alignments)
                
            colors = [0.5 + i*(0.75-0.5)/(len(old_alignments)-1) for i in xrange(len(old_alignments))]

    for i in range(len(objects)):
        if loadOld is not False:
            color = str(colors[objects[i].curvilinearPositions.getLanes()[0]])
        else:
            color = '0.75'
        
        if imgPath is not None:
            objects[i].plotOnWorldImage(float(pixelUnitRatio), withOrigin = True, color = color)                        
        else:
            #object
            plt.plot(objects[i].getXCoordinates(), objects[i].getYCoordinates(), color = color)
            #origine
            plt.plot(objects[i].getXCoordinates()[0], objects[i].getYCoordinates()[0], 'ro', color = color)
            
        if loadOld is not False:
            for old_a in old_alignments:
                if imgPath is not None:
                    old_a.plotOnWorldImage(float(pixelUnitRatio), withOrigin = False, color = '0.25', linestyle = '--')
                else:
                    plt.plot([row[0] for row in old_a], [row[1] for row in old_a], color = '0.25', linestyle = '--')
                    plt.text(old_a[0][0], old_a[0][1], str(old_alignments.index(old_a)))
    
    alignments = write.drawAlign(fig)
    plt.close()

    #transforming to moving.Point() form and taking out double points
    Alignments = []
    for align in alignments:
        RevPoints = []
        for p in reversed(align):
            if align.count(p) > 1:
                align.pop(align.index(p))
            else:
                RevPoints.append(moving.Point(p[0]/pixelUnitRatio,p[1]/pixelUnitRatio))
        Points = []
        for i in reversed(xrange(len(RevPoints))):
            Points.append(RevPoints[i])
        Alignments.append(Points)
        
    return Alignments

def processVideolist(config, video_names, save, loadOld, loadImage, keep_align):
        
    for v in xrange(len(video_names)):
        
        if loadOld is True:
            to_load = video_names[v]
        else:
            to_load = False
        
        if keep_align is True and v > 0:
            pass
        else:
            objects = storage.loadTrajectoriesFromSqlite(os.path.join(config.path_to_sqlite, video_names[v]), 'object')
            
            if loadImage:
                points = traceAndclick(objects, to_load, config.pixel_to_unit_ratio, os.path.join(config.path_to_image, config.image_name))
            else:
                points = traceAndclick(objects, to_load)
                        
            alignments = []
            for p in points:
                alignments.append(moving.Trajectory.fromPointList(p))         
            
            print ''
            for a in alignments:
                print a
            print ''
            
        if save is True:
            print '>> Saving data for '+str(video_names[v])+' to the CSV file'
            csvParse.writeAlignToCSV(config.path_to_csv, config.inpx_name, video_names[v], alignments)
            print '>> Saving successfull'
        else:
            print '>> No-Saving option chosen, here are the data for manual copy-pasting:'
            print video_names[v]
            for a in xrange(len(alignments)):
                formated = str(alignments[a][0])
                for part in xrange(1,len(alignments[a])):
                    formated += ',' + str(alignments[a][part])
                print str(a)+';'+formated
                
        return
            
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

def timeName(min_time, max_time):
    if min_time or max_time is not None:
        if min_time is None:
            name = 't0_to_t'+str(max_time)
        elif max_time is None:
            name = 't'+str(min_time)+'_till_end'
        else:
            name = 't'+str(min_time)+'_to_t'+str(max_time)
    else:
        name = 'full_lenght'
    return name
    
def defName(partial_filename, ana_type, min_time, max_time):            
    name = 'Video_'+str(ana_type)+'_of_'+str(partial_filename) + '_for_' + timeName(min_time, max_time) 
    return '{}/'+ name + '.csv'
    
def turnSqliteIntoTraj(config, min_time, max_time, fps, video_list, diagnosis, maxSpeed, commands):
    '''process function - saves data into traj files that can be loaded by the calibration algorithm'''
    #loading user defined information from [inpxname].csv
    trafIntCorridors = csvParse.extractCorridorsFromCSV(config.path_to_inpx, config.inpx_name, 'trafint')
    video_infos = csvParse.extractAlignmentsfromCSV(config.path_to_inpx, config.inpx_name)
    
    #keeping only video_infos that are in video_list
    if video_list != 'all':    
        for v in reversed(xrange(len(video_infos))):
            if video_infos[v].video_name not in video_list:
                video_infos.pop(v)

    #variable declaration
    Outputs_list = []
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
                    problems.append(objects.index(o))
            
            #discarding problematic objects
            for prob in reversed(problems):
                objects.pop(prob)
            
            
            if diagnosis is True:
                numlist = [o.getNum() for o in objects]
                if len(excess_speed) > 0:
                    for excess in reversed(excess_speed):
                        objects.pop(numlist.index(excess.getNum()))
                    numlist = [o.getNum() for o in objects]         #refresh indexes for invert poping
                    
                for invert in reversed(invert_speed):
                    objects.pop(numlist.index(invert.getNum()))
                    
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
                Outputs = outputs.Derived_data()                
                
                #flow
                counts = [ 0 for c in xrange(len(alignments))]
                for o in objects:
                    counts[o.curvilinearPositions.getLanes()[0]] += 1
        
                Outputs.addSingleOutput('flow', len(objects), video_infos[i].video_name)
                for c in xrange(len(counts)):                
                    Outputs.editLaneCount(c, counts[c])
                
                #lane change count by type        
                oppObjDict, manObjDict, laneDict = outputs.laneChange(objects,trafIntCorridors)
                Outputs.addSingleOutput('oppLCcount', sum([len(oppObjDict[j]) for j in oppObjDict]), video_infos[i].video_name)
                Outputs.addSingleOutput('manLCcount', sum([len(manObjDict[j]) for j in manObjDict]), video_infos[i].video_name)
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
                            sorted_instants, raw_speeds = outputs.calculateInstants(objects, 0.9*alignments[index].getCumulativeDistance(-1), index)                      
                            raw_gaps = outputs.calculateGaps(sorted_instants)
                            onevid_forward_gaps += list(raw_gaps)
                            onevid_forward_speeds += list(raw_speeds)
                            graph_inst += sorted_instants[:-1]
                            graph_gaps += list(raw_gaps)
                            
                            print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(alignments)) + ' ==  |' + str(time.clock())# + ' | ' + str(len(raw_gaps))
                   
                    #trace graph: flow vs time during video
                    sorted_graph_inst, sorted_graph_gaps = mathTools.sort2lists(graph_inst,graph_gaps)
                    if len(sorted_graph_inst) > 0:
                        write.plot_qt(sorted_graph_inst, sorted_graph_gaps, config.path_to_inpx, video_infos[i].video_name, trafIntCorridors[c].name, fps, min_time, max_time)
                                
                #mandatory lane change gaps
                onevid_man_agaps, onevid_man_bgaps = outputs.laneChangeGaps(manObjDict, laneDict, objects)
                print ' == Mandatory lane change gaps calculation done  ==  |' + str(time.clock())
                
                #opportunistic lane change gaps
                onevid_opp_agaps, onevid_opp_bgaps = outputs.laneChangeGaps(oppObjDict, laneDict, objects)
                print ' == Opportunistic lane change gaps calculation done ==  |' + str(time.clock())
            
                #variable concatenation
                Outputs.addSingleOutput('forFMgap',  onevid_forward_gaps, video_infos[i].video_name)
                Outputs.addSingleOutput('forSpeeds', onevid_forward_speeds, video_infos[i].video_name)
                Outputs.addSingleOutput('manLCagap', list(onevid_man_agaps), video_infos[i].video_name)
                Outputs.addSingleOutput('manLCbgap', list(onevid_man_bgaps), video_infos[i].video_name)
                Outputs.addSingleOutput('oppLCagap', list(onevid_opp_agaps), video_infos[i].video_name)
                Outputs.addSingleOutput('oppLCbgap', list(onevid_opp_bgaps), video_infos[i].video_name)
                all_count = list(mathTools.merge_vectors(np.asarray(all_count),np.asarray(counts)))

                Outputs_list.append(Outputs)

    if diagnosis is True:
        pass
    else:
        print '\n' 
        if commands.video_all_once:
            for k in reversed(xrange(1,len(Outputs_list))):
                outputs.Derived_data.concat(Outputs[0],Outputs_list[k])
                Outputs_list.pop(k)
    
        for Outputs in Outputs_list:
            #from forward TIV, calculate flow:
            raw_flow_dist = []
            for dist in Outputs.forFMgap.distributions:
                raw_flow_dist.append(list(3600*fps/np.asarray(dist.raw)))    
            flowDist = outputs.Stats(raw_flow_dist)
        
            #putting the calculated information into a report file
            ##calculating 13 usefull centiles for tracing speeds in vissim
            percentages = []
            values_at_p = []
            for i in [0,2.5,5]+range(10,31,10)+[50]+range(70,91,10)+[95, 97.5,100]:
                percentages.append(i)        
                values_at_p.append( np.percentile(Outputs.forSpeeds.cumul_all.raw,i) )
                
            ##building the video_name list
            if commands.video_all_once: 
                video_names = ''
                for i in xrange(len(Outputs.forFMgap.distributions)):
                    if i == len(Outputs.forFMgap.distributions) -1:
                        video_names += Outputs.forFMgap.distributions[i].filename
                    else:                    
                        video_names += Outputs.forFMgap.distributions[i].filename + ', '
            else:
                video_names = Outputs.forFMgap.distributions[0].filename
            
            ##creating the report filename
            if commands.video_all_once:
                partial_filename = str(Outputs.forFMgap.distributions[0].filename).strip('.sqlite')
            else:
                partial_filename = str(Outputs.forFMgap.distributions[0].filename).strip('.sqlite') + '_to_' + str(Outputs.forFMgap.distributions[-1].filename).strip('.sqlite')
            
            ##building the other_info list to print
            other_info = [['flow:', Outputs.flow.sum],
                          ['count by lane:', Outputs.getLaneCounts()],
                          ['number of opportunistic lane changes:', Outputs.oppLCcount.sum],
                          ['number of mandatory lane changes:', Outputs.manLCcount.sum],
                          ['variable_name','mean','25th centile','median','75th centile','standard deviation'],
                          ['Forward follow gaps:',          Outputs.forFMgap.cumul_all.mean,   Outputs.forFMgap.cumul_all.firstQuart,   Outputs.forFMgap.cumul_all.median,   Outputs.forFMgap.cumul_all.thirdQuart,   Outputs.forFMgap.cumul_all.std],                                  
                          ['Flow distribution (3600/gap):', flowDist.cumul_all.mean,           flowDist.cumul_all.firstQuart,           flowDist.cumul_all.median,           flowDist.cumul_all.thirdQuart,           flowDist.cumul_all.std],
                          ['Opportunistic gaps (after):',   Outputs.oppLCagap.cumul_all.mean,  Outputs.oppLCagap.cumul_all.firstQuart,  Outputs.oppLCagap.cumul_all.median,  Outputs.oppLCagap.cumul_all.thirdQuart,  Outputs.oppLCagap.cumul_all.std],
                          ['Opportunistic gaps (before):',  Outputs.oppLCbgap.cumul_all.mean,  Outputs.oppLCbgap.cumul_all.firstQuart,  Outputs.oppLCbgap.cumul_all.median,  Outputs.oppLCbgap.cumul_all.thirdQuart,  Outputs.oppLCbgap.cumul_all.std],
                          ['Mandatory gaps (after):',       Outputs.manLCagap.cumul_all.mean,  Outputs.manLCagap.cumul_all.firstQuart,  Outputs.manLCagap.cumul_all.median,  Outputs.manLCagap.cumul_all.thirdQuart,  Outputs.manLCagap.cumul_all.std],
                          ['Mandatory gaps (before):',      Outputs.manLCbgap.cumul_all.mean,  Outputs.manLCbgap.cumul_all.firstQuart,  Outputs.manLCbgap.cumul_all.median,  Outputs.manLCbgap.cumul_all.thirdQuart,  Outputs.manLCbgap.cumul_all.std],
                          ['Speeds:',                       Outputs.forSpeeds.cumul_all.mean,  Outputs.forSpeeds.cumul_all.firstQuart,  Outputs.forSpeeds.cumul_all.median,  Outputs.forSpeeds.cumul_all.thirdQuart,  Outputs.forSpeeds.cumul_all.std],                 
                         ]
            ##generating the output    
            write.writeRealDataReport(config.path_to_inpx, defName(partial_filename, 'analysis', min_time, max_time), video_names, config.inpx_name, min_time, max_time, [percentages,values_at_p], other_info)
            
            print 'count by lane:', Outputs.getLaneCounts(), Outputs.getLanePercent()          
            
            #dumping serialised data
            print ' == Dumping to ' + partial_filename + '_' + timeName(min_time, max_time) + '.traj'+' ==  |' + str(time.clock())
            write.write_traj(config.path_to_inpx, partial_filename + '_' + timeName(min_time, max_time), Outputs)
     
    
################################ 
#        Main       
################################

def main(argv):
    time.clock()

    commands = configure.commands(argparse.ArgumentParser(), 'Video')

    #process options
    min_time = commands.min_time
    max_time = commands.max_time
    fps      = commands.fps
    #trace options
    video_names = commands.video_names
    save        = commands.save
    loadImage   = commands.loadImage
    loadOld     = commands.loadOld
    keep_align  = commands.keep_align

    print '== Starting work for the following network : ' + str(config.inpx_name) +' | Concatenation = True =='        
        
    if commands.analysis == 'trace' or (commands.analysis == 'both' and len(commands.video_names) == 1):
        if commands.analysis == 'both':
            save = True
            
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

        processVideolist(config, video_names, save, loadOld, loadImage, keep_align)
        
    if commands.analysis == 'process' or commands.analysis == 'diagnose' or (commands.analysis == 'both' and len(commands.video_names) == 1):
        
        if commands.analysis == 'both':
            commands.analysis = 'process'
        
        if commands.analysis == 'diagnose':
            diagnosis = True
            maxSpeed = commands.maxSpeed/(3.6*fps)
        else:
            diagnosis = False
            maxSpeed = 0
            
        if video_names is None:
            if commands.video_all_once is True:
                print '== Processing sqlite list contained in the csv file for ' + str(config.inpx_name)  +' | Concatenation = False =='
            else:
                print '== Processing sqlite list contained in the csv file for ' + str(config.inpx_name)  +' | Concatenation = True =='
            video_list = 'all'
        else:
            if commands.video_all_once is True:
                print '== Processing specified sqlites for ' + str(config.inpx_name)  +' | Concatenation = True =='
            else:
                print '== Processing sqlite list contained in the csv file for ' + str(config.inpx_name)  +' | Concatenation = False =='
            video_list = video_names[:]
   
        turnSqliteIntoTraj(config, min_time, max_time, fps, video_list, diagnosis, maxSpeed, commands)
                
        print '\n == Processing for ' + str(config.inpx_name) + ' done <<'
       
    
if __name__ == '__main__': sys.exit(main(sys.argv))