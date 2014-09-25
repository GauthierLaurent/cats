#!/usr/bin/env python
# -*- coding: utf-8 -*-


##################
# Import Native Libraries
##################
import os, sys, time
import matplotlib.pyplot as plt
import cPickle as pickle

##################
# Import Traffic Intelligence
##################
#disabling outputs
import lib.nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import moving, storage
sys.stdout = oldstdout
#Re-enable output

##################
# Import Internal Libraries
##################
#import pcvtools
import lib.define as define
import lib.outputs as outputs
import lib.tools_config as config

################################ 
#        Load settings       
################################    
config   = config.Config('pvc.cfg')

################################ 
#        Functions       
################################
def traceAndclick(objects, n):
    '''Pour creer les alignments ou les points de calcul
       n correspond au nombre de clicks sur l'image où les coordonnées seront enregistrées
       Pour tracer les alignements, choisir n multiple de 2'''
       
    for i in range(len(objects)):
        objects[i].plot('r', withOrigin = True)
    numbers = plt.ginput(n)
    
    return numbers

def processVideolist(config, video_names, n):
    for video_name in video_names:
        objects = storage.loadTrajectoriesFromSqlite(os.path.join(config.path_to_sqlite, video_name), 'object')
        points = traceAndclick(objects, n)
        print video_name,' : ', points

def turnSqliteIntoTraj(config):
    
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
        objects = storage.loadTrajectoriesFromSqlite(os.path.join(config.path.sqlite,video_infos[i].video_name), 'object')
        
        alignments = []
        for a in xrange(len(video_infos[i].alignments)):
            alignments.append(moving.Trajectory.fromPointList(video_infos[i].alignments[a].point_list))
                                   
        #Assignments of alignments
        for a in alignments:
            a.computeCumulativeDistances()
            a.plot('k', linewidth = 2, hold = True)
            #line = np.array(a)
            #plt.plot(line[:,0], line[:,1], 'k', linewidth = 2)
        
        for o in objects:
            o.projectCurvilinear(alignments)
            o.curvilinearVelocities = o.curvilinearPositions.differentiate(True)
            
        #Calculation of stats stuff
        to_eval = []
        for j in xrange(len(trafIntCorridors)):
            to_eval += trafIntCorridors[j].to_eval
        
        #flow
        onevid_flow = len(objects)
        
        #lane change count by type        
        oppObjDict, manObjDict, laneDict = outputs.laneChange(objects,trafIntCorridors)
        onevid_opportunisticLC = sum([len(oppObjDict[i]) for i in oppObjDict])
        onevid_mandatoryLC = sum([len(manObjDict[i]) for i in manObjDict])
        print ' == Lane change compilation done ==  |' + str(time.clock())
                    
        #Forward gaps and speeds calculations
        onevid_forward_gaps = []
        onevid_forward_speeds = []        
        for index,lane in enumerate(alignments):
            [snappedSpline, snappedSplineLeadingPoint, snappedPoint, subsegmentDistance, S, Y] = moving.getSYfromXY(moving.Point.midPoint(lane[0], lane[1]), alignments, 0.5)
        
            if index in to_eval:
                raw_gaps, raw_speeds = outputs.forwardGaps(objects, S, index)
                onevid_forward_gaps += list(raw_gaps)
                onevid_forward_speeds += list(raw_speeds)
            print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(alignments)) + ' ==  |' + str(time.clock())
        
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
    
    #dumping serialised data
    with open(os.path.join(config.path_to_inpx, config.inpx_name.strip('.inpx') + '.traj'), 'wb') as output:
        print ' == Dumping to config. ' +str(config.inpx_name.strip('.inpx') + '.traj')+' ==  |' + str(time.clock())        
        pickle.dump(define.version, output, protocol=2)
        pickle.dump(opportunisticLC, output, protocol=2)
        pickle.dump(mandatoryLC, output, protocol=2)
        pickle.dump(flow, output, protocol=2)
        pickle.dump(forward_followgap, output, protocol=2)
        pickle.dump(opportunistic_LCagap, output, protocol=2)
        pickle.dump(opportunistic_LCbgap, output, protocol=2)
        pickle.dump(mandatory_LCagap, output, protocol=2)
        pickle.dump(mandatory_LCbgap, output, protocol=2)
        pickle.dump(forward_speeds, output, protocol=2)

################################ 
#        Main       
################################
time.clock()
import pdb;pdb.set_trace()
print '== Starting work for the following network : ' + str(config.inpx_name) +' =='
if len(sys.argv) >= 2:
    mode = sys.argv[1]
else:
    mode = 'process'
    
if mode == 'process':
    print '== Processing sqlite list contained in the csv file for ' + str(config.inpx_name)  +' =='
    turnSqliteIntoTraj(config)
else:
    if len(sys.argv) >= 4:
        video_names = sys.argv[3:]
    else:
        video_names = [f for f in os.listdir(config.path_to_sqlite) if f.endswith('.sqlite')]
        print '== Loading sqlites from ' + str(config.path_to_sqlite) +' =='
    string = video_names[0]
    for i in xrange(len(video_names)-1):
        string = string +', '+ str(video_names[i+1])
    print '== Enabling alignment drawing for the following videos: '+str(string) +' =='  
    n = sys.argv[2]    
    processVideolist(config, video_names, n)