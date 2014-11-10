# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:38:05 2014

@author: Laurent
"""
##################
# Import Native Libraries
##################

import scipy, os, sys
import numpy as np
import random, time

##################
# Import Traffic Intelligence
##################
#disabling outputs
import nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import storage as TraffIntStorage
sys.stdout = oldstdout #Re-enable output

##################
# Output treatment tools
##################

class sublvl:
    def __init__(self, raw):
        if raw != []:
            cumul,nlist,mean,firstQuart,median,thirdQuart,var  = dist(raw)
            self.raw        = raw        
            self.value      = nlist
            self.cumul      = cumul
            self.mean       = mean
            self.firstQuart = firstQuart
            self.median     = median
            self.thirdQuart = thirdQuart
            self.var        = var
            self.std        = var**0.5
        else:
            self.raw        = []       
            self.value      = None
            self.cumul      = None
            self.mean       = None
            self.firstQuart = None
            self.median     = None
            self.thirdQuart = None
            self.var        = None
            self.std        = None
            
class stats:
    def __init__(self, raw):
        self.distributions  = []
        allvalues = []
        if raw != []:
            for l in raw:
                for m in l:
                    allvalues.append(m)
                self.distributions.append(sublvl(l))
            self.cumul_all = sublvl(allvalues)                                
        else:
            self.cumul_all = sublvl(raw)

def calculateInstants(objects, s, lane):
    instants = []
    speeds = []
    for o in objects:
        t = o.curvilinearPositions.getIntersections(s, lane)
        if t != []:
            instants.append(o.getFirstInstant()+t[0])
            speeds.append(o.curvilinearVelocities.getXCoordinates()[int(np.floor(t[0]))])
    instants.sort()          
    return instants, speeds

def calculateGaps(sorted_instants):
    x = np.asarray(sorted_instants)    
    return x[1:]-x[:-1]
    
def forwardGaps(objects, s, lane):
    '''Calculates all gaps on a given lane and for a given point s'''
    
    instants, speeds = calculateInstants(objects, s, lane)
    gaps = calculateGaps(instants)
    
    return gaps, speeds

def laneChangeGaps(listDict, laneDict, objects):
    '''Determines the width of lane change gaps for a list of objects who make lane changes
        agaps represent the gap present after the insertion of the lane changing vehicule
        bgaps reprensent the gap present before the insertion of the lane changing vehicule'''
    
    x = []  #agaps construction variable
    y = []  #bgaps construction variable
    for obj in listDict.keys():
        
        for change in range(len(listDict[obj])):
            lane = listDict[obj][change][1]                                                     #Dict[i][1] = lane after lane change
            stepNum = objects[obj].getFirstInstant()+listDict[obj][change][2]                   #Dict[i][2] = position of the lane change in the objects list 
            s = objects[obj].curvilinearPositions.getXCoordinates()[listDict[obj][change][2]]
				
            #determining the gap
            instants = []
            for candidate in laneDict[lane]:
                if candidate != obj:
                    t = objects[candidate].curvilinearPositions.getIntersections(s, lane)
                    if t != []:
                        #if objects[candidate].getFirstInstant()+t[0] > stepNum:
                        instants.append(objects[candidate].getFirstInstant()+t[0] - stepNum)
	
            instants.sort() 
            if instants != []: 
                for i in range(len(instants)):
                    if instants[i] > 0:
                        x.append(instants[i])
                        y.append(instants[i] - instants[i -1])
                        
                        break

    agaps = np.asarray(x)
    bgaps = np.asarray(y)

    return agaps, bgaps

def appendDicts(candidate, dictionnary, position_before, position_after, frame_after):
    '''adds {candidate: position_before, position_after, frame_after} to dictionnary'''
    if candidate not in dictionnary:       
        dictionnary[candidate] = [[position_before,position_after,frame_after]]
    else:
        dictionnary[candidate].append([position_before,position_after,frame_after])
        
    return dictionnary
    
def laneChange(objects, corridors):
    #Dictionaries    
    oppObjDict = {}
    manObjDict = {}
    laneDict = {}
    
    to_eval = []
    for j in xrange(len(corridors)):
        to_eval += corridors[j].to_eval
                
    for o in range(len(objects)):
        #building the lane dictionnary
        for i in set(objects[o].curvilinearPositions.lanes):
            if i not in laneDict: laneDict[i] = []
            if o not in laneDict[i]: laneDict[i].append(o)         
        
        #Vissim data
        if isinstance(objects[o].curvilinearPositions.lanes[0],str):
            first_appeareance = None
            last_appeareance = None
            for i in xrange(len(corridors)):       
                if int(objects[o].curvilinearPositions.lanes[0].split('_')[0]) in corridors[i].link_list: first_appeareance = i
                if int(objects[o].curvilinearPositions.lanes[-1].split('_')[0]) in corridors[i].link_list: last_appeareance = i
                    
            #if the object stays in the same corridors over the whole trajectory --> all lane changes are opportunistic lane change        
            if first_appeareance == last_appeareance:
                for pos in range(len(objects[o].curvilinearPositions.lanes) -1):
                    #keeping only the evaluated links                            
                    if int(objects[o].curvilinearPositions.lanes[pos].split('_')[0]) in to_eval:
                        #eliminating link interface change
                        if objects[o].curvilinearPositions.lanes[pos].split('_')[0] == objects[o].curvilinearPositions.lanes[pos + 1].split('_')[0]:
                            if objects[o].curvilinearPositions.lanes[pos].split('_')[1] != objects[o].curvilinearPositions.lanes[pos + 1].split('_')[1]:
                                oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)                        
                    
            #otherwise, we need to investigate more
            else:      
                for pos in range(len(objects[o].curvilinearPositions.lanes) -1):                  
                    #keeping only the evaluated links                            
                    if int(objects[o].curvilinearPositions.lanes[pos].split('_')[0]) in to_eval:                    
                        #if link is not the same
                        if objects[o].curvilinearPositions.lanes[pos].split('_')[0] != objects[o].curvilinearPositions.lanes[pos + 1].split('_')[0]:
                            start = None
                            end = None
                            #Verify if both links are in the same corridor
                            for i in xrange(len(corridors)):
                                if int(objects[o].curvilinearPositions.lanes[pos].split('_')[0]) in corridors[i].link_list: start = i
                                if int(objects[o].curvilinearPositions.lanes[pos +1].split('_')[0]) in corridors[i].link_list: end = i
        
                            if start != end:    #if not --> mandatory lane change
                                manObjDict = appendDicts(o, manObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)

                        #if link is the same
                        else:
                            #if lane is not the same --> opportunistic lane change
                            if objects[o].curvilinearPositions.lanes[pos].split('_')[1] != objects[o].curvilinearPositions.lanes[pos + 1].split('_')[1]:
                                
                                #finding the exit direction of corridor the vehicule is on
                                direction = None
                                for i in xrange(len(corridors)):
                                    if int(objects[o].curvilinearPositions.lanes[0].split('_')[0]) in corridors[i].link_list: direction = corridors[i].direction
    
                                if direction == 'r':
                                    #if the link between the corridors is to the right, an increasing lane number is opportunistic
                                    if objects[o].curvilinearPositions.lanes[pos].split('_')[1] < objects[o].curvilinearPositions.lanes[pos +1].split('_')[1]:
                                        oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
                                    else:
                                        manObjDict = appendDicts(o, manObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
                                                
                                #if the link between the corridors is to the left, a decreasing lane number is opportunistic
                                else:
                                    if objects[o].curvilinearPositions.lanes[pos].split('_')[1] > objects[o].curvilinearPositions.lanes[pos +1].split('_')[1]:
                                        oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
                                    else:
                                        manObjDict = appendDicts(o, manObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)

        #Traffic Intelligence data
        else:                        
            first_appeareance = None
            last_appeareance = None
            for i in xrange(len(corridors)):            
                if objects[o].curvilinearPositions.lanes[0] in corridors[i].link_list: first_appeareance = i
                if objects[o].curvilinearPositions.lanes[-1] in corridors[i].link_list: last_appeareance = i
                    
            #if the object stays in the same corridors over the whole trajectory --> all lane changes are opportunistic lane change        
            if first_appeareance == last_appeareance:
                for pos in range(len(objects[o].curvilinearPositions.lanes) -1):
                    #keeping only the evaluated links                            
                    if objects[o].curvilinearPositions.lanes[pos] in to_eval:
                        if objects[o].curvilinearPositions.lanes[pos] != objects[o].curvilinearPositions.lanes[pos + 1]:
                            oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)                        
                        
            else:

                for pos in range(len(objects[o].curvilinearPositions.lanes) -1):
                    #keeping only the evaluated links                            
                    if objects[o].curvilinearPositions.lanes[pos] in to_eval:                                            
                        #if alignment is not the same
                        if objects[o].curvilinearPositions.lanes[pos] != objects[o].curvilinearPositions.lanes[pos + 1]:
                            start = None
                            end = None
                            #Verify if both alignments are in the same corridor
                            for i in xrange(len(corridors)):
                                if objects[o].curvilinearPositions.lanes[pos] in corridors[i].link_list: start = i
                                if objects[o].curvilinearPositions.lanes[pos +1] in corridors[i].link_list: end = i
                            if start != end:    #If not --> mandatory lane change
                                manObjDict = appendDicts(o, manObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
    
                            else:
                                #At this point, the convention the store lane informations in the video analysis script
                                #Lane numbering MUST start with 0 as the right lane and increment towards the left lane
                                
                                direction = None
                                for i in xrange(len(corridors)):
                                    if objects[o].curvilinearPositions.lanes[0] in corridors[i].link_list: direction = corridors[i].direction
    
                                if direction == 'r':
                                    #if the link between the corridors is to the right, an increasing lane number is opportunistic
                                    if objects[o].curvilinearPositions.lanes[pos] < objects[o].curvilinearPositions.lanes[pos +1]:
                                        oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
                                    else:
                                        manObjDict = appendDicts(o, manObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
                                                
                                #if the link between the corridors is to the left, a decreasing lane number is opportunistic
                                else:
                                    if objects[o].curvilinearPositions.lanes[pos] > objects[o].curvilinearPositions.lanes[pos +1]:
                                        oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
                                    else:
                                        manObjDict = appendDicts(o, manObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)
    
    return oppObjDict, manObjDict, laneDict
    
def dist(x):
    xx = np.array(x)
    nlist = np.unique(xx)
    l = float(len(x))
    if len(nlist)==len(x):
        stats = [1./l]*len(x)
    else:
        stats = [np.sum(xx==i)/l for i in nlist]
    cumul = np.cumsum(stats)
    mean = np.mean(xx)
    firstQuart = np.percentile(xx,25)
    median = np.median(xx)
    thirdQuart = np.percentile(xx,75)
    var = np.var(xx)      
    return cumul,nlist,mean,firstQuart,median,thirdQuart,var
    
def computeMeanfromOld(data,old_num):
    '''data must be provided as a list: [old_mean, a,b,c,...]'''
    new_mean = (data[0] * old_num + sum(data[1:]) ) / ( old_num + len(data[1:]) )                
    return new_mean

def treatVissimOutputs(files, inputs):
    '''Treat outputs in the given folder 
       If Old_data exists, it must be transfered as the raw list'''
    
    folderpath                 = inputs[0]
    simulationStepsPerTimeUnit = inputs[1]
    warmUpTime                 = inputs[2]
    verbose                    = inputs[3]
    corridors                  = inputs[4]
    
    if len(inputs) == 6:
        old_data = inputs[5]
    else:
        old_data = []
    
    
    if old_data == []:
        raw_opportunisticLC = []
        raw_mandatoryLC     = [] 
        raw_flow            = []
        raw_forward_gaps    = []
        raw_opp_LC_agaps    = []
        raw_opp_LC_bgaps    = []
        raw_man_LC_agaps    = []
        raw_man_LC_bgaps    = []
        raw_forward_speeds  = []
    else:
        raw_opportunisticLC = old_data[0]
        raw_mandatoryLC     = old_data[1] 
        raw_flow            = old_data[2]
        raw_forward_gaps    = old_data[3]
        raw_opp_LC_agaps    = old_data[4]
        raw_opp_LC_bgaps    = old_data[5]
        raw_man_LC_agaps    = old_data[6]
        raw_man_LC_bgaps    = old_data[7]
        old_num             = old_data[8]   #Number of previous data. Is used to calculate the new means (old_mean*N+new_stuff)/(N+nbr_new_stuff)
        raw_forward_speeds  = old_data[9]

    if files is not None:    #this was implemented to be able to concatenate data received by a multiprocessing run
        for filename in files:
            if verbose:
                print ' === Starting calculations for ' + filename + ' ===  |'    
            objects = TraffIntStorage.loadTrajectoriesFromVissimFile(os.path.join(folderpath,filename), simulationStepsPerTimeUnit, nObjects = -1, warmUpLastInstant = warmUpTime * simulationStepsPerTimeUnit)
            raw_flow.append(len(objects))
            
            #lane building block
            to_eval = []
            for j in xrange(len(corridors)):
                to_eval += corridors[j].to_eval
   
            lanes = {}
            for o in objects:
                o.curvilinearVelocities = o.curvilinearPositions.differentiate(True)
                for i in xrange(len(o.curvilinearPositions.lanes)):
                    p = o.curvilinearPositions[i]
                    lane = p[2]
                    s = p[0]
                    if int(lane.split('_')[0]) in to_eval:
                        if lane not in lanes:
                            lanes[lane] = [s, s]
                        else:
                            if s < lanes[str(lane)][0]:
                                lanes[str(lane)][0] = s
                            elif s > lanes[str(lane)][1]:
                                lanes[str(lane)][1] = s
    
            #lane change count by type        
            oppObjDict, manObjDict, laneDict = laneChange(objects,corridors)
               
            if verbose:
                print ' == Lane change compilation done ==  |' + str(time.clock())
            raw_opportunisticLC.append(sum([len(oppObjDict[i]) for i in oppObjDict]))
            raw_mandatoryLC.append(sum([len(manObjDict[i]) for i in manObjDict]))
            
            #forward gap analysis
            temp_raw_forward_gaps = []
            temp_raw_speeds = []
            for index,lane in enumerate(lanes):  
                s = (lanes[str(lane)][0]+lanes[str(lane)][1])/2
                raw_gaps, raw_speeds = forwardGaps(objects, s, lane)
                if raw_gaps != []: temp_raw_forward_gaps += list(raw_gaps)
                if raw_speeds != []: temp_raw_speeds += list(raw_speeds)    
                if verbose:
                    print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(lanes)) + ' ==  |' + str(time.clock())
            if temp_raw_forward_gaps != []:
                raw_forward_gaps.append(temp_raw_forward_gaps)
                raw_forward_speeds.append(temp_raw_speeds)
                
            #mandatory lane change gaps
            agaps, bgaps = laneChangeGaps(manObjDict, laneDict, objects)
            if agaps.any(): raw_man_LC_agaps.append(agaps)
            if bgaps.any(): raw_man_LC_bgaps.append(bgaps)
            if verbose:
                print ' == Mandatory lane change gaps calculation done  ==  |' + str(time.clock())

            #opportunistic lane change gaps
            agaps, bgaps = laneChangeGaps(oppObjDict, laneDict, objects)
            if agaps.any(): raw_opp_LC_agaps.append(agaps)
            if bgaps.any(): raw_opp_LC_bgaps.append(bgaps)
            if verbose:
                print ' == Opportunistic lane change gaps calculation done ==  |' + str(time.clock())
                 
                print ' === Calculations for ' + filename + ' done ===  |' + str(time.clock()) + '\n'

    '''
    write.writeListToCSV(raw_forward_gaps, './raw_forward_gaps.csv')
    write.writeListToCSV(raw_opp_LC_agaps, './raw_opp_LC_agaps.csv')
    write.writeListToCSV(raw_opp_LC_agaps, './raw_opp_LC_bgaps.csv')
    write.writeListToCSV(raw_man_LC_agaps, './raw_man_LC_agaps.csv')
    write.writeListToCSV(raw_man_LC_bgaps, './raw_man_LC_bgaps.csv')
    '''
               
    #Treating raw outputs to compute means
    if raw_opportunisticLC != []:
        if old_data == []:
            mean_opportunisticLC = scipy.mean(raw_opportunisticLC)
        else:
            mean_opportunisticLC = computeMeanfromOld(raw_opportunisticLC,old_num)
    else:
        mean_opportunisticLC = 0
    
    if raw_mandatoryLC != []:
        if old_data == []:
            mean_mandatoryLC = scipy.mean(raw_mandatoryLC)

        else:
            mean_mandatoryLC = computeMeanfromOld(raw_mandatoryLC,old_num)
            
    else:
        mean_mandatoryLC = 0
    
    if raw_flow != []:
        if old_data == []:
            mean_flow = scipy.mean(raw_flow)
        else:
            mean_flow = computeMeanfromOld(raw_flow,old_num)
    else:
        mean_flow = 0
    

    forward_followgap = stats(raw_forward_gaps)
    opportunistic_LCagap = stats(raw_opp_LC_agaps)
    opportunistic_LCbgap = stats(raw_opp_LC_bgaps)
    mandatory_LCagap = stats(raw_man_LC_agaps)
    mandatory_LCbgap = stats(raw_man_LC_bgaps)
    forward_speeds = stats(raw_forward_speeds)
    
    return mean_flow, mean_opportunisticLC, mean_mandatoryLC, forward_followgap, opportunistic_LCagap, opportunistic_LCbgap,  mandatory_LCagap,  mandatory_LCbgap, forward_speeds

def randomGaussRange(low, high, n):
    out = []    
    mu = random.uniform(low, high)
    sigma = random.uniform(0, (mu - low) )
    while len(out) < n:
        num = (random.normalvariate(mu, sigma))
        if num < high and num > low:
            out.append(num)
        
    return out

def generateRandomOutputs(parameters):
    '''This fonction serves to bypass everything produced by Vissim to gain speed while testing the code'''
    RandSeed = parameters[1]
    NumRuns = parameters[2]   
    
    raw_opportunisticLC = []
    raw_mandatoryLC = [] 
    raw_flow = []
    raw_forward_gaps = []
    raw_opp_LC_agaps = []
    raw_opp_LC_bgaps = []
    raw_man_LC_agaps = []
    raw_man_LC_bgaps = []
    raw_foward_speed = []
        
    for i in range(NumRuns):
        random.seed(RandSeed + i)
        raw_opportunisticLC.append(random.uniform(2,30))
        raw_mandatoryLC.append(random.uniform(2,30)) 
        raw_flow.append(random.uniform(1200,2000))
        raw_forward_gaps.append(randomGaussRange(1,20,100))
        raw_opp_LC_agaps.append(randomGaussRange(1,20,100))
        raw_opp_LC_bgaps.append(randomGaussRange(1,20,100))
        raw_man_LC_agaps.append(randomGaussRange(5,10,100))
        raw_man_LC_bgaps.append(randomGaussRange(7,10,100))
        raw_foward_speed.append(randomGaussRange(7,10,100))
    
    mean_opportunisticLC =  scipy.mean(raw_opportunisticLC)
    mean_mandatoryLC =  scipy.mean(raw_mandatoryLC)  
    mean_flow =  scipy.mean(raw_flow)
    
    forward_followgap = stats(raw_forward_gaps)
    opportunistic_LCagap = stats(raw_opp_LC_agaps)
    opportunistic_LCbgap = stats(raw_opp_LC_bgaps)
    mandatory_LCagap = stats(raw_man_LC_agaps)
    mandatory_LCbgap = stats(raw_man_LC_bgaps)
    forward_speeds = stats(raw_foward_speed)
    
    return mean_flow, mean_opportunisticLC, mean_mandatoryLC, forward_followgap, opportunistic_LCagap, opportunistic_LCbgap,  mandatory_LCagap,  mandatory_LCbgap, forward_speeds