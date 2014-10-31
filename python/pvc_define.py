# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:28:53 2014

@author: Laurent
"""

#this will be used to verify if the serialised data is still matching the data processsed by pcvtools
def version():
    '''
    version is RX.Y.Z u. DD-MM-AAAA
    where:
            X is the release version
            Y is the serialized data version
            Z is the subrelease update version
    '''
    return 'R1.3.0 u. 29-10-2014'
    
def verify_release_version(in_version):
    '''looks for the X part of the version number'''
    if in_version.split('.')[0] == version().split('.')[0]:
        return True
    else:
        return False 

def verify_data_version(in_version):
    '''looks for the Y part of the version number'''
    if in_version.split('.')[1] == version().split('.')[1]:
        return True
    else:
        return False 
        
##################
# Import Libraries
##################
#Natives
from itertools import izip, chain, repeat, product
from pylab import csv2rec
import multiprocessing, random
import math, sys, os
import numpy as np
import cPickle as pickle
import StringIO

##################
# Import Traffic Intelligence
##################
#disabling outputs
import nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import moving
sys.stdout = oldstdout #Re-enable output

##################
# Read file data tools
##################
def loadDataFromTraj(path, filename):
    with open(os.path.join(path, filename), 'rb') as input_data:
        trajversion = pickle.dump(input_data)
        if verify_data_version(trajversion): 
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
                inter = brute[vid][b].split(';')[1].replace(' ','')
                inter = [inter.replace(')','').replace('(','')]

                point = []
                while len(inter) > 0:
                    inter = inter[0].split(',',2)
                    point.append(moving.Point(float(inter[0]),float(inter[1])))
                    inter = inter[2:]           
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
    def __init__(self, name = None, vissim_name = None, vissim_min = None, vissim_max = None, vissim_default = None, desired_min = None, desired_max = None, point = None):
        self.name           = name
        self.vissim_name    = vissim_name
        self.vissim_default = floatOrBool(vissim_default)
        self.desired_min    = floatOrBool(desired_min)
        self.desired_max    = floatOrBool(desired_max)
        self.vissim_min     = floatOrNone(vissim_min)
        self.vissim_max     = floatOrNone(vissim_max)
        self.point          = floatOrNone(point)

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
    
def verifyDesiredPoints(variables):
    chk = True
    for i in xrange(len(variables)):
        if variables[i].vissim_min is not None:
            if variables[i].point < variables[i].vissim_min:
                chk = False
        
        if variables[i].vissim_max is not None:    
            if variables[i].point > variables[i].vissim_max:
                chk = False
                
    return chk

def writeAlignToCSV(dirname, inpxname, video_name, text_to_add):
    '''inserts the info for the video in the CSV file respecting, if applicable, the
       location of the $Video_alignments section and keeping, if applicable, other
       videos' informations'''
    def add_end(list_to_append, video_name, text_to_add):
        for i in xrange(len(text_to_add)):
            list_to_append += [str(i)+';']
            for j in xrange(len(text_to_add[i])):
                if j == len(text_to_add[i])-1:
                    list_to_append += [str(text_to_add[i][j])+'\n']
                else:
                    list_to_append += [str(text_to_add[i][j])+',']
        list_to_append += ['\n']
        return list_to_append
    
    if inpxname in dirname: dirname = dirname.strip(inpxname)
    if os.path.exists(os.path.join(dirname, inpxname.strip('.inpx') + '.csv')):
           
        with open(os.path.join(dirname, inpxname.strip('.inpx') + '.csv'), 'r+') as f:
            
            text_list = []
            
            for l in f:
                text_list.append(l)

            to_write_list = []
            
            for line in xrange(len(text_list)):
                if 'Video_alignments' in text_list[line]:                  
                    #$Video_alignments does exist, we must modify this section
                    section_list = []
                    for lines in xrange(line+1,len(text_list)):
                        if '$' in text_list[lines]:
                            last_line = lines
                            break
                        section_list.append(text_list[lines])                    
                    
                    modified_section_list = []
                    index_list = []
                    found = False
                    for sec in xrange(len(section_list)):
                        if '.sqlite' in section_list[sec]:
                            index_list.append(sec)
                        if video_name in section_list[sec]:
                            found = sec
                            
                    #no video of that name found
                    if found is False:
                        modified_section_list.append('$Video_alignments\n')
                        modified_section_list += section_list[0:found]
                        modified_section_list.append(str(video_name)+'\n')
                        modified_section_list = add_end(modified_section_list, video_name, text_to_add)
                                       
                    #name found, overwritting this section
                    else:
                        #adding the first part
                        modified_section_list.append('$Video_alignments\n')
                        modified_section_list += section_list[0:found]

                        #adding the values we are interested in                                                
                        modified_section_list.append(str(video_name)+'\n')
                        modified_section_list = add_end(modified_section_list, video_name, text_to_add)

                        #adding the last part if it exists
                        if found < index_list[-1]:
                            modified_section_list += section_list[index_list[index_list.index(found)+1]:]

                    #adding modified section and rest of the file
                    to_write_list += modified_section_list
                    to_write_list += text_list[last_line:]
                    break
                
                elif line == len(text_list) -1:
                    #No section $Video_alignments found, we must create it
                    to_write_list.append(text_list[line])
                    if text_list[line] != '\n':
                        if '\n' in text_list[line]:
                            to_write_list.append('\n')
                        else:
                            to_write_list.append('\n\n')
                    to_write_list.append('$Video_alignments\n')
                    to_write_list.append(str(video_name)+'\n')
                    to_write_list = add_end(to_write_list, video_name, text_to_add)

                else:
                    to_write_list.append(text_list[line])

        f.close()
        
        with open(os.path.join(dirname, inpxname.strip('.inpx') + '.csv'), 'w') as f:
              for i in to_write_list:
                  f.write(i)
        f.close()

################################ 
#        Serialized data files     
################################
def write_traj(depositpath,name,opp_LC_count,man_LC_count,flow,forward_gaps,opp_LC_agaps,opp_LC_bgaps,man_LC_agaps,man_LC_bgaps,forwar_speed):
    '''dumps data into a file named name.traj in the folder provided in depositpath'''    
    with open(os.path.join(depositpath, name + '.traj'), 'wb') as output:       
        pickle.dump(version(),    output, protocol=2)
        pickle.dump(opp_LC_count, output, protocol=2)
        pickle.dump(man_LC_count, output, protocol=2)
        pickle.dump(flow,         output, protocol=2)
        pickle.dump(forward_gaps, output, protocol=2)
        pickle.dump(opp_LC_agaps, output, protocol=2)
        pickle.dump(opp_LC_bgaps, output, protocol=2)
        pickle.dump(man_LC_agaps, output, protocol=2)
        pickle.dump(man_LC_bgaps, output, protocol=2)
        pickle.dump(forwar_speed, output, protocol=2)

def load_traj(fullpath):
    '''loads data from the traj file provided in full path
    full path must end with \name.traj'''
    with open(fullpath, 'r') as input_file:
        version      = pickle.load(input_file)
        opp_LC_count = pickle.load(input_file)
        man_LC_count = pickle.load(input_file)
        flow         = pickle.dump(input_file)
        forward_gaps = pickle.load(input_file)
        opp_LC_agaps = pickle.load(input_file)
        opp_LC_bgaps = pickle.load(input_file)
        man_LC_agaps = pickle.load(input_file)
        man_LC_bgaps = pickle.load(input_file)
        forwar_speed = pickle.load(input_file)
        
    if version == version():
        return [opp_LC_count, man_LC_count, flow, forward_gaps, opp_LC_agaps, opp_LC_bgaps, man_LC_agaps, man_LC_bgaps, forwar_speed]
    else:
        return ['TrajVersionError']
        
################################ 
#        Network Calibration class       
################################
class Network:
    def __init__(self,inpx_path,traj_path_list):
        self.inpx_path = inpx_path

        if isinstance(traj_path_list, list):
            self.traj_paths = traj_path_list
        else:
            self.traj_paths = [traj_path_list] 

        
    def addtraj(self,traj):
        self.traj_paths = self.traj_paths + [traj]
                       
    def addCorridor(self, corridor):
        self.corridors = corridor
        
    def addVissim(self, vissim):
        self.vissim = vissim
        
    def addVideoComparison(self,data_list):
        try:
            self.videoComparison.append(data_list)
        except:
            self.videoComparison = data_list        
        
def buildNetworkObjects(config):
    '''takes all info from calib.cfg and build a network object out of it. This fonction will not duplicate a
    network that has been entered multiple times to be processed on two different videos files'''
    
    inpx_list = {}
    if config.active_network_1:
        inpx_list[config.path_to_inpx_1.split(os.sep)[-1]] = Network(config.path_to_inpx_1,config.path_to_video_data_1)
        VissimCorridors1, trafIntCorridors1 = extractVissimCorridorsFromCSV(config.path_to_csv_net1, config.path_to_csv_net1.split(os.sep)[-1])
        inpx_list[config.path_to_inpx_1.split(os.sep)[-1]].addCorridor(VissimCorridors1)
        
    if config.active_network_2:
        if config.path_to_inpx_2.split(os.sep)[-1] not in inpx_list:
            inpx_list[config.path_to_inpx_2.split(os.sep)[-1]] = Network(config.path_to_inpx_2,config.path_to_video_data_2)
            VissimCorridors2, trafIntCorridors2 = extractVissimCorridorsFromCSV(config.path_to_csv_net2, config.path_to_csv_net2.split(os.sep)[-1])
            inpx_list[config.path_to_inpx_2.split(os.sep)[-1]].addCorridor(VissimCorridors2)
        else:
            inpx_list[config.path_to_inpx_2.split(os.sep)[-1]].addtraj(config.path_to_video_data_2)
            
    if config.active_network_3:
        if config.path_to_inpx_3.split(os.sep)[-1] not in inpx_list:
            inpx_list[config.path_to_inpx_3.split(os.sep)[-1]] = Network(config.path_to_inpx_3,config.path_to_video_data_3)
            VissimCorridors3, trafIntCorridors3 = extractVissimCorridorsFromCSV(config.path_to_csv_net3, config.path_to_csv_net3.split(os.sep)[-1])
            inpx_list[config.path_to_inpx_3.split(os.sep)[-1]].addCorridor(VissimCorridors3)
        else:
            inpx_list[config.path_to_inpx_3.split(os.sep)[-1]].addtraj(config.path_to_video_data_3)    

    if config.active_network_4:
        if config.path_to_inpx_4.split(os.sep)[-1] not in inpx_list:
            inpx_list[config.path_to_inpx_4.split(os.sep)[-1]] = Network(config.path_to_inpx_4,config.path_to_video_data_4)
            VissimCorridors4, trafIntCorridors4 = extractVissimCorridorsFromCSV(config.path_to_csv_net4, config.path_to_csv_net4.split(os.sep)[-1])
            inpx_list[config.path_to_inpx_4.split(os.sep)[-1]].addCorridor(VissimCorridors4)
        else:
            inpx_list[config.path_to_inpx_4.split(os.sep)[-1]].addtraj(config.path_to_video_data_4)    
        
    return inpx_list.values()  
        
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

##################
# Sampling tools
##################

def genMCsample(variables, n):
    '''generates a Monte Carlo sample of n points'''
    valuesVector = []
    for i in xrange(n):
        thisVector = []
        laneChangeState = random.randrange(0,2)
        for j in xrange(len(variables)):
            if variables[j].vissim_name not in ['CoopLnChg','CoopLnChgSpeedDiff','CoopLnChgCollTm']:
                thisVector.append(random.uniform(variables[j].desired_min,variables[j].desired_max))
            else:
                if variables[j].vissim_name == 'CoopLnChg':
                    if laneChangeState == 1:
                        thisVector.append(True)
                    else:
                        thisVector.append(False)
                else:
                    if laneChangeState == 1:
                        thisVector.append(random.uniform(variables[j].desired_min,variables[j].desired_max))
                    else:
                        thisVector.append(999999)
        valuesVector.append(thisVector)
    return valuesVector

def choose(n):
    '''returns a list of n intergers randomly order from the range 0 to n-1'''
    final = []
    for i in xrange(n):
        chosen = False        
        while chosen is False:
            test = random.randint(0,n-1)
            if test not in final:
                chosen = True
                final.append(test)       
    return final
    
def choose_xn(n,m):
    '''chooses n points m times'''
    mat = []    
    for i in xrange(m):
        mat.append(choose(n))
    
    return mat
    
def boolTable(n):
    out = []
    for args in product(*repeat((True, False),n)):
        out.append(list(args))
    return out
    
def genLHCsample(variables,n):
    '''generates a Latin Hypercube sample of n points per non boolean dimension
       variables can be either boolean or real number values
       
       returns all combinations of real values (nxn matrix) for the True and False
       possibility of each boolean variable
        
       total number of points returned = ( len(real variables) )*(  2 ** len(bool variables) )
    '''        
    real_dim = []
    disc_dim = []
    
    #classification of boolean and nonboolean variables
    ranges = []
    for var in xrange(len(variables)):
        ranges.append([variables[var].desired_min, variables[var].desired_max])
        if isinstance(variables[var].desired_max, bool):
            disc_dim.append(var)
        else:
            real_dim.append(var)
    
    #subdivision of the ranges of each nonboolean variable
    cut_ranges =  []
    for i in real_dim:
        this_one_range = []   
        for j in xrange(n):
            this_one_range.append([ranges[i][0] + j * (ranges[i][1]-ranges[i][0])/float(n), ranges[i][0] + (j+1) * (ranges[i][1]-ranges[i][0])/float(n)])
        cut_ranges.append(this_one_range)

    #column,row selection
    mat = choose_xn(n,len(real_dim))

    #real values variable point selection
    real_mat = []
    for m in xrange(n):
        point = []
        for k in xrange(len(real_dim)):
            point.append(random.uniform(cut_ranges[k][mat[k][m]][0],cut_ranges[k][mat[k][m]][1]))
        real_mat.append(point)   

    #bool values combinations enumeration
    bool_mat = boolTable(len(disc_dim))

    #assembly line
    #TODO: apply corrections to variables affected by True/False value of the bool variable
    final_mat = []
    for i in xrange(len(bool_mat)):
        semi_mat = []
        for k in xrange(len(real_mat)):
            point = []                
            for m in xrange(len(variables)):
                if m in disc_dim:
                    point.append(bool_mat[i][disc_dim.index(m)])
                else:
                    point.append(real_mat[k][real_dim.index(m)])
            semi_mat.append(point)
        final_mat += semi_mat

    return final_mat
            
    