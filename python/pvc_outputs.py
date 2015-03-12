# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:38:05 2014

@author: Laurent
"""
##################
# Import Native Libraries
##################

import os, sys
import numpy as np
import random, time

##################
# Import Traffic Intelligence
##################
#disabling outputs
import nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import storage
sys.stdout = oldstdout #Re-enable output

##################
# Data classes
##################
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
    
class Sublvl:
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

    def addFileName(self,filename):
        self.filename = filename
            
class Stats:
    def __init__(self, raw):
        self.distributions  = []

        if raw != []:
            for l in raw:
                self.distributions.append(Sublvl(l))
            self.regen_cumul_all()                                
        else:
            self.cumul_all = Sublvl(raw)
    
    def add_one_dist_list(self, raw):
        '''adds a raw data list to the distributions'''
        self.distributions.append(Sublvl(raw))
        self.regen_cumul_all()
        
    def add_many_dist_list(self, raw_list):
        '''needs a list of raw data list'''
        for raw in raw_list:
            self.distributions.append(Sublvl(raw))
        self.regen_cumul_all()
        
    def pop_dist_list(self, mylist):
        '''mylist must refer to the indexes of the list of distributions to pop'''
        if len(mylist) > 0:
            for i in reversed(sorted(mylist)):
                if len(self.distributions) >= i:
                    self.distributions.pop(i)
            self.regen_cumul_all()
        
    def regen_cumul_all(self):
        '''recalculates the cumum_all distribution'''
        allvalues = []
        for dist in self.distributions:
            allvalues += list(dist.raw)
        self.cumul_all = Sublvl(allvalues)
        self.cumul_all.raw.sort()

    @classmethod
    def concat(cls, stats1, *stats):
        '''concanate all the distributions of the stats class variables into the first one'''
        new_raw = []
        for stat in stats:
            for dist in stat.distributions:
                new_raw.append(dist.raw)
        stats1.add_many_dist_list(new_raw)
        
class SingleValueStats:
    def __init__(self,raw):
        self.raw = raw
        self.recalculate()
        
    def addOne(self,number):
        self.raw.append(number)
        self.raw.sort()
        self.recalculate()
        
    def addMany(self,mylist):
        for i in mylist:
            self.raw.append(i)
        self.raw.sort()
        self.recalculate()
        
    def popList(self,mylist):
        '''mylist must refer to the indexes of the numbers to pop'''
        if len(mylist) > 0:
            for i in reversed(sorted(mylist)):
                if len(self.raw) >= i:
                    self.raw.pop(i)
            self.recalculate()
        
    def recalculate(self):
        '''calculates usfull data'''
        if self.raw != []:
            self.mean = np.mean(self.raw)
            self.var = np.var(self.raw)
            self.std = np.std(self.raw)
            self.count = len(self.raw)
        else:
            self.mean = 0
            self.var = 0
            self.std = 0
            self.count = len(self.raw)
            self.raw.sort()

    @classmethod
    def concat(cls, stats1, *stats):
        '''concanate all the distributions of the stats class variables into the first one'''
        new_raw = []
        for stat in stats:
            new_raw += stat.raw
        stats1.addMany(new_raw)

class Outputs:
    def __init__(self, flow=None, oppLCcount=None, manLCcount=None, forFMgap=None, oppLCagap=None, oppLCbgap=None, manLCagap=None, manLCbgap=None, forSpeeds=None):
        self.flow       = flow
        self.oppLCcount = oppLCcount
        self.manLCcount = manLCcount
        self.forFMgap   = forFMgap
        self.oppLCagap  = oppLCagap
        self.oppLCbgap  = oppLCbgap
        self.manLCagap  = manLCagap
        self.manLCbgap  = manLCbgap
        self.forSpeeds  = forSpeeds
        
    def add_one_count(self, flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, forSpeeds):
        pass
    ##TODO: ajouter une instance de chaque entrée
        
    def GetFilenames():
        pass
    ##TODO: passe à travers forFMgap.distributions[i].filename pour les retourner

##TODO:
    #1 - conceptualiser le calcul des outputs pour les générer un fichier à la fois
    #2 - finir la classe Outputs afin d'ajouter les outputs un à la fois
    #3 - refaire les calculs des outputs pour les générer un fichier à la fois
    #4 - refaire les calculs des randoms outputs pour les générer un à la fois
    #5 - ajouter une fonction de pop et popList à la classe Outputs
    #6 - permettre de disable certains outputs
        
##################
# Output treatment tools
##################
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
    return list(x[1:]-x[:-1])
    
def forwardGaps(objects, s, lane):
    '''Calculates all gaps on a given lane and for a given point s'''
    
    instants, speeds = calculateInstants(objects, s, lane)
    gaps = calculateGaps(instants)
    #for g in reversed(xrange(len(gaps))):
    #    if gaps[g] >= 30:
    #        gaps.pop(g)
    return gaps, speeds

def laneChangeGaps(listDict, laneDict, objects):
    '''Determines the width of lane change gaps for a list of objects who make
       lane changes
        - agaps represent the gap present after the insertion of the lane
          changing vehicule
        - bgaps reprensent the gap present before the insertion of the lane
          changing vehicule'''
    
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
                    if int(objects[o].curvilinearPositions.lanes[pos].split('_')[0]) in to_eval or int(objects[o].curvilinearPositions.lanes[pos+1].split('_')[0]) in to_eval:
                        #eliminating link interface change
                        if objects[o].curvilinearPositions.lanes[pos].split('_')[0] == objects[o].curvilinearPositions.lanes[pos + 1].split('_')[0]:
                            if objects[o].curvilinearPositions.lanes[pos].split('_')[1] != objects[o].curvilinearPositions.lanes[pos + 1].split('_')[1]:
                                oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)                        
                    
            #otherwise, we need to investigate more
            else:      
                for pos in range(len(objects[o].curvilinearPositions.lanes) -1):                  
                    #keeping only the evaluated links                            
                    if int(objects[o].curvilinearPositions.lanes[pos].split('_')[0]) in to_eval or int(objects[o].curvilinearPositions.lanes[pos+1].split('_')[0]) in to_eval:                    
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
                    if objects[o].curvilinearPositions.lanes[pos] in to_eval or objects[o].curvilinearPositions.lanes[pos+1] in to_eval:
                        if objects[o].curvilinearPositions.lanes[pos] != objects[o].curvilinearPositions.lanes[pos + 1]:
                            oppObjDict = appendDicts(o, oppObjDict, objects[o].curvilinearPositions.lanes[pos], objects[o].curvilinearPositions.lanes[pos+1], pos+1)                        
                        
            else:

                for pos in range(len(objects[o].curvilinearPositions.lanes) -1):
                    #keeping only the evaluated links                            
                    if objects[o].curvilinearPositions.lanes[pos] in to_eval or objects[o].curvilinearPositions.lanes[pos+1] in to_eval:                                            
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

def read_error_file(dirname,filename):
    '''reads an error file and returns the number of
            deceleration is positive errors
            accelaration is zero errors
            the total number of vehicules that could not be generated
    '''
    case_dp = 0     #deceleration is positive
    case_a0 = 0     #acceleration is zero
    num = 0         #number of vehicles to generate
    with open(os.path.join(dirname,filename),'r') as err:
        for line in err:
            
            if 'The expected trajectory of vehicle' in line and 'cannot be determined' in line:
                if 'expected deceleration is positive' in line:
                    case_dp += 1
                if 'expected acceleration is zero' in line:
                    case_a0 += 1
                    
            if 'Vehicle input' in line and 'could not be finished completely' in line:
                num += float(line.strip().split('remain: ')[-1].split(' ')[0])
                
    return num, case_dp, case_a0

def search_folder_for_error_files(dirname):
    '''search a directory and returns the mean value, for every fzp files, of
            deceleration is positive errors
            accelaration is zero errors
            the total number of vehicules that could not be generated
    '''
    filenames = [f for f in os.listdir(dirname) if f.endswith('err')]
    fzp_files = [f for f in os.listdir(dirname) if f.endswith('fzp')]
    
    if len(fzp_files) > 0:
        num_list = []; dp_list = []; a0_list = []
        for filename in filenames:       
            num, dp, a0 = read_error_file(dirname,filename)
            num_list.append(num); dp_list.append(dp); a0_list.append(a0)
        
        if len(filenames) < len(fzp_files):
            for i in xrange(len(fzp_files)-len(filenames)):
                num_list.append(0); dp_list.append(0); a0_list.append(0)
        
        return np.mean(num_list), np.mean(dp_list), np.mean(a0_list)
    else:
        return float('nan'), float('nan'), float('nan')

def convert_errors_to_constraints(config, num, dp, a0):
    '''converts num, dp and a0 errors into constraint values
       
       values are reduced by the tolerance threshold, allowing the use of
       EB, PB or PEB constraint handling strategies
    '''
    C_0 = 0
    C_1 = 0
    C_2 = 0

    if num > config.num_const_thresh:
        C_0 = num - config.num_const_thresh
    if dp > config.dp_const_thresh:
        C_1 = dp - config.dp_const_thresh
    if a0 > config.a0_const_thresh:
        C_2 = a0 - config.a0_const_thresh
        
    return C_0, C_1, C_2

def sort_fout_and_const(fout_lists):
    '''sort many outputs f1, f2, f3, etc. to keep the worst one
       if all fi respect the constraints, then fi are sorted to give worst fout
       if not all fi respect constraint, the first one to not respect it is returned
    '''

    valids = []    
    #check constraints:
    for l in fout_lists:
        if l[1] == 0 and l[2] == 0 and l[3] == 0:
            valids.append(fout_lists.index(l))

    #sort valids
    if len(valids) == len(fout_lists):
        to_conserve = fout_lists[valids[0]]
        for i in valids:
            if fout_lists[i][0] > to_conserve[0]:
                to_conserve = fout_lists[i]

        return to_conserve
    else:
        for i in xrange(len(fout_lists)):
            if i not in valids:
                return fout_lists[i]

def extract_num_from_fzp_name(filename):
    '''returns the numerical component of a vissim fzp file'''
    return int(os.path.splitext(filename)[0].split('_')[-1])

def extract_num_from_fzp_list(filenames):
    '''returns the numerical component of a list of vissim fzp files'''
    num_list = []
    for filename in filenames:
        num_list.append(extract_num_from_fzp_name(filename))
    return num_list
    
def check_fzp_content(dirname,filename):
    '''classifies a fzp file according to the column headers
    
       case 1: everything is in place where traffic intelligence expects it
       case 2: every needed information is provided, but not in the right order
       case 3: the poslat information is missing, it will be assumed to be 0.5 everywhere
       case 4: some important non-spoofable information is missing, raising a warning and exiting
    '''
    #finding the header
    with open(os.path.join(dirname,filename)) as fzp:
        for i in xrange(1):
            fzp.readline()
        
        for line in fzp:
            if '$' not in line:
                pass
            else:
                header_line = line.strip().strip('$').lower().split(';')
                break
    
    #classifying with available columns
    if 'vehicle:simsec' in header_line[0] and 'no' in header_line[1] and 'lane\\link\\no' in header_line[2] and 'lane\\index' in header_line[3] and 'pos'in header_line[4] and 'poslat' in header_line[5]:
        case = 1
    elif 'vehicle:simsec' in header_line and 'no' in header_line and 'lane\\link\\no' in header_line and 'lane\\index' in header_line and 'pos'in header_line:       
        if 'poslat' in header_line:
            case = 2
        else:
            case = 3
    else:
        print ('Missing information columns in the fzp files\n'
               '\n'
               'Make sure that all the following attributes are activated...\n'
               'Interface name [.fzp name]:\n'
               '     Simulation second [VEHICLE:SIMSEC],\n'
               '     Number [NO]\n'
               '     Lane\Link\Number [LANE\LINK\NO]\n'
               '     Lane\Index [LANE\INDEX]\n'
               '     Position [POS]\n'
               '     Position (lateral) [POSLAT]\n'
               '\n'
               'To activate:\n'
               '  Evaluation > Configuration > Tab: Direct Output >\n'
               '  Row: Vehicle > Record > Click to More... > Click to Attributes\n'
               )
        sys.exit()

    return case
    
def false_fzp(case,dirname,filename):
    '''Reorders Case 2 and Case 3 fzp files with required information by the
       traffic intelligence function
       
       Returns the name of the temporary file created
    
       information on .fzp files can be found in section 10.8.2.1 of the manual'''
    
    false_fzp = ''
    with open(os.path.join(dirname,filename),'r') as fzp:
        #skip header        
        for i in xrange(1):
            false_fzp += fzp.readline()

        for line in fzp:
            #print line.strip()
            if '$' not in line:
                false_fzp += line
            else:
                false_fzp += line
                break
        
        #reorder the file
        order = line.strip().strip('$').lower().split(';')
        for line in fzp:
            if line.strip() != '':
                line_build = ''
                line_infos = line.strip().split(';')
                line_build += line_infos[order.index('vehicle:simsec')] + ';'
                line_build += line_infos[order.index('no')] + ';'
                line_build += line_infos[order.index('lane\\link\\no')] + ';'
                line_build += line_infos[order.index('lane\\index')] + ';'
                line_build += line_infos[order.index('pos')] + ';'
                
                if case == 2:
                    line_build += line_infos[order.index('poslat')]
                elif case == 3:
                    line_build += '0.5'
                
                line_build += '\n'
                
                false_fzp += line_build
                
    with open(os.path.join(dirname,'temp_reordered_'+filename),'w') as temp_fzp:
        for line in false_fzp:
            temp_fzp.write(line)
                
    return 'temp_reordered_'+filename

def readTrajectoryFromFZP(dirname, filename, simulationStepsPerTimeUnit, warmUptime):
    '''first checks for the compatibility of the given fzp, then process it'''
    case = check_fzp_content(dirname,filename)
    
    if case == 1:        
        objects = storage.loadTrajectoriesFromVissimFile(os.path.join(dirname, filename), simulationStepsPerTimeUnit, nObjects = -1, warmUpLastInstant = warmUptime*simulationStepsPerTimeUnit)

    elif case ==2 or case == 3:
        temp_fzp = false_fzp(case,dirname,filename)
        objects = storage.loadTrajectoriesFromVissimFile(os.path.join(dirname, temp_fzp), simulationStepsPerTimeUnit, nObjects = -1, warmUpLastInstant = warmUptime*simulationStepsPerTimeUnit)
        
        os.remove(os.path.join(dirname,temp_fzp))

    return objects

def treatVissimOutputs(files, inputs):
    '''Treat outputs in the given folder '''
    
    folderpath                 = inputs[0]
    simulationStepsPerTimeUnit = inputs[1]
    warmUpTime                 = inputs[2]
    verbose                    = inputs[3]
    corridors                  = inputs[4]
    
    if len(inputs) == 6:
        old_data = inputs[5]
    else:
        old_data = []
    
    raw_opportunisticLC = []
    raw_mandatoryLC     = [] 
    raw_flow            = []
    raw_forward_gaps    = []
    raw_opp_LC_agaps    = []
    raw_opp_LC_bgaps    = []
    raw_man_LC_agaps    = []
    raw_man_LC_bgaps    = []
    raw_forward_speeds  = []
    
    if old_data != []:
        mean_flow            = old_data[0]
        mean_opportunisticLC = old_data[1]
        mean_mandatoryLC     = old_data[2]
        forward_followgap    = old_data[3]
        opportunistic_LCagap = old_data[4]
        opportunistic_LCbgap = old_data[5]
        mandatory_LCagap     = old_data[6]
        mandatory_LCbgap     = old_data[7]
        forward_speeds       = old_data[8]

    for filename in files:
        if verbose:
            print ' === Starting calculations for ' + filename + ' ===  |'    
        objects = readTrajectoryFromFZP(folderpath, filename, simulationStepsPerTimeUnit,  warmUpTime)
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
            s = (0.5*lanes[str(lane)][1]-0.5*lanes[str(lane)][0])
            raw_gaps, raw_speeds = forwardGaps(objects, s, lane)
            if raw_gaps != []: temp_raw_forward_gaps += list(raw_gaps)
            if raw_speeds != []: temp_raw_speeds += list(raw_speeds)    
            if verbose:
                print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(lanes)) + ' ==  |' + str(time.clock()) + ' | ' + str(len(temp_raw_forward_gaps))

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
               
    #Treating raw outputs to compute means
    if old_data != []:
        mean_flow.addMany(raw_flow)
        mean_opportunisticLC.addMany(raw_opportunisticLC)
        mean_mandatoryLC.addMany(raw_mandatoryLC)
        forward_followgap.add_many_dist_list(raw_forward_gaps)
        opportunistic_LCagap.add_many_dist_list(raw_opp_LC_agaps)
        opportunistic_LCbgap.add_many_dist_list(raw_opp_LC_bgaps)
        mandatory_LCagap.add_many_dist_list(raw_man_LC_agaps)
        mandatory_LCbgap.add_many_dist_list(raw_man_LC_bgaps)
        forward_speeds.add_many_dist_list(raw_forward_speeds)    
    
    else:
        mean_flow            = SingleValueStats(raw_flow)
        mean_opportunisticLC = SingleValueStats(raw_opportunisticLC)
        mean_mandatoryLC     = SingleValueStats(raw_mandatoryLC)    
        forward_followgap    = Stats(raw_forward_gaps)
        opportunistic_LCagap = Stats(raw_opp_LC_agaps)
        opportunistic_LCbgap = Stats(raw_opp_LC_bgaps)
        mandatory_LCagap     = Stats(raw_man_LC_agaps)
        mandatory_LCbgap     = Stats(raw_man_LC_bgaps)
        forward_speeds       = Stats(raw_forward_speeds)        
    
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

def generateRandomOutputs(parameters, rand_seed_shake):
    '''This fonction serves to bypass everything produced by Vissim to gain
       speed while testing the code'''
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
        random.seed(RandSeed + i + rand_seed_shake)
        raw_opportunisticLC.append(random.uniform(2,30))
        raw_mandatoryLC.append(random.uniform(2,30)) 
        raw_flow.append(random.uniform(1200,2000))
        raw_forward_gaps.append(randomGaussRange(1,20,100))
        raw_opp_LC_agaps.append(randomGaussRange(1,20,100))
        raw_opp_LC_bgaps.append(randomGaussRange(1,20,100))
        raw_man_LC_agaps.append(randomGaussRange(5,10,100))
        raw_man_LC_bgaps.append(randomGaussRange(7,10,100))
        raw_foward_speed.append(randomGaussRange(7,10,100))
    
    mean_opportunisticLC = SingleValueStats(raw_opportunisticLC)
    mean_mandatoryLC     = SingleValueStats(raw_mandatoryLC)  
    mean_flow            = SingleValueStats(raw_flow)    
    forward_followgap    = Stats(raw_forward_gaps)
    opportunistic_LCagap = Stats(raw_opp_LC_agaps)
    opportunistic_LCbgap = Stats(raw_opp_LC_bgaps)
    mandatory_LCagap     = Stats(raw_man_LC_agaps)
    mandatory_LCbgap     = Stats(raw_man_LC_bgaps)
    forward_speeds       = Stats(raw_foward_speed)
    
    return mean_flow, mean_opportunisticLC, mean_mandatoryLC, forward_followgap, opportunistic_LCagap, opportunistic_LCbgap,  mandatory_LCagap,  mandatory_LCbgap, forward_speeds