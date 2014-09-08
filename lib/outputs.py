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
import random

#disabling outputs
import lib.nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
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

def forwardGaps(objects, s, lane):
    '''Calculates all gaps on a given lane and for a given point s'''
    instants = []
    for o in objects:
        t = o.curvilinearPositions.getIntersections(s, lane)
        if t != []:
            instants.append(o.getFirstInstant()+t[0])
                
    instants.sort()
    x = np.asarray(instants)
    gaps = x[1:]-x[:-1]
    
    return gaps	
	
def laneChangeGaps(lists, listDict, laneDict, objects):
    '''Determines the width of lane change gaps for a list of objects who make lane changes
        agaps represent the gap present after the insertion of the lane changing vehicule
        bgaps reprensent the gap present before the insertion of the lane changing vehicule'''
    
    x = []  #agaps construction variable
    y = []  #bgaps construction variable
    for obj in lists:
        
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
    
def NEW_laneChange(objects, corridors):

    #Lists
    oppObj = []    
    manObj = []

    #Dictionaries    
    oppObjDict = {}    
    manObjDict = {}
    laneDict = {}

    for o in range(len(objects):    
        for i in set(objects[o].curvilinearPositions.lanes):
            if i not in laneDict: laneDict[i] = []
            if o not in laneDict[i]: laneDict[i].append(o)   
    
        #Vissim lane changes
        if isinstance(objects[o].curvilinearPositions.lanes[0],string):
            for pos in range(len(objects[o].curvilinearPositions.lanes) -1):
                #if link is not the same
                if objects[o].curvilinearPositions.lanes[pos].strip('_')[0] != objects[o].curvilinearPositions.lanes[pos + 1].strip('_')[0]:
                    start = None
                    end = None
                    #Verify if both links are in the same corridor
                    for corridor in corridors:
                        if objects[o].curvilinearPositions.lanes[pos] in corridor: start = corridor
                        if objects[o].curvilinearPositions.lanes[pos +1] in corridor: end = corridor
                    if start != end:    #if not --> mandatory lane change
                        if o not in manObj: manObj.append(o)
                        if o not in manObjDict:
                            manObjDict[o] = [[objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1]]
                        else:
                            manObjDict[o].append([objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1])
                #if link is the same
                else:
                    #if lane is not the same --> opportunistic lane change
                    if objects[o].curvilinearPositions.lanes[pos].strip('_')[1] != objects[o].curvilinearPositions.lanes[pos + 1].strip('_')[1]:
                        if o not in oppObj: oppObj.append(o)
                        if o not in oppObjDict:
                            oppObjDict[o] = [[objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1]]
                        else:
                            oppObjDict[o].append([objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1])
        
        #Traffic Intelligence lane changes
        else:
            for pos in range(len(objects[o].curvilinearPositions.lanes) -1):
                #if alignment is not the same
                if objects[o].curvilinearPositions.lanes[pos] != objects[o].curvilinearPositions.lanes[pos + 1]:
                    start = None
                    end = None
                    #Verify if both links are in the same corridor
                    for corridor in corridors:
                        if objects[o].curvilinearPositions.lanes[pos] in corridor: start = corridor
                        if objects[o].curvilinearPositions.lanes[pos +1] in corridor: end = corridor
                    if start == end:    #If yes --> opportunistic lane change
                        if o not in oppObj: oppObj.append(o)
                        if o not in oppObjDict:
                            oppObjDict[o] = [[objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1]]
                        else:           
                            oppObjDict[o].append([objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1])
                    else:               #If not --> mandatory lane change
                        if o not in manObj: manObj.append(o)
                        if o not in manObjDict:
                            manObjDict[o] = [[objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1]]
                        else:
                            manObjDict[o].append([objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1])
                            
    return oppObj, manObj, oppObjDict, manObjDict, laneDict
    
def laneChange(objects):
    '''Calculates whether an object makes a mandatory or an opportunistic lane change creates 3 dictionaries and two lists
    
    The two list (oppObj and manObj) are the objects respectively doing opportunistic lane changes and mandatory lane changes      
    
                                *************************
                                
    The fist two dictionaries (oppObjDict and manObjDict) present, for each lane change:
                    - lane before the lane change
                    - lane after the lane change
                    - position of the last lane in the lane vector
    
                      dict =  {obj | [ [start_lane, end_lane, end_pos], [start_lane, end_lane, end_pos], ... ] }
                        
                                *************************
                                
    The last dictionary presents the list of objects present on a lane
                      dict =  {lane | [ obj1, obj2, ... ] }   
    '''  
    #Lists
    oppObj = []    
    manObj = []

    #Dictionaries    
    oppObjDict = {}    
    manObjDict = {}
    laneDict   = {}
    
    for o in range(len(objects)):
        
        for i in set(objects[o].curvilinearPositions.lanes):
            if i not in laneDict: laneDict[i] = []
            if o not in laneDict[i]: laneDict[i].append(o)            
            
        #lanes are named "link_lane"
        #as of now, the assumption is that if a vehicle ends it's trajectory on a different link as it started, all the lane changes are considered mandatory.
        #this will have to be tried visually to be confirmed. Put Vissim's Simulation very low with a high density (2100+ veh/h/ln) and watch both the simulation and the outputs
        if objects[o].curvilinearPositions.lanes[0].split("_")[0] == objects[o].curvilinearPositions.lanes[-1].split("_")[0]:
            for lane in range(len(objects[o].curvilinearPositions.lanes) -1):
                                    
                if objects[o].curvilinearPositions.lanes[lane] != objects[o].curvilinearPositions.lanes[lane + 1]:
                    if o not in oppObj: oppObj.append(o)                    
                    if o in oppObjDict:
                        oppObjDict[o].append([objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1])
                    else:
                        oppObjDict[o] = [[objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1]]
                    
        else:                            
            for lane in range(len(objects[o].curvilinearPositions.lanes) -1):
                    
                if objects[o].curvilinearPositions.lanes[lane] != objects[o].curvilinearPositions.lanes[lane + 1]:
                    if o not in manObj: manObj.append(o)                    
                    if o in manObjDict:
                        manObjDict[o].append([objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1])
                    else:
                        manObjDict[o] = [[objects[o].curvilinearPositions.lanes[lane],objects[o].curvilinearPositions.lanes[lane + 1],lane + 1]]

    return oppObj, manObj, oppObjDict, manObjDict, laneDict

def dist(x):
    nlist = np.unique(x)
    stats = [sum(x==i)/float(len(x)) for i in nlist]
    cumul = np.cumsum(stats)
    mean = np.mean(np.asarray(x))
    firstQuart = numpy.percentile(x,25)
    median = np.median(np.asarray(x))
    thirdQuart = numpy.percentile(x,75)
    var = np.var(np.asarray(x))      
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
    
    if len(inputs) == 5:
        old_data = inputs[4]
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
	
    '''
    #Legacy code used the skip some files while looping during the Statistical precision analysis
    #Was removed when working to implement multiprocessing with this function    
    if first_file != None:
        for f in files:
            striped = f.strip('.csv')
            num = int(striped.split('_')[2])
            if num < first_file:
                files.pop(f)        
    '''

    if files is not None:    #this was implemented to be able to concatenate data received by a multiprocessing run
        for filename in files:
            if verbose:
                print ' === Starting calculations for ' + filename + ' ==='       
            objects = TraffIntStorage.loadTrajectoriesFromVissimFile(os.path.join(folderpath,filename), simulationStepsPerTimeUnit, nObjects = -1, warmUpLastInstant = warmUpTime * simulationStepsPerTimeUnit)
            raw_flow.append(len(objects))
            
            #lane building block
            lanes = {}
            for o in objects:
                for i in range(len(o.curvilinearPositions.lanes)):
                    lane = o.curvilinearPositions.lanes[i]
                    s = o.curvilinearPositions.getXCoordinates()[i]
                    if lane not in lanes:
                        lanes[lane] = [s, s]
                    else:
                        if s < lanes[str(lane)][0]:
                            lanes[str(lane)][0] = s
                        elif s > lanes[str(lane)][1]:
                            lanes[str(lane)][1] = s
    
            #lane change count by type        
            oppObj, manObj, oppObjDict, manObjDict, laneDict = laneChange(objects)
            if verbose:
                print ' == Lane change compilation done == '
            raw_opportunisticLC.append(sum([len(oppObjDict[i]) for i in oppObjDict]))
            raw_mandatoryLC.append(sum([len(manObjDict[i]) for i in manObjDict]))
            
            '''
            #Reserved code: calculates if an objects returns to the same lane he previously departed
            #May serve to check the results of the laneChange fct
            #Functionality proven on a random output file
            returns = []
            test = [i for i in manObjDict if len(manObjDict[i]) > 0]
            for j in range(len(test)):
                ori = []
                for f in range(len(manObjDict[test[j]])):                
                    if manObjDict[test[j]][f][0] not in ori: ori.append(manObjDict[test[j]][f][0])
                    if manObjDict[test[j]][f][1] in ori:
                        if test[j] not in returns: returns.append(test[j])
            
            print returns
            '''
              
            #forward gap analysis                    
            for index,lane in enumerate(lanes):  
                s = (lanes[str(lane)][0]+lanes[str(lane)][1])/2
                raw_gaps = forwardGaps(objects, s, lane) 
                if raw_gaps != []: raw_forward_gaps.append(raw_gaps)
                if verbose:
                    print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(lanes)) + ' == '
                
            #mandatory lane change gaps
            agaps, bgaps = laneChangeGaps(manObj, manObjDict, laneDict, objects)
            if agaps != []: raw_man_LC_agaps.append(agaps)
            if bgaps != []: raw_man_LC_bgaps.append(bgaps)
            if verbose:
                print ' == Mandatory lane change gaps calculation done == '
    	
            #opportunistic lane change gaps
            agaps, bgaps = laneChangeGaps(oppObj, oppObjDict, laneDict, objects)
            if agaps != []: raw_opp_LC_agaps.append(agaps)
            if bgaps != []: raw_opp_LC_bgaps.append(bgaps)
            if verbose:
                print ' == Opportunistic lane change gaps calculation done == '
                 
                print ' === Calculations for ' + filename + ' done ==='
               
    #Treating raw outputs to compute means
    if raw_opportunisticLC != []:
        if old_data == []:
            mean_opportunisticLC = scipy.mean(raw_opportunisticLC)
        else:
            mean_opportunisticLC = computeMeanfromOld(raw_opportunisticLC,old_num)
    else:
        mean_opportunisticLC = None
    
    if raw_mandatoryLC != []:
        if old_data == []:
            mean_mandatoryLC = scipy.mean(raw_mandatoryLC)
        else:
            mean_mandatoryLC = computeMeanfromOld(raw_mandatoryLC,old_num)
    else:
        mean_mandatoryLC = None
    
    if raw_flow != []:
        if old_data == []:
            mean_flow = scipy.mean(raw_flow)
        else:
            mean_flow = computeMeanfromOld(raw_flow,old_num)
    else:
        mean_flow = None
       
    forward_followgap = stats(raw_forward_gaps)
    opportunistic_LCagap = stats(raw_opp_LC_agaps)
    opportunistic_LCbgap = stats(raw_opp_LC_bgaps)
    mandatory_LCagap = stats(raw_man_LC_agaps)
    mandatory_LCbgap = stats(raw_man_LC_bgaps)

    return mean_flow, mean_opportunisticLC, mean_mandatoryLC, forward_followgap, opportunistic_LCagap, opportunistic_LCbgap,  mandatory_LCagap,  mandatory_LCbgap

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
    raw_man_LC_agaps =[]
    raw_man_LC_bgaps =[]
        
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
    
    mean_opportunisticLC =  scipy.mean(raw_opportunisticLC)
    mean_mandatoryLC =  scipy.mean(raw_mandatoryLC)  
    mean_flow =  scipy.mean(raw_flow)
    
    forward_followgap = stats(raw_forward_gaps)
    opportunistic_LCagap = stats(raw_opp_LC_agaps)
    opportunistic_LCbgap = stats(raw_opp_LC_bgaps)
    mandatory_LCagap = stats(raw_man_LC_agaps)
    mandatory_LCbgap = stats(raw_man_LC_bgaps)
    
    return mean_flow, mean_opportunisticLC, mean_mandatoryLC, forward_followgap, opportunistic_LCagap, opportunistic_LCbgap,  mandatory_LCagap,  mandatory_LCbgap