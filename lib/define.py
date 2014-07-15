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
import math

#Internals
import lib.analysis as analysis


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

def createWorkers(total_number_of_tasks, function, inputs):
    '''Spawns workers to process the given function(values,inputs). The values 
       list wil be broken down into a number of chunks appropriate for the
       number of cores that can process it
    
       By default, the number of processes it spawns is equal to the number of cores.
       To change it: pool = multiprocessing.pool(processes=4) would spawn 4 processes.
       To get the number of cores: multiprocessing.cpu_count() '''
    
    #starting the workers
    pool = multiprocessing.Pool()
    
    #calculating the number of tasks
    ##number of processes
    nbr_pro = len(multiprocessing.active_children())
    
    ##calculating the number of chunks needed to have one chunk per process
    len_chunks = int(math.ceil(len(total_number_of_tasks)/float(nbr_pro)))
    
    ##breaking into chunks without 'None' values
    clean_chunks = cleanChunks(len_chunks, total_number_of_tasks)
    
    #Assigning tasks
    results_async = [pool.apply_async(function, [clean_chunks[i], inputs]) for i in range(len(clean_chunks))]
    pool.close()
    pool.join()
    
    results = [r.get() for r in results_async]

    return results
    
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
        rangeW74ax        = [2.0, 4.0]                       #min = 0    
        rangeW74bxAdd  = [2.0, 4.0]
        rangeW74bxMult  = [3.0, 4.0]
        
        rangevalues.append(rangeW74ax,rangeW74bxAdd,rangeW74bxMult)
    
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