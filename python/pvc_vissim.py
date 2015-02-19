# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:25:24 2014

@author: Laurent
"""
##################
# Import Native Libraries
##################

import psutil, sys
import win32com.client

##################
# Vissim management tools
##################

def isVissimRunning(kill):
    '''This function is used to verify if the Vissim program is running
       The first time it is called in the program, firstTime should be called
       as True:
       This is to make sure Vissim was not left open in non COM mode before
       starting the python program
    '''
    running = False
    
    # Go through list and check each processes executeable name for 'Vissim.exe'
    for p in psutil.get_process_list():
        try:
            if p.name == 'VISSIM.exe':
                if kill is True:
                    # killing Vissim so it can be restarted with the COM module enabled
                    p.kill()
                else:
                    running = True
        except:
            pass             
    return running

def startVissim():
    '''start an instance of Vissim. Returns the object Vissim if successfull,
       StartError otherwise'''
    try:
        return win32com.client.dynamic.Dispatch("Vissim.Vissim.600")
        #Note: win32com.client.dynamic.Dispatch() works both with an open or unopened vissim. It can be called multiple
        #                                         times, and will first assign already opened instances, then start new ones
        #      win32com.client.Dispatch() will ignore already opened vissim instances and start a fresh one
    except:
        return 'StartError'
        
   
def loadNetwork(Vissim, InpxPath):
    '''start a Vissim network. Returns True if successfull, LoadNetError otherwise
       The filename MUST have a capital first letter'''
    if Vissim is not False and Vissim is not 'StartError':
        try:
            Vissim.LoadNet (InpxPath)
            return True
        except:
           return 'LoadNetError'

def stopVissim(Vissim):
    '''Closes the current instance of Vissim. Return True if successfull, False otherwise'''
    try:
        Vissim.Exit()
    except:
        sys.exc_info()
    if isVissimRunning(True):
        return False
    else:
        return True
        
def initializeSimulation(Vissim, sim_parameters, values, parameters, swp = False):          #Change Lane parameters need to be added
    ''' Defines the Vissim Similuation parameters
        the sim_parameters variables must be [simulationStepsPerTimeUnit,
        first_seed, nbr_runs, CarFollowModType, Simulation lenght]'''    

    try:
        Simulation = Vissim.Simulation
        Evaluation = Vissim.Evaluation
        
        if Simulation.AttValue("IsRunning") is True:
            Simulation.Stop()
        
        #Setting Simulation attributes        
        Simulation.SetAttValue("SimRes", sim_parameters[0])         #ODOT p.45 (56 in the pdf)
        Simulation.SetAttValue("useMaxSimSpeed", True)
        Simulation.SetAttValue("RandSeed", sim_parameters[1])       #Hitchhiker's Guide to the Galaxy!
        Simulation.SetAttValue("RandSeedIncr", sim_parameters[5])
        Simulation.SetAttValue("NumRuns", sim_parameters[2])        #To be verified
        Simulation.SetAttValue("SimPeriod",sim_parameters[3])
        
        #Setting the number of cores to use
        Simulation.SetAttValue("NumCores",sim_parameters[4])       
        
        #Enabling the Quick Mode
        Vissim.graphics.currentnetworkwindow.SetAttValue("QuickMode", True)
        
        #Setting Evaluation outputs
        Evaluation.SetAttValue("VehRecWriteFile",True)               #Enable .fzp outputs
        if swp: Evaluation.SetAttValue("LaneChangesWriteFile",True)  #Enable .swp outputs
        
        #Setting driving behavior attributes
        if sim_parameters[3] is not None:
            for i in xrange(len(Vissim.Net.DrivingBehaviors)):                       
                for variable in xrange(len(parameters)):
                    if caracterizedParameter('DrivingBehaviors', parameters[variable]):
                        Vissim.Net.DrivingBehaviors[i].SetAttValue(parameters[variable].vissim_name,values[variable])
                 
        #Starting the simulation            
        Simulation.RunContinuous()
        
        simulated = True        
    except:
        simulated = sys.exc_info()
        
    return simulated
    
def caracterizedParameter(param_type, parameter):
    '''function used to assign parameters to the correct Vissim COM method
        -> this will be usefull to expand pvctools to other type of study than
           DrivingBehaviors related studies
           
           checks if the parameter is in the type of variables, returns True or False
    '''
    drivingBehaviors_list = ['W74ax','W74bxAdd', 'W74bxMult',
                             'W99cc0','W99cc1','W99cc2','W99cc3','W99cc4','W99cc5','W99cc6','W99cc7','W99cc8','W99cc9',
                             'LookAheadDistMin','LookAheadDistMax','ObsrvdVehs','LookBackDistMin','LookBackDistMax',
                             'MaxDecelOwn','DecelRedDistOwn','AccDecelOwn','MaxDecelTrail','DecelRedDistTrail','AccDecelTrail','DiffusTm','MinHdwy','SafDistFactLnChg','CoopLnChg','CoopLnChgSpeedDiff','CoopLnChgCollTm','CoopDecel'
                             ]
                             
    if param_type == 'DrivingBehaviors':
        if parameter.vissim_name in drivingBehaviors_list:
            return True
        else:
            return False

def weidemannCheck(model, parameters):
    '''returns the parameters that are not part of the other wiedemann model than
       the one specified. If None is passed for the model type, every parameters
       will be returned   - Presently unused'''
       
    weidemann74 = ['W74ax','W74bxAdd', 'W74bxMult']
    weidemann99 = ['W99cc0','W99cc1','W99cc2','W99cc3','W99cc4','W99cc5','W99cc6','W99cc7','W99cc8','W99cc9']    

    output = []    
    for i in xrange(len(parameters)):
        if model == 74:
            if parameters[i].vissim_name in weidemann99:
                pass
            else:
                output.append(parameters[i])

        elif model == 99:
            if parameters[i].vissim_name in weidemann74:
                pass
            else:
                output.append(parameters[i])
    return output
    
#######   Under developpement  ############
class vissimParameters:
    def __init__(self,vissim_name,vissim_min, vissim_max, vissim_default, param_type):
        self.vissim_name    = vissim_name
        self.vissim_min     = vissim_min
        self.vissim_max     = vissim_max
        self.vissim_default = vissim_default
        self.param_type     = param_type
        
def vissimDictionnary():
    values = {}
    
    #Wiedemann 74
    values.append(vissimParameters('W74ax',      0.0,   None,    2.0,   'DrivingBehaviors'))
    values.append(vissimParameters('W74bxAdd',   0.0,   None,    2.0,   'DrivingBehaviors'))
    values.append(vissimParameters('W74bxMult',  0.0,   None,    3.0,   'DrivingBehaviors'))
    
    #Wiedemann 99
    values.append(vissimParameters('W99cc0',     0.0,   None,    1.5,   'DrivingBehaviors'))
    values.append(vissimParameters('W99cc1',    None,   None,    0.9,   'DrivingBehaviors'))
    values.append(vissimParameters('W99cc2',     0.0,   None,    4.0,   'DrivingBehaviors'))
    values.append(vissimParameters('W99cc3',    None,   None,   -8.0,   'DrivingBehaviors'))
    values.append(vissimParameters('W99cc4',    None,   None,   -0.35,  'DrivingBehaviors'))
    values.append(vissimParameters('W99cc5',    None,   None,    0.35,  'DrivingBehaviors'))
    values.append(vissimParameters('W99cc6',    None,   None,   11.44,  'DrivingBehaviors'))
    values.append(vissimParameters('W99cc7',    None,   None,    0.25,  'DrivingBehaviors'))
    values.append(vissimParameters('W99cc8',    None,   None,    3.5 ,  'DrivingBehaviors'))
    values.append(vissimParameters('W99cc9',    None,   None,    1.5 ,  'DrivingBehaviors'))
    
    #general following behavior
    
    #general lane change
    
    
    