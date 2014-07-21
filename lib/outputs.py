# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:38:05 2014

@author: Laurent
"""
##################
# Import Native Libraries
##################

import scipy, os
import numpy as np
import storage as TraffIntStorage
import random

##################
# Output treatment tools
##################

class sublvl:
    def __init__(self, raw = [], value = None, cumul = None, mean = None, median = None, var = None):
        self.raw    = raw        
        self.value  = value
        self.cumul  = cumul
        self.mean   = mean
        self.median = median
        self.var    = var
        self.std    = var**0.5 

class stats:
    def __init__(self, raw):
        self.distributions  = []
        allvalues = []
        for l in raw:
            for m in l:
                allvalues.append(m)
            cumul,nlist,mean,median,var  = dist(l)
            self.distributions.append(sublvl(l, nlist,cumul,mean,median,var))

        cumul,nlist,mean,median,var  = dist(allvalues)
        self.cumul_all = sublvl(allvalues,nlist,cumul,mean,median,var)

def forwardGaps(objects, s, lane):
    '''Calculates all gaps on a given lane and for a given point s'''
    instants = []
    for o in objects:
        t = o.curvilinearPositions.getIntersections(s, str(lane))
        if t != []:
            instants.append(o.getFirstInstant()+t[0])
                
    instants.sort()
    x = np.asarray(instants)
    gaps = x[1:]-x[:-1]
    
    return gaps	
	
def laneChangeGaps(lists, objects):
    '''Determines the width of lane change gaps for a list of objects who make lane changes
        agaps represent the gap present after the insertion of the lane changing vehicule
        bgaps reprensent the gap present before the insertion of the lane changing vehicule'''
	
    x = []  #agaps construction variable
    y = []  #bgaps construction variable
    for obj in lists:
        for pos in range(len(objects[obj].curvilinearPositions.lanes)-1):
            if objects[obj].curvilinearPositions.lanes[pos] != objects[obj].curvilinearPositions.lanes[pos +1]: 
                lane = objects[obj].curvilinearPositions.lanes[pos +1]
                stepNum = objects[obj].getFirstInstant()+obj
                s = objects[obj].curvilinearPositions.getXCoordinates()[pos +1]
				
                #determining the gap
                instants = []
                for candidate in range(len(objects)):
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
							
def laneChange(objects):
    '''Calculates whether an object makes a mandatory or an opportunistic lane change'''  
    oppObj  = []
    manObj = []  
    for o in range(len(objects)):
        #lanes are named "link_lane"
        #as of now, the assumption is that if a vehicle ends it's trajectory on a different link as it started, all the lane changes are considered mandatory.
        #this will have to be tried visually to be confirmed. Put Vissim's Simulation very low with a high density (2100+ veh/h/ln) and watch both the simulation and the outputs
        if objects[o].curvilinearPositions.lanes[0].split("_") == objects[o].curvilinearPositions.lanes[-1].split("_"):
            for lane in range(len(objects[o].curvilinearPositions.lanes) -1):
                if objects[o].curvilinearPositions.lanes[lane] != objects[o].curvilinearPositions.lanes[lane + 1]:
                    oppObj.append(o)
                    
        else:                            
            for lane in range(len(objects[o].curvilinearPositions.lanes) -1):
                if objects[o].curvilinearPositions.lanes[lane] != objects[o].curvilinearPositions.lanes[lane + 1]:
                    manObj.append(o)

    return oppObj, manObj

def dist(x):
    nlist = np.unique(x)
    stats = [sum(x==i)/float(len(x)) for i in nlist]
    cumul = np.cumsum(stats)
    mean = np.mean(np.asarray(x))
    median = np.median(np.asarray(x))
    var = np.var(np.asarray(x))      
    return cumul,nlist,mean,median,var

def treatVissimOutputs(folderpath, simulationStepsPerTimeUnit, warmUpTime, old_data = [], first_file = None):
    '''Treat outputs in the given folder 
       If Old_data exists, it must be transfered as the raw list'''
    
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
	
    files = [f for f in os.listdir(folderpath) if f.endswith("fzp")]
    if first_file != None:
        for f in files:
            striped = f.strip('.csv')
            num = int(striped.split('_')[2])
            if num < first_file:
                files.pop(f)        
        
    for filename in files:
        #print ' === Starting calculations for ' + filename + ' ==='
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
        oppObj, manObj = laneChange(objects)
        #print ' == Lane change compilation done == '
        raw_opportunisticLC.append(len(oppObj))
        raw_mandatoryLC.append(len(manObj))
                    
        #forward gap analysis                    
        for index,lane in enumerate(lanes):  
            s = (lanes[str(lane)][0]+lanes[str(lane)][1])/2
            raw_forward_gaps.append(forwardGaps(objects, s, lane))		
            #print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(lanes)) + ' == '
        #mandatory lane change gaps
        agaps, bgaps = laneChangeGaps(manObj, objects)
        if agaps != []: raw_man_LC_agaps.append(agaps)
        if bgaps != []: raw_man_LC_bgaps.append(bgaps)
        #print ' == Mandatory lane change gaps calculation done == '
	
        #opportunistic lane change gaps
        agaps, bgaps = laneChangeGaps(oppObj, objects)
        if agaps != []: raw_opp_LC_agaps.append(agaps)
        if bgaps != []: raw_opp_LC_bgaps.append(bgaps)
        #print ' == Oppurtunistic lane change gaps calculation done == '
         
        #print ' === Calculations for ' + filename + ' done ==='
        
    #Treating raw outputs to compute means
    if raw_opportunisticLC != []:
        mean_opportunisticLC =  scipy.mean(raw_opportunisticLC)
    else:
        mean_opportunisticLC = None
    if raw_mandatoryLC != []:
        mean_mandatoryLC =  scipy.mean(raw_mandatoryLC)
    else:
        mean_mandatoryLC = None
    if raw_flow != []:
        mean_flow =  scipy.mean(raw_flow)
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