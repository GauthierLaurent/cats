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
       The first time it is called in the program, firstTime should be called as True:
       This is to make sure Vissim was not left open in non COM mode before starting the python program
    '''
    running = False    
    list = psutil.get_pid_list()

    # Go through list and check each processes executeable name for 'Vissim.exe'
    for i in range(0, len(list)):
        try:
            p = psutil.Process(list[i])
            if p.cmdline[0].find("Vissim.exe") != -1:
                if kill is True:                
                    # killing Vissim so it can be restarted with the COM module enabled
                    p.kill()
                else:
                    running = p
                break;
        except:
            pass       
    return running

def startVissim(running, InpxPath):
    '''start an instance of Vissim. Return the object Vissim if successfull, False otherwise'''

    Vissim = False
    if running is False:
        try:
            Vissim = win32com.client.Dispatch("Vissim.Vissim.600")        
            #time.sleep(150)    
        except:
            Vissim = 'StartError'
            
    if Vissim is not False and Vissim is not 'StartError':
        try:
            Vissim.LoadNet (InpxPath)   #the filename MUST have a capital first letter 
        except:
           Vissim = 'LoadNetError'
           
    return Vissim

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

def initializeSimulation(Vissim, parameters, values = [], variables = [], swp = False):          #Change Lane parameters need to be added
    ''' Defines the Vissim Similuation parameters
        the parameter variables must be [simulationStepsPerTimeUnit, first_seed, nbr_runs, CarFollowModType, Simulation lenght]'''    
    
    try:
        Simulation = Vissim.Simulation
        Evaluation = Vissim.Evaluation
        
        if Simulation.AttValue("IsRunning") is True:
            Simulation.Stop()
        
        #Setting Simulation attributes        
        Simulation.SetAttValue("SimRes", parameters[0])         #ODOT p.45 (56 in the pdf)
        Simulation.SetAttValue("useMaxSimSpeed", True)
        Simulation.SetAttValue("RandSeed", parameters[1])       #Hitchhiker's Guide to the Galaxy!
        Simulation.SetAttValue("RandSeedIncr", 1)
        Simulation.SetAttValue("NumRuns", parameters[2])        #To be verified
        Simulation.SetAttValue("SimPeriod",parameters[4])
        
        #Enabling the Quick Mode
        Vissim.graphics.currentnetworkwindow.SetAttValue("QuickMode", True)
        
        #Setting Evaluation outputs
        Evaluation.SetAttValue("VehRecWriteFile",True)               #Enable .fzp outputs
        if swp: Evaluation.SetAttValue("LaneChangesWriteFile",True)  #Enable .swp outputs
        
        #Setting driving behavior attributes
        if variables != []:   
            for i in range(len(Vissim.Net.DrivingBehaviors)):                       
                Type = "WIEDEMANN"+str(parameters[3])
                Vissim.Net.DrivingBehaviors[i].SetAttValue("CarFollowModType",Type)
                for variable in range(len(variables)):
                    Vissim.Net.DrivingBehaviors[i].SetAttValue(variables[variable],values[variable])
                    
        #Starting the simulation            
        Simulation.RunContinuous()

        simulated = True        
    except:
        simulated = sys.exc_info()
        
    return simulated