# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:28:53 2014

@author: Laurent
"""
##################
# Version
##################
#this will be used to verify if the serialised data is still matching the data processsed by pcvtools
def version():
    '''if a change modifies the data to be serialized, increment the number directly after R
       otherwise, play with .X.Y
    '''
    Version = 'R1.2.1 u. 06-10-2014'
    
##################
# Import Libraries
##################
#Natives
from itertools import izip, chain, repeat
from pylab import csv2rec
import multiprocessing
import math, sys, os
import numpy as np
import cPickle as pickle
import StringIO

##################
# Import Traffic Intelligence
##################
#disabling outputs
import lib.nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import moving
sys.stdout = oldstdout #Re-enable output

##################
# Read file data tools
##################
def loadDataFromTraj(path, filename):
    with open(os.path.join(path, filename), 'rb') as input_data:
        trajversion = pickle.dump(input_data)
        if trajversion == version(): 
            oppLCcount  = pickle.load(input_data)
            manLCcount  = pickle.load(input_data)
            flow        = pickle.load(input_data)
            forFMgap    = pickle.load(input_data)
            oppLCagap   = pickle.load(input_data)
            oppLCbgap   = pickle.load(input_data)
            manLCagap   = pickle.load(input_data)
            manLCbgap   = pickle.load(input_data)
            Speeds      = pickle.load(input_data)
            return [oppLCcount, manLCcount, flow, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap, Speeds]
        
        else:
             print 'Data version outdated, aborting calculations. Please recalculate video data'
             sys.exit()

#corridor information             
class Corridor:
    def __init__(self,data):
        self.name      = data[0]
        self.direction = data[1]
        self.link_list = data[2]
        self.to_eval   = data[3]

def extractVissimCorridorsFromCSV(dirname, inpxname):
    '''Reads corridor information for a csv named like the inpx
       CSV file must be build as:    Corridor_name,vissim list,traffic intelligence list
       both list must be separated by "-"
    '''

    if inpxname in dirname: dirname = dirname.strip(inpxname)
    if os.path.exists(os.path.join(dirname, inpxname)):

        filename  = [f for f in os.listdir(dirname) if f == (inpxname.strip('.inpx') + '.csv')]
        f = open(os.path.join(dirname,filename[0]))
        for line in f:
            if '$Corridors' in line.strip(): break
            
        brute = []
        for line in f:
            if '$' in line.strip(): break
            if line.startswith('#') is False and line.strip() != '': brute.append(line.strip())
             
        vissimCorridors = {}
        trafIntCorridors = {}    
        for b in xrange(len(brute)):        
            vissimCorridors[b] = Corridor([ brute[b].split(';')[0], brute[b].split(';')[1], [int(s) for s in brute[b].split(';')[2].split('-')], [int(s) for s in brute[b].split(';')[3].split('-')] ])
            trafIntCorridors[b] = Corridor([ brute[b].split(';')[0], brute[b].split(';')[1], [int(s) for s in brute[b].split(';')[4].split('-')], [int(s) for s in brute[b].split(';')[5].split('-')] ])
       
        return vissimCorridors.values(), trafIntCorridors.values()
    else:
        print 'No vissim file named ' + str(inpxname) + ', closing program '
        sys.exit()

#alignement information
class Videos:
    def __init__(self,data):
        self.video_name = data[0]
        self.alignments = []
        for i in data[1]:
            self.alignments.append(Alignments(i))
        
class Alignments:
    def __init__(self,data):
        self.name       = data[0]
        self.point_list = data[1]
        
def extractAlignmentsfromCSV(dirname, inpxname):
    '''Reads corridor information for a csv named like the inpx
       CSV file must be build as:
       Video_name
       Alignment_name;point_list with point_list as: (x1,y1),(x2,y2),etc
       both list must be separated by "-"
    '''
    if inpxname in dirname: dirname = dirname.strip(inpxname)
    if os.path.exists(os.path.join(dirname, inpxname)):

        filename  = [f for f in os.listdir(dirname) if f == (inpxname.strip('.inpx') + '.csv')]
        f = open(os.path.join(dirname,filename[0]))
        for line in f:
            if '$Video_alignments' in line.strip(): break
        
        video_names = []
        sublvl = []
        brute = []
        for line in f:
            if line.strip() == '':
                if sublvl != []: brute.append(sublvl)
                sublvl = [] 
            if '$' in line.strip():
                break
            if line.strip().endswith('.sqlite'):
                video_names.append(line.strip())
                if sublvl != []: brute.append(sublvl)
                sublvl = []
            if line.strip().endswith('.sqlite') is False and line.strip() != '':
                sublvl.append(line.strip())
        if sublvl != []: brute.append(sublvl)
        
        videos = {}
        for vid in xrange(len(brute)):
            vid_name = video_names[vid]
            align_list = {}
            for b in xrange(len(brute[vid])):
                name = brute[vid][b].split(';')[0]
                inter = brute[vid][b].split(';')[1].replace('),(',');(').split(';')
                point = []
                for i in xrange(len(inter)):
                    point.append(moving.Point(float(inter[i].strip('(').strip(')').split(',')[0]),float(inter[i].strip('(').strip(')').split(',')[1])))
           
                align_list[b] = [name, point]
            videos[vid] = Videos([vid_name, align_list.values()])
                
        return videos.values()
    else:
        print 'No vissim file named ' + str(inpxname) + ', closing program '
        sys.exit()

#parameter information        
def floatOrNone(stringvalue):
    try:
        return float(stringvalue)
    except:
        return None
        
def floatOrBool(stringvalue): 
    try:
        return float(stringvalue)
    except: 
        if stringvalue.lower() == 'false':
            return False
        elif stringvalue.lower() == 'true':
            return True

class Variable:
    def __init__(self, name, vissim_name, vissim_min, vissim_max, vissim_default, desired_min, desired_max):
        self.name           = name
        self.vissim_name    = vissim_name
        self.vissim_default = floatOrBool(vissim_default)
        self.desired_min    = floatOrBool(desired_min)
        self.desired_max    = floatOrBool(desired_max)
        self.vissim_min     = floatOrNone(vissim_min)
        self.vissim_max     = floatOrNone(vissim_max)

def extractParamFromCSV(dirname, inpxname): #MIGRATION TO FINISH
    '''Reads variable information for a csv named like the inpx
       CSV file must be build as:
             1rst line:      VarName,VissimMin,VissimMax,DesiredMin,DesiredMax,VissimName
             other lines:    stringfloat,float,float,float,string,
             
             where:
                     VarName is a name given by the user and will be used to write
                     pcvtools reports
                     VissimName is the name of the variable found in the Vissim COM manual
                     VissimMin and VissimMax are the min and max values found in the
                     Vissim COM manual
                     DesiredMin and DesiredMax are the range to be used for the evaluation                           
    '''

    if inpxname in dirname: dirname = dirname.strip(inpxname)
    if os.path.exists(os.path.join(dirname, inpxname)):

        filename  = [f for f in os.listdir(dirname) if f == (inpxname.strip('.inpx') + '.csv')]
        f = open(os.path.join(dirname,filename[0]))
        for line in f:
            if '$Variables' in line.strip(): break
            
        brutestring = ''
        for line in f:
            if '$' in line: break
            if line.startswith('#') is False and line.strip() != '': brutestring += line.replace("\t", "")
            
        vissimNames, vissimMinVa, vissimMaxVa, vissimDefau, value_names, desiredMinV, desiredMaxV = extractDataFromVariablesCSV(StringIO.StringIO(brutestring.replace(" ", "")))
        
        parameters = {}        
        for i in xrange(len(vissimNames)):
            parameters[i] = Variable(value_names[i], vissimNames[i], vissimMinVa[i], vissimMaxVa[i], vissimDefau[i], desiredMinV[i], desiredMaxV[i])
        
        parameters = verifyDesiredRanges(parameters.values())       
        
        return parameters
    else:
        print 'No vissim file named ' + str(inpxname) + ', closing program '
        sys.exit()
        
def extractDataFromVariablesCSV(filename): 
    '''works inside convertParameterstoString'''
    variablesInfo = csv2rec(filename)
    vissimNames = variablesInfo['vissimname']
    vissimMinVa = variablesInfo['vissimmin']
    vissimMaxVa = variablesInfo['vissimmax']
    vissimDefau = variablesInfo['vissimdefault']
    value_names = variablesInfo['varname']
    desiredMinV = variablesInfo['desiredmin']
    desiredMaxV = variablesInfo['desiredmax']
       
    return vissimNames, vissimMinVa, vissimMaxVa, vissimDefau, value_names, desiredMinV, desiredMaxV

def verifyDesiredRanges(variables):
    for i in xrange(len(variables)):
        if variables[i].vissim_min is not None:
            if variables[i].desired_min < variables[i].vissim_min:
                print str(variables[i].name) + ' was set to have a lower bound of ' + str(variables[i].vissim_min) + ' which is lower than the vissim minimum bound. Setting the lower bound to the vissim bound' 
                variables[i].desired_min = variables[i].vissim_min
        
        if variables[i].vissim_max is not None:    
            if variables[i].desired_max > variables[i].vissim_max:
                print str(variables[i].name) + ' was set to have a upper bound of ' + str(variables[i].vissim_max) + ' which is higher than the vissim maximum bound. Setting the upper bound to the vissim bound'             
                variables[i].desired_max = variables[i].vissim_max            
    return variables

##################
# Define tools
##################

def sort2lists(list1,list2):
    '''Sorts list2 according to the sorting of the content of list1
       list1 must contain values that can be sorted while
       list2 may contain any kind of data'''
       
    indexes = range(len(list1))
    indexes.sort(key=list1.__getitem__)
    sorted_list1 = map(list1.__getitem__, indexes)
    sorted_list2 = map(list2.__getitem__, indexes)
    
    return sorted_list1, sorted_list2

##################
# Multiprocessing tools
##################
    
def toChunks(n, iterable, padvalue=None, asList=True):
    ''' Split an iterable into chunks of n size
        toChunks(3, 'abcdefg', 'x')
        >>> [['a','b','c'], ['d','e','f'], ['g','x','x']]
        '''
    if(asList): return [list(x) for x in izip(*[chain(iterable, repeat(padvalue, n-1))]*n)]
    else:       return izip(*[chain(iterable, repeat(padvalue, n-1))]*n)

def cleanChunks(n, iterable, padvalue=None, asList=True):
    chunks = toChunks(n, iterable, padvalue, asList)
    if padvalue is None:
        clean_chunks = [[] for i in range(len(chunks))]
        for i in range(len(chunks)):
            for j in range(len(chunks[i])):
                if chunks[i][j] != None:
                    clean_chunks[i].append(chunks[i][j])
    else:
        clean_chunks = chunks
    return clean_chunks
    
def intelligentChunks(n, iterable, value_names):
    '''Cuts the variables into chunks keeping together the variables that need to relate to others'''           
    
    intelligent_chunk = []
    if len(iterable) != n:
        keepAssembled_g1 = ("LookAheadDistMin","LookAheadDistMax","LookBackDistMin","LookBackDistMax")    
        keepAssembled_g2 = ("CoopLnChg","CoopLnChgSpeedDiff","CoopLnChgCollTm")    

        keptAssembled_g1 = []
        keptAssembled_g2 = []
        other_iterables = []    
        
        for i in range(len(iterable)):
            if value_names[i] in keepAssembled_g1:
                keptAssembled_g1.append([iterable[i],i])
            elif value_names[i] in keepAssembled_g2:
                keptAssembled_g2.append([iterable[i],i])            
            else:
                other_iterables.append([iterable[i],i])            
                 
        if len(keptAssembled_g1) + len(keptAssembled_g2) <= n and len(keptAssembled_g1) + len(keptAssembled_g2) > 0:
            intelligent_chunk.append(keptAssembled_g1 + keptAssembled_g2)
        else:
            if keptAssembled_g1 != []: intelligent_chunk.append(keptAssembled_g1)
            if keptAssembled_g2 != []: intelligent_chunk.append(keptAssembled_g2)
        if other_iterables != []:
            clean_chunks = cleanChunks(n, other_iterables, padvalue=None, asList=True)
            for i in range(len(clean_chunks)): intelligent_chunk.append(clean_chunks[i])
    else:
        for i in range(len(iterable)):
            intelligent_chunk.append([iterable[i],i])
    
    return intelligent_chunk

def createWorkers(total_number_of_tasks, function, inputs, commands, minChunkSize = (multiprocessing.cpu_count() - 1), variables_names = []):
  
    '''Spawns workers to process the given function(values,inputs). The values 
       list wil be broken down into a number of chunks appropriate for the
       number of cores that can process it.
       
       Total number of task is a list of the tasks to be performed by function
               ie: values in function(values, input)
    
       By default, the number of processes it spawns is equal to the number of cores.
       To change it: pool = multiprocessing.pool(processes=4) would spawn 4 processes.
       To get the number of cores: multiprocessing.cpu_count() '''
    #getting the number of cores:
    num_cores = multiprocessing.cpu_count() - 1  
    
    #starting the workers
    pool = multiprocessing.Pool(processes = num_cores)
    
    #calculating the number of tasks
    ##number of processes
    nbr_pro = len(multiprocessing.active_children()) #redondant with num_cores, but left there to rmember the function later on
    
    ##calculating the number of chunks needed to have one chunk per process, but with a max number of simulations per chunk
    one_chunk_per_process = int(math.ceil(len(total_number_of_tasks)/float(nbr_pro)))    

    ##blocking the number of variables to 4 per Chunks   
    len_chunks = min(one_chunk_per_process, minChunkSize)  

    ##breaking into chunks without 'None' values
    if not variables_names:
        processed_chunks = cleanChunks(len_chunks, total_number_of_tasks)
    ##breaking into chunks keeping linked variables together        
    else:
        processed_chunks = intelligentChunks(len_chunks, total_number_of_tasks, variables_names)

    if commands.verbose:
        print ('    ###  Spawning additionnal processes    ### \n'
               'Number of cores:             ' + str(num_cores) + '\n'
               'Number or processes spawned: ' + str(nbr_pro) + '\n'
               '\n'
               '    ### Spliting the inputs into subgroups ### \n'
               'Number of subgroups: '+ str(len(processed_chunks)) + '\n'
               )
    
    #Assigning tasks
    if commands.multi_test is False:
        results_async = [pool.apply_async(function, [processed_chunks[i], inputs]) for i in range(len(processed_chunks))]
        pool.close()
        pool.join()
           
        results = [r.get() for r in results_async]
        
        return results
        
    else:
        #to test if there is a problem inside the called function
        for i in range(len(processed_chunks)):
            print function(processed_chunks[i], inputs)
            import pdb;pdb.set_trace()   

def cpuPerVissimInstance():
    '''calculates the number of vissim process to spawn depending on the amount of
       cpus present in the computer.
       
       The value of cores_per_process returned is the flat value to alocate the same
       amount of cpus to each vissim process. The unused_cores calculated could be
       redistributed to some of the processes and the number of simulations increased
       accordingly on those processes.
    '''
    num_cores = multiprocessing.cpu_count()
    if num_cores > 5:
        cores_per_process = (num_cores - 1) // 4
        number_of_process = 4
        unused_cores      = (num_cores - 1) % 4
    
    else:
        cores_per_process = 1
        number_of_process = num_cores - 1
        unused_cores      = 0
        
    return cores_per_process, number_of_process, unused_cores
        
#calculations of number of chunks to build
def countPoints(variable_names, points, sim):
    '''returns the min number of variables per chunks needed to have maximum 200 simulations per chunks
       200 simulations = 4 parameters * 5 points/para * 10 sim/points '''
    
    total_points = 0
    
    for var in variable_names:
        if var == "CoopLnChg":
            total_points += 2
        else:
            total_points += points
    
    total_sims = np.ceil(float(total_points)*sim/200)
    
    return int(np.ceil(len(variable_names)/total_sims))

def monteCarloCountPoints(points, sim):
    '''returns the min number of variables per chunks needed to have maximum 200 simulations per chunks
       200 simulations = 4 parameters * 5 points/para * 10 sim/points '''
    
    total_points = points*sim
    total_sims = np.ceil(float(total_points)*sim/200)
    
    return int(np.ceil(total_points/total_sims))
