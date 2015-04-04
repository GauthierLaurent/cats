# -*- coding: utf-8 -*-
'''
Created on Tue Mar 03 16:18:06 2015

@author: Laurent
'''

from itertools import izip, chain, repeat
import multiprocessing, math
import numpy as np

################################ 
#        Misc tools     
################################
class FalseCommands:
    '''this serves only to spoof the worker function'''
    def __init__(self):
        self.verbose    = False
        self.multi_test = False
        
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

def cleanChunks(n, iterable, asList=True):
    '''Splits an iterable into chunks of n size using the toChunks function but
       removes the padvalue'''
    chunks = toChunks(n, iterable, padvalue='TO_REMOVE', asList = asList)     
    for i in xrange(len(chunks)):
        for j in reversed(xrange(len(chunks[i]))):
            if chunks[i][j] == 'TO_REMOVE':
                chunks[i].pop(j)
    return chunks
    
def intelligentChunks(n, iterable, value_names):
    '''Cuts the variables into chunks keeping together the variables that need
       to relate to others'''           
    
    intelligent_chunk = []
    if len(iterable) != n:
        keepAssembled_g1 = ('LookAheadDistMin','LookAheadDistMax','LookBackDistMin','LookBackDistMax')    
        keepAssembled_g2 = ('CoopLnChg','CoopLnChgSpeedDiff','CoopLnChgCollTm')    

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
            clean_chunks = cleanChunks(n, other_iterables, asList=True)
            for i in range(len(clean_chunks)): intelligent_chunk.append(clean_chunks[i])
    else:
        for i in range(len(iterable)):
            intelligent_chunk.append([iterable[i],i])
    
    return intelligent_chunk

def createWorkers(total_number_of_tasks, function, inputs, commands, minChunkSize = (multiprocessing.cpu_count() - 1), variables_names = [], defineNbrProcess = False, defineChunkSize = False):
  
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
    if defineNbrProcess is False and defineChunkSize is False:
        nbr_pro = len(multiprocessing.active_children()) #redondant with num_cores, but left there to rmember the function later on

        ##calculating the number of chunks needed to have one chunk per process, but with a max number of simulations per chunk
        one_chunk_per_process = int(math.ceil(len(total_number_of_tasks)/float(nbr_pro))) 
    
        ##blocking the number of variables to 4 per Chunks   
        len_chunks = min(one_chunk_per_process, minChunkSize)

    elif not isinstance(defineNbrProcess, bool) and isinstance(defineChunkSize, bool):
        nbr_pro = defineNbrProcess
        
        len_chunks = int(math.ceil(len(total_number_of_tasks)/float(nbr_pro)))

    elif isinstance(defineNbrProcess, bool) and not isinstance(defineChunkSize, bool):
        len_chunks = defineChunkSize

        nbr_pro = np.ceil(float(len_chunks)/len(total_number_of_tasks))
        
    else:
        nbr_pro = max(defineNbrProcess, np.ceil(float(defineChunkSize)/len(total_number_of_tasks)))

    ##breaking into chunks without 'None' values
    if variables_names == []:
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
        if var == 'CoopLnChg':
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