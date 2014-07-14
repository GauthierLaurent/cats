# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:28:53 2014

@author: Laurent
"""
##################
# Import Native Libraries
##################
from itertools import izip, chain, repeat

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
    
def createFMValues(CarFollowModType, values = []):
    ''' CarFollowModType must be Wiedemann74 OR Wiedemann99 
       The following values are the default values. They could be changed latter on in the calibration process'''
    
    FMvalues = []
    FMvariables = []
    
    #Variables in Wiedemann 74
    W74ax = 2.0        #min = 0    
    W74bxAdd = 2.0
    W74bxMult = 3.0
    
    #Variables in Wiedemann 99
    W99cc0 = 1.5        #min = 0
    W99cc1 = 0.9
    W99cc2 = 4.0        #min = 0
    W99cc3 = -8.0
    W99cc4 = -0.35
    W99cc5 = 0.35
    W99cc6 = 11.44
    W99cc7 = 0.25
    W99cc8 = 3.5
    W99cc9 = 1.5
    
    #Other variables
    LookAheadDistMin = 0.0      #min = 0, max = 999999
    LookAheadDistMax = 250.0  #min = 0, max = 999999
    ObsrvdVehs = 2.0                #min = 0, max = 10
    LookBackDistMin = 0.0        #min = 0, max = 999999
    LookBackDistMax = 150.0    #min = 0, max = 999999
    
    if CarFollowModType == 74 :
        FMvariables.append('W74ax'),FMvariables.append('W74bxAdd'),FMvariables.append('W74bxMult')
        FMvalues.append(W74ax),FMvalues.append(W74bxAdd),FMvalues.append(W74bxMult)
        
    elif CarFollowModType == 99 :
        FMvariables.append('W99cc0'),FMvariables.append('W99cc1'),FMvariables.append('W99cc2')
        FMvariables.append('W99cc3'),FMvariables.append('W99cc4'),FMvariables.append('W99cc5')
        FMvariables.append('W99cc6'),FMvariables.append('W99cc7'),FMvariables.append('W99cc8')
        FMvariables.append('W99cc9')
        FMvalues.append(W99cc0),FMvalues.append(W99cc1),FMvalues.append(W99cc2)
        FMvalues.append(W99cc3),FMvalues.append(W99cc4),FMvalues.append(W99cc5)
        FMvalues.append(W99cc6),FMvalues.append(W99cc7),FMvalues.append(W99cc8)
        FMvalues.append(W99cc9)

    FMvariables.append('LookAheadDistMin'),FMvariables.append('LookAheadDistMax'),FMvariables.append('ObsrvdVehs')
    FMvariables.append('LookBackDistMin'),FMvariables.append('LookBackDistMax')
    FMvalues.append(LookAheadDistMin),FMvalues.append(LookAheadDistMax),FMvalues.append(ObsrvdVehs)
    FMvalues.append(LookBackDistMin),FMvalues.append(LookBackDistMax)
    
    return FMvalues, FMvariables       

def createLCValues(values = []):
    #Variables in LC behavior
    LCvalues = []
    LCvariables = []
    
    SafDistFactLnChg = 0.6
    MinHdwy = 0.5
    DiffusTm = 60
    CoopLnChg = False
    CoopLnChgSpeedDiff = 3.0 
    CoopLnChgCollTm = 10.0
    CoopDecel = -3.0              # min = -10    max = 0
    MaxDecelOwn = -4.0            # min = -10    max = -0.01
    MaxDecelTrail = -3.0          # min = -10    max = -0.01
    DecelRedDistOwn = 100         # min = 0
    DecelRedDistTrail = 100       # min = 0
    AccDecelOwn = -1.0            # min = -10    max = -1
    AccDecelTrail = -1.0          # min = -10    max = -1
    
    LCvariables.append('MaxDecelOwn'), LCvariables.append('DecelRedDistOwn'), LCvariables.append('AccDecelOwn'), LCvariables.append('MaxDecelTrail')
    LCvariables.append('DecelRedDistTrail'), LCvariables.append('AccDecelTrail'), LCvariables.append('DiffusTm'), LCvariables.append('MinHdwy')
    LCvariables.append('SafDistFactLnChg'), LCvariables.append('CoopLnChg'), LCvariables.append('CoopLnChgSpeedDiff'),
    LCvariables.append('CoopLnChgCollTm'), LCvariables.append('CoopDecel')
    
    if values != []:
        LCvalues = values
    else:
        LCvalues.append(MaxDecelOwn), LCvalues.append(DecelRedDistOwn), LCvalues.append(AccDecelOwn),  LCvalues.append(MaxDecelTrail)
        LCvalues.append(DecelRedDistTrail), LCvalues.append(AccDecelTrail), LCvalues.append(DiffusTm), LCvalues.append(MinHdwy)
        LCvalues.append(SafDistFactLnChg), LCvalues.append(CoopLnChg), LCvalues.append(CoopLnChgSpeedDiff),
        LCvalues.append(CoopLnChgCollTm), LCvalues.append(CoopDecel)   
    
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
    rangeLookAheadDistMin = [0.0     , 30.0] ; rangevalues.append(rangeLookAheadDistMin)        #min = 0, max = 999999
    rangeLookAheadDistMax = [200.0  , 300.0] ; rangevalues.append(rangeLookAheadDistMax)        #min = 0, max = 999999
    rangeObsrvdVehs =       [2.0     , 10.0] ; rangevalues.append(rangeObsrvdVehs)              #min = 0, max = 10
    rangeLookBackDistMin =  [0.0     , 30.0] ; rangevalues.append(rangeLookBackDistMin)         #min = 0, max = 999999
    rangeLookBackDistMax =  [100.0  , 200.0] ; rangevalues.append(rangeLookBackDistMax)         #min = 0, max = 999999            
                         
    ##Variables for lane change behavior
    rangeMaxDecelOwn =         [-10.0 , -0.01] ; rangevalues.append(rangeMaxDecelOwn)           #min = -10, max = -0.01
    rangeDecelRedDistOwn =     [100.0 , 100.0] ; rangevalues.append(rangeDecelRedDistOwn)       #min = 0
    rangeAccDecelOwn =         [-10.0 ,   0.0] ; rangevalues.append(rangeAccDecelOwn)           #min = -10, max = -1
    rangeMaxDecelTrail =       [-10.0 , -0.01] ; rangevalues.append(rangeMaxDecelTrail)         #min = -10, max = -0.01
    rangeDecelRedDistTrail =   [100.0 , 100.0] ; rangevalues.append(rangeDecelRedDistTrail)     #min = 0
    rangeAccDecelTrail =       [-10.0 ,   0.0] ; rangevalues.append(rangeAccDecelTrail)         #min = -10, max = -1
    rangeDiffusTm =            [60    , 100.0] ; rangevalues.append(rangeDiffusTm)
    rangeMinHdwy =             [0.5   ,   1.5] ; rangevalues.append(rangeMinHdwy)
    rangeSafDistFactLnChg =    [0.6   ,   0.9] ; rangevalues.append(rangeSafDistFactLnChg)
    rangeCoopLnChg =           [True  , False] ; rangevalues.append(rangeCoopLnChg)
    rangeCoopLnChgSpeedDiff =  [5.0   ,  15.0] ; rangevalues.append(rangeCoopLnChgSpeedDiff) 
    rangeCoopLnChgCollTm =     [7.0   ,  13.0] ; rangevalues.append(rangeCoopLnChgCollTm)
    rangeCoopDecel =           [-10.65,  -0.9] ; rangevalues.append(rangeCoopDecel)             #min = -10, max = 0

    return rangevalues    