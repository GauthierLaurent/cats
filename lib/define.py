# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:28:53 2014

@author: Laurent
"""
##################
# Import Libraries
##################
#Natives
from itertools import izip, chain, repeat
import multiprocessing
import math, sys

##################
# Define tools
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

def createWorkers(total_number_of_tasks, function, inputs, multi_test, variables_names = []):
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
    
    ##calculating the number of chunks needed to have one chunk per process
    ##this number won't actually be followed as this some variables might have
    ##to be taken out of the pool of variables to be kept together
    len_chunks = int(math.ceil(len(total_number_of_tasks)/float(nbr_pro)))
    
    ##breaking into chunks without 'None' values
    if not variables_names:
        processed_chunks = cleanChunks(len_chunks, total_number_of_tasks)
    else:
        processed_chunks = intelligentChunks(len_chunks, total_number_of_tasks, variables_names)
    
    #Assigning tasks
    if multi_test is False:
        results_async = [pool.apply_async(function, [processed_chunks[i], inputs]) for i in range(len(processed_chunks))]
        pool.close()
        pool.join()
           
        results = [r.get() for r in results_async]
        
        return results
        
    else:
        #to test if the is a a problem is the called function
        for i in range(len(processed_chunks)):
            print function(processed_chunks[i], inputs)
            import pdb;pdb.set_trace()   
    
def createFMValues(model):
    ''' CarFollowModType must be Wiedemann74 OR Wiedemann99 
       The following values are the default values. They could be changed latter on in the calibration process'''
    
    FMvalues = []
    FMvariables = []
    
    #Variables in Wiedemann 74
    if int(model) == 74 :
        W74ax = 2.0     ; FMvariables.append('W74ax')     ; FMvalues.append(W74ax)     #min = 0    
        W74bxAdd = 2.0  ; FMvariables.append('W74bxAdd')  ; FMvalues.append(W74bxAdd)
        W74bxMult = 3.0 ; FMvariables.append('W74bxMult') ; FMvalues.append(W74bxMult)
    
    #Variables in Wiedemann 99
    elif int(model) == 99 :
        W99cc0 = 1.5    ; FMvariables.append('W99cc0')    ; FMvalues.append(W99cc0)    #min = 0
        W99cc1 = 0.9    ; FMvariables.append('W99cc1')    ; FMvalues.append(W99cc1)
        W99cc2 = 4.0    ; FMvariables.append('W99cc2')    ; FMvalues.append(W99cc2)    #min = 0
        W99cc3 = -8.0   ; FMvariables.append('W99cc3')    ; FMvalues.append(W99cc3)
        W99cc4 = -0.35  ; FMvariables.append('W99cc4')    ; FMvalues.append(W99cc4)
        W99cc5 = 0.35   ; FMvariables.append('W99cc5')    ; FMvalues.append(W99cc5)
        W99cc6 = 11.44  ; FMvariables.append('W99cc6')    ; FMvalues.append(W99cc6)
        W99cc7 = 0.25   ; FMvariables.append('W99cc7')    ; FMvalues.append(W99cc7)
        W99cc8 = 3.5    ; FMvariables.append('W99cc8')    ; FMvalues.append(W99cc8)
        W99cc9 = 1.5    ; FMvariables.append('W99cc9')    ; FMvalues.append(W99cc9)
    
    #Other variables
    LookAheadDistMin = 0.0    ; FMvariables.append('LookAheadDistMin')  ; FMvalues.append(LookAheadDistMin)   #min = 0, max = 999999
    LookAheadDistMax = 250.0  ; FMvariables.append('LookAheadDistMax')  ; FMvalues.append(LookAheadDistMax)   #min = 0, max = 999999
    ObsrvdVehs = 2.0          ; FMvariables.append('ObsrvdVehs')        ; FMvalues.append(ObsrvdVehs)         #min = 0, max = 10
    LookBackDistMin = 0.0     ; FMvariables.append('LookBackDistMin')   ; FMvalues.append(LookBackDistMin)    #min = 0, max = 999999
    LookBackDistMax = 150.0   ; FMvariables.append('LookBackDistMax')   ; FMvalues.append(LookBackDistMax)    #min = 0, max = 999999
    
    return FMvalues, FMvariables       

def createLCValues():
    #Variables in LC behavior
    LCvalues = []
    LCvariables = []

    MaxDecelOwn = -4.0        ; LCvariables.append('MaxDecelOwn')         ; LCvalues.append(MaxDecelOwn)       # min = -10    max = -0.01    
   #DecelRedDistOwn = 100     ; LCvariables.append('DecelRedDistOwn')     ; LCvalues.append(DecelRedDistOwn)   # min = 0
    AccDecelOwn = -1.0        ; LCvariables.append('AccDecelOwn')         ; LCvalues.append(AccDecelOwn)       # min = -10    max = -1
    MaxDecelTrail = -3.0      ; LCvariables.append('MaxDecelTrail')       ; LCvalues.append(MaxDecelTrail)     # min = -10    max = -0.01
   #DecelRedDistTrail = 100   ; LCvariables.append('DecelRedDistTrail')   ; LCvalues.append(DecelRedDistTrail) # min = 0
    AccDecelTrail = -1.0      ; LCvariables.append('AccDecelTrail')       ; LCvalues.append(AccDecelTrail)     # min = -10    max = -1
    DiffusTm = 60             ; LCvariables.append('DiffusTm')            ; LCvalues.append(DiffusTm)
    MinHdwy = 0.5             ; LCvariables.append('MinHdwy')             ; LCvalues.append(MinHdwy)
    SafDistFactLnChg = 0.6    ; LCvariables.append('SafDistFactLnChg')    ; LCvalues.append(SafDistFactLnChg)
    CoopLnChg = False         ; LCvariables.append('CoopLnChg')           ; LCvalues.append(CoopLnChg)
    CoopLnChgSpeedDiff = 3.0  ; LCvariables.append('CoopLnChgSpeedDiff')  ; LCvalues.append(CoopLnChgSpeedDiff)
    CoopLnChgCollTm = 10.0    ; LCvariables.append('CoopLnChgCollTm')     ; LCvalues.append(CoopLnChgCollTm)
    CoopDecel = -3.0          ; LCvariables.append('CoopDecel')           ; LCvalues.append(CoopDecel)         # min = -10    max = 0
        
    return LCvalues, LCvariables
    
def buildRanges(model):
    rangevalues = []
       
    ##Variables in Wiedemann 74   [min,max]
    if int(model) == 74:        
        rangeW74ax     = [2.0, 4.0] ; rangevalues.append(rangeW74ax)      #min = 0    
        rangeW74bxAdd  = [2.0, 4.0] ; rangevalues.append(rangeW74bxAdd)
        rangeW74bxMult = [3.0, 4.0] ; rangevalues.append(rangeW74bxMult)
    
    ##Variables in Wiedemann 99   [min,max]
    elif int(model) == 99: 
        rangeW99cc0 = [0.47   , 12.0] ; rangevalues.append(rangeW99cc0)   #min = 0
        rangeW99cc1 = [0.43   , 3.00] ; rangevalues.append(rangeW99cc1)
        rangeW99cc2 = [0.0    , 15.0] ; rangevalues.append(rangeW99cc2)   #min = 0
        rangeW99cc3 = [-30.0  , 0.00] ; rangevalues.append(rangeW99cc3)
        rangeW99cc4 = [-2.0   , 2.00] ; rangevalues.append(rangeW99cc4)
        rangeW99cc5 = [-0.35  , 2.00] ; rangevalues.append(rangeW99cc5)
        rangeW99cc6 = [0.00   , 20.0] ; rangevalues.append(rangeW99cc6)
        rangeW99cc7 = [0.00   , 1.25] ; rangevalues.append(rangeW99cc7)
        rangeW99cc8 = [1.6    , 13.0] ; rangevalues.append(rangeW99cc8)
        rangeW99cc9 = [1.5    , 7.00] ; rangevalues.append(rangeW99cc9)

    ##Other variables for the following behavior model     
    rangeLookAheadDistMin = [0.0    ,  30.0] ; rangevalues.append(rangeLookAheadDistMin)        #min = 0, max = 999999
    rangeLookAheadDistMax = [200.0  , 300.0] ; rangevalues.append(rangeLookAheadDistMax)        #min = 0, max = 999999
    rangeObsrvdVehs =       [2.0    ,  10.0] ; rangevalues.append(rangeObsrvdVehs)              #min = 0, max = 10
    rangeLookBackDistMin =  [0.0    ,  30.0] ; rangevalues.append(rangeLookBackDistMin)         #min = 0, max = 999999
    rangeLookBackDistMax =  [100.0  , 200.0] ; rangevalues.append(rangeLookBackDistMax)         #min = 0, max = 999999            
                         
    ##Variables for lane change behavior
    rangeMaxDecelOwn =         [-10.0 , -0.01] ; rangevalues.append(rangeMaxDecelOwn)           #min = -10, max = -0.01
   #rangeDecelRedDistOwn =     [100.0 , 100.0] ; rangevalues.append(rangeDecelRedDistOwn)       #min = 0
    rangeAccDecelOwn =         [-10.0 ,   0.0] ; rangevalues.append(rangeAccDecelOwn)           #min = -10, max = -1
    rangeMaxDecelTrail =       [-10.0 , -0.01] ; rangevalues.append(rangeMaxDecelTrail)         #min = -10, max = -0.01
   #rangeDecelRedDistTrail =   [100.0 , 100.0] ; rangevalues.append(rangeDecelRedDistTrail)     #min = 0
    rangeAccDecelTrail =       [-10.0 ,   0.0] ; rangevalues.append(rangeAccDecelTrail)         #min = -10, max = -1
    rangeDiffusTm =            [60    , 100.0] ; rangevalues.append(rangeDiffusTm)
    rangeMinHdwy =             [0.5   ,   1.5] ; rangevalues.append(rangeMinHdwy)
    rangeSafDistFactLnChg =    [0.6   ,   0.9] ; rangevalues.append(rangeSafDistFactLnChg)
    rangeCoopLnChg =           [True  , False] ; rangevalues.append(rangeCoopLnChg)
    rangeCoopLnChgSpeedDiff =  [5.0   ,  15.0] ; rangevalues.append(rangeCoopLnChgSpeedDiff) 
    rangeCoopLnChgCollTm =     [7.0   ,  13.0] ; rangevalues.append(rangeCoopLnChgCollTm)
    rangeCoopDecel =           [-10.65,  -0.9] ; rangevalues.append(rangeCoopDecel)             #min = -10, max = 0

    return rangevalues
    
def verifyRanges(rangevalues, variables):
    
    closing = False    
    for i in range(len(rangevalues)):
        if variables[i] == "W74ax":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for W74ax not respected | min = 0 | Closing PvcTools"
                closing = True
            
        if variables[i] == "W99cc0":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for W99cc0 not respected | min = 0 | Closing PvcTools"
                closing = True
                       
        if variables[i] == "W99cc2":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for W99cc2 not respected | min = 0 | Closing PvcTools"
                closing = True
            
        if variables[i] == "LookAheadDistMin":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for LookAheadDistMin not respected | min = 0 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > 999999.0:
                print "Maximum value for LookAheadDistMin not respected | max = 999999 | Closing PvcTools"
                closing = True        
                
        if variables[i] == "LookAheadDistMax":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for LookAheadDistMax not respected | min = 0 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > 999999.0:
                print "Maximum value for LookAheadDistMax not respected | max = 999999 | Closing PvcTools"
                closing = True  
                
        if variables[i] == "ObsrvdVehs":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for ObsrvdVehs not respected | min = 0 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > 10.0:
                print "Maximum value for ObsrvdVehs not respected | max = 10 | Closing PvcTools"
                closing = True 
                
        if variables[i] == "LookBackDistMin":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for LookBackDistMin not respected | min = 0 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > 999999.0:
                print "Maximum value for LookBackDistMin not respected | max = 999999 | Closing PvcTools"
                closing = True
                
        if variables[i] == "LookBackDistMax":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for LookBackDistMax not respected | min = 0 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > 999999.0:
                print "Maximum value for LookBackDistMax not respected | max = 999999 | Closing PvcTools"
                closing = True
                
        if variables[i] == "MaxDecelOwn":
            if rangevalues[i][0] < -10.0:
                print "Minimal value for MaxDecelOwn not respected | min = -10 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > -0.02:
                print "Maximum value for MaxDecelOwn not respected | max = -0.01* but Vissim refuses it, blocking any values higher than -0.02 | Closing PvcTools"
                closing = True
                
        if variables[i] == "DecelRedDistOwn":
            if rangevalues[i][0] < 0.0:
                print "Minimal value for DecelRedDistOwn not respected | min = 0 | Closing PvcTools"
                closing = True
                
        if variables[i] == "AccDecelOwn":
            if rangevalues[i][0] < -10.0:
                print "Minimal value for AccDecelOwn not respected | min = -10 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > -1.0:
                print "Maximum value for AccDecelOwn not respected | max = -1 | Closing PvcTools"
                closing = True
                
        if variables[i] == "MaxDecelTrail":
            if rangevalues[i][0] < -10.0:
                print "Minimal value for MaxDecelTrail not respected | min = -10 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > -0.02:
                print "Maximum value for MaxDecelTrail not respected | max = -0.01* but Vissim refuses it, blocking any values higher than -0.02 | Closing PvcTools"
                closing = True
                
        if variables[i] == "DecelRedDistTrail":   
            if rangevalues[i][0] < 0.0:
                print "Minimal value for DecelRedDistTrail not respected | min = 0 | Closing PvcTools"
                closing = True
                
        if variables[i] == "AccDecelTrail": 
            if rangevalues[i][0] < -10.0:
                print "Minimal value for AccDecelTrail not respected | min = -10 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > -1.0:
                print "Maximum value for AccDecelTrail not respected | max = -1 | Closing PvcTools"
                closing = True
                
        if variables[i] == "CoopDecel": 
            if rangevalues[i][0] < -10.0:
                print "Minimal value for CoopDecel not respected | min = -10 | Closing PvcTools"
                closing = True        
            if rangevalues[i][1] > -0.0:
                print "Maximum value for CoopDecel not respected | max = 0 | Closing PvcTools"
                closing = True
                
    if closing == True:
        sys.exit()