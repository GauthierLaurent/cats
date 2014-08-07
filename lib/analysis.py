# -*- coding: utf-8 -*-
"""
Created on Thu Jul 10 14:43:44 2014

@author: Laurent
"""

################################ 
#        Importing dependencies       
################################ 
#Natives
import os, shutil, sys, copy, random, math
from scipy.stats import t, chi2
from scipy.stats.mstats import kruskalwallis
import numpy as np

#Internal
import lib.tools_write as write
import lib.vissim as vissim
import lib.outputs as outputs
import lib.define as define

################################ 
#        Calibration analysis       
################################

def checkCorrespondanceOfOutputs(video_value, calculated_value):
    '''Test a range of values with the kruskalwallis test'''

    H_statistic_list = []
    p_value_list = []

    for i in range(len(calculated_value)):    
        H_statistic, p_value = kruskalwallis(video_value[i].cumul_all.raw, calculated_value[i].cumul_all.raw)

        H_statistic_list.append(H_statistic)
        p_value_list.append(p_value)
    
    return p_value_list    

def simplicesDiameter(pointlist):
    '''Comuptes the distance point to point for every points in poinlist'''
    dist = []
    for i in range(len(pointlist)-1):
        for j in range(len(pointlist)-i-1):
            dist.append(sum(np.power((np.asarray(pointlist[len(pointlist)-j-1])-np.asarray(pointlist[i])),2))**0.5)
    return max(dist)

def detL(pointlist):
    '''pointlist MUST have n+1 vectors of n points'''
    
    point_array = np.asarray(pointlist)    
    L = []    
    for i in range(len(point_array)-1):
        L.append(point_array[i+1]-point_array[0])
    
    return np.linalg.det(np.asarray(L).T)    

def vonY(pointlist):
    
    diam = simplicesDiameter(pointlist)
    det = detL(pointlist)
    n = len(pointlist)-1   

    return abs(det)/(math.factorial(n)*diam)**n

    
def priorityAppend(sorted_list1,sorted_list2,append_list1,append_list2):
    '''takes sorted lists and insert a value after all values lower or equal to it'''
    appended_list1 = []; appended_list2 = []    

    indexes_before_new_value = [i for i, j in enumerate(sorted_list1) if j <= append_list1]
    indexes_after_new_value  = [i for i, j in enumerate(sorted_list1) if j > append_list1]

    for i in indexes_before_new_value: appended_list1.append(sorted_list1[i])
    appended_list1.append(append_list1)
    for i in indexes_after_new_value: appended_list1.append(sorted_list1[i])
        
    for i in indexes_before_new_value: appended_list2.append(sorted_list2[i])
    appended_list2.append(append_list2)
    for i in indexes_after_new_value: appended_list2.append(sorted_list2[i])
        
    return appended_list1, appended_list2
    
def appendAndsort2lists_withPriority(list1,list2,append_list1,append_list2,iteration_type):
    '''Sorts list2 according to the sorting of the content of list1 and the priority rules
       contained in priorityAppend'''

    if not isinstance(list1,list):  #mostly usefull for 'shrink' type
        preappend1 = [list1]
        preappend2 = [list2]
    else:    
        preappend1,preappend2 = define.sort2lists(list1,list2)     
    
    if iteration_type != 'shrink':
        sorted_list1, sorted_list2 = priorityAppend(preappend1,preappend2,append_list1,append_list2)
        
    else:
        for i in range(len(append_list1)):
            preappend1, preappend2 = priorityAppend(preappend1,preappend2,append_list1[i],append_list2[i])
        
        sorted_list1 = preappend1
        sorted_list2 = preappend2
    
    return sorted_list1, sorted_list2     

def calculateOnePass(values, foldername, inputs):
    
    #unpacking inputs
    commands    = inputs[0]
    config      = inputs[1]
    outputspath = inputs[2]
    parameters  = inputs[3]
    Inpxname    = inputs[4]
    InpxPath    = inputs[5]
    value_names = inputs[7]
    video_value = inputs[8]
    running     = inputs[9]

    #creating a folder containing the files for that iteration
    folderpath, filename = prepareFolderforVissimAnalysis(outputspath, foldername, Inpxname, InpxPath)
    
    p_values = []
    if commands.mode:  #this serves to bypass Vissim while testing the code
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
        
    else:
        #Starting a Vissim instance
        Vissim = vissim.startVissim(running, os.path.join(folderpath, filename))
        
        #Initializing and running the simulation
        simulated = vissim.initializeSimulation(Vissim, parameters, values, value_names)
        
        if simulated is not True:
            print 'Could not run the Vissim simulation for ' + str(foldername)
            sys.exit()
            
        else:
            #treating the outputs
            inputs = [outputspath, config.sim_steps, config.warm_up_time]
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs([f for f in os.listdir(folderpath) if f.endswith("fzp")], inputs)
            
    #checking the correspondance to the real data values
    calculated_values = [forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap]
    p_values = p_values + checkCorrespondanceOfOutputs(video_value, calculated_values)

    return p_values, filename
        
def runVissimForCalibrationAnalysis(inputvalues, inputs):
    '''handles two type of inputs:
            one generated by intelligentChunks --> inputvalues = [[[values we need],i],[[values we need],i],...]
            one generated by cleanChunks       --> inputvalues = [[values we need],[values we need],...]
    '''
    #unpacking inputs
    commands    = inputs[0]
    brutename   = inputs[6]
    
    p_values = [] 
    filenames = []
    if isinstance(inputvalues[0],list):    
        for i in range(len(inputvalues)):
            #defining the values and the folder name
            #try:
            if commands.multi:
                foldername = brutename + '_point_' + str(inputvalues[i][1]+1)
                values = inputvalues[i][0]
                p, f = calculateOnePass(values, foldername, inputs)
                p_values.append(p); filenames.append(f)
            #except(IndexError):
            else:            
                foldername = brutename + '_point_' + str(i+1)
                values = inputvalues[i]
                p, f = calculateOnePass(values, foldername, inputs)
                p_values.append(p); filenames.append(f)
    else:
        foldername = brutename
        values = inputvalues
        p, f = calculateOnePass(values, foldername, inputs)
        p_values = p_values + p; filenames.append(f)
        
    return p_values, filenames

def respectUniverseBoundaries(origine,destination,hard_bounds):
    '''verifies if the destination is within the boundaries. Else, return a point on the boundary'''
    vector = np.asarray(destination)-np.asarray(origine)
    vect_len = sum(np.power(vector,2))**0.5
    #norm_vect = vector/sum(np.power(vector,2))**0.5
    
    point_out = destination
    for i in range(len(destination)):
        #gathering informations on symetric equations: (x-x0)/a = (y-y0)/b = ... = (n-n0)/m

        if hard_bounds[i][0] is not None:        
            if destination[i] < hard_bounds[i][0]:      
                point = origine[i]
                coeff = vector[i]
                bound = hard_bounds[i][0]
            else:
                continue
                
        elif hard_bounds[i][1] is not None:
            if destination[i] > hard_bounds[i][1]:
                point = origine[i]
                coeff = vector[i]
                bound = hard_bounds[i][1]
            else:
                continue
        
        else:
            continue
        
        reduced_point = []
        for j in range(len(vector)):
            reduced_point.append((bound-point)/float(coeff)*vector[j]+origine[j])
 
        new_vect = np.asarray(reduced_point)-np.asarray(origine)
        
        if sum(np.power(new_vect,2))**0.5 < vect_len:
            point_out = reduced_point
            vect_len = sum(np.power(new_vect,2))**0.5
            
    return point_out
    
def newPoint(yn, yc, coeff,hard_bounds):
    ynew = []
    for i in range(len(yc)):
        ynew.append( yc[i] + coeff*(yc[i]-yn[i]) )
        
    return respectUniverseBoundaries(yc,ynew,hard_bounds)
    
def simplex_search_81(out, config, commands, hard_bounds, default_values, value_names, video_values, outputspath, parameters, InpxName, InpxPath, running, filename):        
    '''
    hard_bounds = min and max values that CAN be taken for an acceptable value of the tested variables    
    
    
    Pseudocode: 

    ***************************************************************** 
    *   from:  Introduction to derivative-free optimization p.120   *
    *          Algorithm 8.1 (The Nelder-Mead method).              *
    ***************************************************************** 
    
    Initialization: Choose an initial simplex of vertices Y0 = {y0, y1, ..., yn}.
    Evaluate f at the points in Y0. Choose constants:
            0 < γs < 1, −1 < δic < 0 < δoc < δr < δe.
            
    For k = 0, 1, 2, ...
    
    0.  Set Y = Yk .
    1.  Order: Order the n+1 vertices of Y = {y0, y1, ..., yn} so that
                    f0 = f(y0) ≤ f1 = f(y1) ≤ ··· ≤ fn = f(yn).
    2.  Reflect: Reflect the worst vertex yn over the centroid yc = Σ(de i=0 à n−1) yi/n
        of the remaining n vertices:
                                yr = yc+δr (yc− yn).
        Evaluate fr = f(yr). If f0 ≤ fr < fn−1, then replace yn by the reflected
        point yr and terminate the iteration: Yk+1 = {y0, y1, ..., yn−1, yr }.
    3.  Expand: If fr < f0, then calculate the expansion point
                                ye = yc +δe(yc− yn)
        and evaluate fe = f(ye). If fe ≤ fr , replace yn by the expansion point ye and
        terminate the iteration: Yk+1 = {y0, y1, ..., yn−1, ye}. Otherwise, replace yn by
        the reflected point yr and terminate the iteration: Yk+1 = {y0, y1, ..., yn−1, yr }.
        
    4.  Contract: If fr ≥ fn−1, then a contraction is performed between the best of
        yr and yn.
        
        (a) Outside contraction: If fr < fn, perform an outside contraction
                        yoc = yc+δoc(yc− yn)
        and evaluate foc = f(yoc). If foc ≤ fr , then replace yn by the outside
        contraction point yoc and terminate the iteration: Yk+1 = {y0, y1, ..., yn−1, yoc}.
        Otherwise, perform a shrink.
        
        (b) Inside contraction: If fr ≥ fn, perform an inside contraction
                        yic = yc+δic(yc− yn)
        and evaluate fic = f(yic). If fic < fn, then replace yn by the inside
        contraction point yic and terminate the iteration: Yk+1 = {y0, y1, ..., yn−1, yic}.
        Otherwise, perform a shrink.        
        
    5.  Shrink: Evaluate f at the n points y0+γs(yi − y0), i = 1, ... ,n, and replace
        y1, ..., yn by these points, terminating the iteration:
        Yk+1 = {y0 + γs(yi − y0), i = 0, ...,n}.
    
    A stopping criterion could consist of terminating the run when the diameter of the
    simplex becomes smaller than a chosen tolerance DeltaTol > 0 (for instance, DeltaTol = 10**−5).
     
    The Nelder–Mead algorithm performs the following number of function evaluations
    per iteration:
                    1    if the iteration is a reflection,
                    2    if the iteration is an expansion or contraction,
                    n+2  if the iteration is a shrink.
        
    The standard choices for the coefficients used are
                    γs = 1/2, δic = −1/2, δoc = 1/2, δr = 1, and δe = 2.
       
    '''
    
    ################## 
    #   Initialization       
    ##################
    #Iteration number
    itt = 0
    
    #Defining parameters
    gamma_s = 0.5   #shrink
    delta_ic = -0.5 #inside contraction
    delta_oc = 0.5  #outside contraction
    delta_r = 1     #reflect
    delta_e = 2     #expansion
   
    ##Stoping criterions
    Delta_tol = 0.001
   
    ###Numer of iterations
    max_itt = 10                #this low number serves to test out if the process goes well
   
    #Defining the first points
    start_values = [default_values]
    
    for j in range(len(default_values)):
        point = []
        for i in range(len(default_values)):            
            if isinstance(default_values[i], bool):
                point.append(default_values[i])
            else:
                low  = default_values[i]-1
                high = default_values[i]+1
                
                #checking if low is higher than the lower hard_bound 
                if hard_bounds[i][0] != None:
                    while low < hard_bounds[i][0]:
                        low += 0.1                
        
                #checking if up is lower than the upper hard_bound 
                if hard_bounds[i][1] != None:
                    while high > hard_bounds[i][1]:
                        high += -0.1
        
                #generates random points around the default values        
                point.append(round(random.uniform(low,high),4))
        start_values.append(point)
    
    #starting a count for the report statistics        
    point_count = len(start_values)
    
    #creating the output folder for the starting point - this folder will include folders for each starting points
    startingpath = write.createSubFolder(os.path.join(outputspath, "starting_points"), "starting_points")
         
    #Evaluation of the first points
    if commands.multi is True:
            
        futureChunks = []        
        for i in range(len(start_values)):
            futureChunks.append([start_values[i],i])
            
        inputs = [commands, config, startingpath, parameters, InpxName, InpxPath, "iteration_0", value_names, video_values, running]
        results = define.createWorkers(futureChunks, runVissimForCalibrationAnalysis, inputs, commands)
            
        #unpacking results and writing to report
        p_values = []
        for i in range(len(results)):
            for j in range(len(results[i][0])):
                write.writeInFile(out, [results[i][1][j], start_values[i], results[i][0][j]])
                p_values.append(results[i][0][j])
            
    else:                 
        inputs = [commands, config, startingpath, parameters, InpxName, InpxPath, "iteration_0", value_names, video_values, running]
        p_values, name = runVissimForCalibrationAnalysis(start_values, inputs)        
        
        #writing to report        
        for i in range(len(p_values)): 
            write.writeInFile(out, [name[i], start_values[i]], p_values[i])

    points = copy.deepcopy(start_values)
    gap_p_values = [p_values[i][0] for i in range(len(p_values))]
    
    ################## 
    #   Algorythm       
    ##################

    #  ****  1. sorting the p_values and the points together  *****************  
    gap_p_values, points = define.sort2lists(gap_p_values, points)
    
    #diameter
    Delta = simplicesDiameter(points)   #Delta = diam(Y)

    #To call the statistical function:
    #H-statistic, p-value = kruskalwallis(default_value, calculated_value)
    #if p<0.05 then first array is statistically different from second array
    #normally len(array) must be >= 5


    while Delta > Delta_tol or gap_p_values[0] >= 0.05 and itt <= max_itt:
        #prequisite stuff
        ## iteration number
        itt += 1
        
        if commands.verbose:
            print ' == Starting work on iteration number ' + str(itt) + ' =='
            
        ##iteration folder
        iterationpath = write.createSubFolder(os.path.join(outputspath, "iteration_"+str(itt)), "iteration_"+str(itt))    
        
        #  ****  2. Reflect  ******************************************************  
        worst = points[-1];         points.pop(-1)
        worst_p = gap_p_values[-1]; gap_p_values.pop(-1)
            
        ##calculating yc
        yc = []
        coordinates = [[] for i in range(len(points[0]))]
        for i in range(len(points)): #must find the centroid for each coordinates
            for o in range(len(points[i])):
                coordinates[o].append(points[i][o])        
        
        for coord in coordinates:    
            yc.append(np.mean(coord))                   #yc = Σ(de i=0 à n−1) yi/n
            
        ##reflecting every coordinates                
        yr = newPoint(worst, yc, delta_r,hard_bounds)
        
        ##evaluating the new point
        inputs = [commands, config, iterationpath, parameters, InpxName, InpxPath, "iteration_"+str(itt)+"_reflect", value_names, video_values, running]                
        yr_p_values, name = runVissimForCalibrationAnalysis(yr, inputs)
        write.writeInFile(out, [name, yr, yr_p_values])
        
        #incrementing stats
        point_count += 1
        
        #3.  ****   Expand  **  and 1. Sort  ************************************** 
        if yr_p_values[0] < gap_p_values[0]:     #the indice must correspond to the one used to define gap_p_values      
            ##expanding
            ye = newPoint(worst, yc, delta_e,hard_bounds)
                
            ##evaluating the new point
            inputs = [commands, config, iterationpath, parameters, InpxName, InpxPath, "iteration_"+str(itt)+"_expand", value_names, video_values, running]
            ye_p_values, name = runVissimForCalibrationAnalysis(ye, inputs)
            write.writeInFile(out, [name, ye, ye_p_values])
            
            #incrementing stats
            point_count += 1            
            
            if ye_p_values[0] < yr_p_values:    #the indice must correspond to the one used to define gap_p_values 
                gap_p_values,points = appendAndsort2lists_withPriority(gap_p_values,points,ye_p_values[0],ye,'expansion')
                Delta = simplicesDiameter(points)

                if commands.verbose:
                    print (' == Iteration concluded with an expansion == \n'
                           '')
                    
                continue
            
            else:
                gap_p_values,points = appendAndsort2lists_withPriority(gap_p_values,points,yr_p_values[0],yr,'reflection')
                Delta = simplicesDiameter(points)
                
                if commands.verbose:
                    print (' == Iteration concluded with a reflection == \n'
                           '')                          
                continue            
        
        #4.  ****   Contract  **  and 1. Sort  ************************************
        elif yr_p_values[0] >= gap_p_values[-1]:    #the indice must correspond to the one used to define gap_p_values
            
            #outside contraction        
            if yr_p_values[0] < worst_p:              #the indice must correspond to the one used to define gap_p_values
                
                ##contracting
                yoc = newPoint(worst, yc, delta_oc,hard_bounds)
                
                ##evaluating the new point
                inputs = [commands, config, iterationpath, parameters, InpxName, InpxPath, "iteration_"+str(itt)+"_outide_contraction", value_names, video_values, running]
                yoc_p_values, name = runVissimForCalibrationAnalysis(yoc, inputs)
                write.writeInFile(out, [name, yoc, yoc_p_values])

                #incrementing stats
                point_count += 1 
            
                if yoc_p_values[0] < yr_p_values[0]:
                    gap_p_values,points = appendAndsort2lists_withPriority(gap_p_values,points,yoc_p_values[0],yoc,'outside contraction')
                    Delta = simplicesDiameter(points)
                    if commands.verbose:
                        print (' == Iteration concluded with an outside contraction == \n'
                               '')
                    continue
                else:
                    pass
            
            #inside contraction
            else:
                ##contracting
                yic = newPoint(worst, yc, delta_ic,hard_bounds)
                
                ##evaluating the new point
                inputs = [commands, config, iterationpath, parameters, InpxName, InpxPath, "iteration_"+str(itt)+"_inside_contraction", value_names, video_values, running]
                yic_p_values, name = runVissimForCalibrationAnalysis(yic, inputs)
                write.writeInFile(out, [name, yic, yic_p_values])
                
                #incrementing stats
                point_count += 1 

                if yic_p_values[0] < yr_p_values[0]:         #the indice must correspond to the one used to define gap_p_values
                    gap_p_values,points = appendAndsort2lists_withPriority(gap_p_values,points,yic_p_values[0],yic,'inside contraction')
                    Delta = simplicesDiameter(points)
                    
                    if commands.verbose:
                        print (' == Iteration concluded with an inside contraction == \n'
                               '')                           
                    continue
                else:
                    pass            
                
        #****** 5. Skrink  **  and 1. Sort  ***************************************
            ##generating the folder
            shrinkpath = write.createSubFolder(os.path.join(iterationpath, "shrink"), "shrink")
            
            ##writing the kept point to the report
            write.writeInFile(out, ["iteration_"+str(itt)+"_shrink_y0", points[0], gap_p_values[0]])
            
            ##generating the shrinked points y0, y1', y2' ..., yn'
            points.append(worst)
            shrink_points = []            
            for i in range(len(points)-1):
                construction_point = []
                for o in range(len(points[i+1])):
                    construction_point.append(points[0][o] + gamma_s*(points[i+1][o]-points[0][o]))
            
                shrink_points.append(construction_point)
            
            ##evaluating the new points
            if commands.multi is True:
        
                #shutting down the verbose command in multiprocessing
                if commands.verbose:
                    commands.verbose = False
                    restart = True
            
                futureChunks = []        
                for i in range(len(shrink_points)):
                    futureChunks.append([shrink_points[i],i])
                    
                inputs = [commands, config, shrinkpath, parameters, InpxName, InpxPath, "iteration_"+str(itt)+"_shrink", value_names, video_values, running]
                results = define.createWorkers(futureChunks, runVissimForCalibrationAnalysis, inputs, commands)
        
                #reenabling verbose for the rest of the iteration
                if restart is True: commands.verbose = True
                
                #unpacking results and writing to report
                shrink_p_values = []
                for i in range(len(results)):
                    for j in range(len(results[i][0])):
                        write.writeInFile(out, [results[i][1][j], start_values[i], results[i][0][j]])
                        shrink_p_values.append(results[i][0][j])
                
            else:                              
                inputs = [commands, config, shrinkpath, parameters, InpxName, InpxPath, "iteration_"+str(itt)+"_shrink", value_names, video_values, running]
                shrink_p_values, name = runVissimForCalibrationAnalysis(shrink_points, inputs)    
                for i in range(len(shrink_points)):
                    write.writeInFile(out, [name[i], shrink_points[i], shrink_p_values[i]])       

            #incrementing stats
            point_count += len(shrink_points)
            
            #working out the p_value to be used
            gap_shrink_p_values = []
            for i in range(len(shrink_p_values)):
                gap_shrink_p_values.append(shrink_p_values[i][0])
                    
            gap_p_values,points = appendAndsort2lists_withPriority(gap_p_values[0],points[0],gap_shrink_p_values,shrink_points,'shrink')
            Delta = simplicesDiameter(points)
            
            if commands.verbose:
                print (' == Iteration concluded with a shrink == \n'
                       '')
            continue
        
        #0.  ****   Initialize next step if f0 < fr <= fn-1 **  and 1. Sort  ******
        else:
            gap_p_values,points = appendAndsort2lists_withPriority(gap_p_values,points,yr_p_values,yr,'reflection')
            Delta = simplicesDiameter(points)
        
            if commands.verbose:
                print (' == Iteration concluded with a reflection == \n'
                       '')
            continue
        
    #need more code?
    if commands.verbose:
        if itt >= max_itt:
            print '-> maximum number of iterations reached. Aborting calculations'
        else:
            print '-> Optimum found'
        
    return itt, point_count


            
            
def pattern_search(out, config, commands, rangevalues, default_values, outputspath, first_start_default = True):
            
    '''
    Pseudocode: 

    ***************************************************************** 
    *   from:  Introduction to derivative-free optimization p.120   *
    *          Algorithm 7.1 (Coordinate-search method).            *
    ***************************************************************** 
      
    Initialization: Choose x0, and α0 > 0.
            
    For k = 0, 1, 2, ...
    
    1.  Poll step: Order the poll set Pk = {xk +αkd : d ∈ D⊕}. Start evaluating f
        at the poll points following the order determined. If a poll point xk +αkdk is
        found such that f (xk +αkdk ) < f (xk), then stop polling, set xk+1 = xk +αkdk,
        and declare the iteration and the poll step successful. Otherwise, declare the
        iteration (and the poll step) unsuccessful and set xk+1 = xk.


    2.  Parameter update: If the iteration was successful, tset αk+1 = αk (or αk+1 =
        2αk ). Otherwise, set αk+1 = αk/2. 

    The poll step makes at most |Dk | (where |Dk| ≥ 2n + 1) function evaluations and
    exactly that many at all unsuccessful iterations.
    
    The natural stopping criterion in directional direct search is to terminate the run
    when αk < αtol , for a chosen tolerance αtol > 0 (for instance, αtol = 10−5).
       
    '''
    #Defining parameters        #may add some random generation?
    ##Alpha0                    #the values are now arbitrary and no search was done to define them
    alpha_0 = 1
   
    ##Betas
    beta_1 = 0.1 
    beta_2 = 0.4
   
    ##Stoping criterions
    ###Alpha tolerance
    alpha_tol = 0.001
   
    ###Numer of iterations
    max_itt = 10                #this low number serves to test out if the process goes well
   
    #Defining the first point
    start_values = []
    
    if first_start_default is True:
        start_values = default_values
    else:
        for i in range(len(rangevalues)):
            start_values.append(random.uniform(rangevalues[i][0],rangevalues[i][1]))
    
    #





################################ 
#        Statistical precision analysis       
################################

def statistical_ana(concat_variables, default_values, filename, InpxPath, InpxName, outputspath, graphspath, config, commands, running, parameters):
    '''Finds the number of iterations needed to achieve a good confidence interval
    
    Base on the ODOT specifications:
        1. run 10 simulations and calculates the median and standard deviation for the outputs
        2. run the Student t-test while fixing the confidence interval to +/- err*mu
                   where err is the %error on the mean value, specified in the cfg file.
                   --> N = [t(1-alpha/2;N-1)*S/(err*mu)]^2 with aplha = 0.975 (bivariate 95% confidence)
            2a. calculate the confidence interval for the standard deviation
            
        3. check if N > number of simulations ran up to this point
        4. if yes, run one more simulation and repeat steps 2, 3 and 4 until "number of simulations" >= N
        
    '''
    max_itt = 25    #might consider adding it to the cfg file    
    
    text = []
   
    #set the number of runs to 10
    first_seed = parameters[1]    
    parameters[2] = 10
    iterrations_ran = 10
    
    #renaming the inpx and moving it to the output folder
    if os.path.exists(os.path.join(outputspath, "Statistical_test.inpx")) is False:
        shutil.copy(InpxPath, os.path.join(outputspath, InpxName))
        os.rename(os.path.join(outputspath, InpxName), os.path.join(outputspath, "Statistical_test.inpx"))
    
    if commands.verbose is True:
        print 'Starting the first 10 runs'
    
    if commands.mode:  #this serves to bypass Vissim while testing the code
        flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
    else:
        Vissim = vissim.startVissim(running, os.path.join(outputspath,  "Statistical_test.inpx"))
                            
        #Vissim initialisation and simulation running                                                   
        simulated = vissim.initializeSimulation(Vissim, parameters, default_values, concat_variables, commands.save_swp)
        
        if simulated is not True:
            print simulated
            sys.exit()
            
        else:
            #output treatment
            if commands.multi is True:
                inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose]
                results = define.createWorkers([f for f in os.listdir(outputspath) if f.endswith("fzp")], outputs.treatVissimOutputs, inputs, commands)            
                #building the old_data            
                for i in range(len(results)):
                    if i == 0:
                                            
                        old_nb_opp = [ results[i][1] ]
                        old_nb_man = [ results[i][2] ]
                        old_flow   = [ results[i][0] ]
                        old_FM     = [ results[i][3].distributions[j].raw for j in range(len(results[i][3].distributions)) if results[i][3].distributions[j] != [] ]
                        old_oppA   = [ results[i][4].distributions[j].raw for j in range(len(results[i][4].distributions)) if results[i][4].distributions[j] != [] ]
                        old_oppB   = [ results[i][5].distributions[j].raw for j in range(len(results[i][5].distributions)) if results[i][5].distributions[j] != [] ]
                        old_manA   = [ results[i][6].distributions[j].raw for j in range(len(results[i][6].distributions)) if results[i][6].distributions[j] != [] ]
                        old_manB   = [ results[i][7].distributions[j].raw for j in range(len(results[i][7].distributions)) if results[i][7].distributions[j] != [] ]
                                           
                    else:
                        old_nb_opp.append(results[i][1])
                        old_nb_man.append(results[i][2])
                        old_flow.append(results[i][0])
                        for j in range(len(results[i][3].distributions)):
                            if results[i][3].distributions[j] != []: old_FM.append(results[i][3].distributions[j].raw)
                        for j in range(len(results[i][4].distributions)):
                            if results[i][4].distributions[j] != []: old_oppA.append(results[i][4].distributions[j].raw)
                        for j in range(len(results[i][5].distributions)):
                            if results[i][5].distributions[j] != []: old_oppB.append(results[i][5].distributions[j].raw)
                        for j in range(len(results[i][6].distributions)):
                            if results[i][6].distributions[j] != []: old_manA.append(results[i][6].distributions[j].raw)
                        for j in range(len(results[i][7].distributions)):
                            if results[i][7].distributions[j] != []: old_manB.append(results[i][7].distributions[j].raw)
                       
                old_num    = iterrations_ran
                old_data   = [old_nb_opp, old_nb_man, old_flow, old_FM, old_oppA, old_oppB, old_manA, old_manB, old_num]
                inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose, old_data]
                flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs(None, inputs)
                                    
            else:
                inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose]
                flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs([f for f in os.listdir(outputspath) if f.endswith("fzp")], inputs)
       
    #Student t-test to find the min number of runs
    t_student = t.ppf(0.975,9)
    err = config.desired_pct_error/100

    N1 = ( t_student * forFMgap.cumul_all.std / (err * forFMgap.cumul_all.mean) )**2
    N2 = ( t_student * oppLCagap.cumul_all.std / (err * oppLCagap.cumul_all.mean) )**2
    N3 = ( t_student * oppLCbgap.cumul_all.std / (err * oppLCbgap.cumul_all.mean)  )**2
    N4 = ( t_student * manLCagap.cumul_all.std / (err * manLCagap.cumul_all.mean)  )**2
    N5 = ( t_student * manLCbgap.cumul_all.std / (err * manLCbgap.cumul_all.mean)  )**2
    
    #if all variables are to be statisticaly significant to 95% confidance, they must all pass the test, thus N1...N5 must be < than the number of runs
    N =  max(N1, N2, N3, N4, N5)    
    
    #std confidence intervals             
    SCI1 = [forFMgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 ,  forFMgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI2 = [oppLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]   
    SCI3 = [oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI4 = [manLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    SCI5 = [manLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
    
    text.append(["Nbr_itt","Student-t","Std1","Mean1","N1","Std2","Mean2","N2","Std3","Mean3","N3","Std4","Mean4","N4","Std5","Mean5","N5","N","SCI1max","SCI1min","SCI2max","SCI2min","SCI3max","SCI3min","SCI4max","SCI4min","SCI5max","SCI5min"])
    text.append([iterrations_ran, t_student, forFMgap.cumul_all.std,forFMgap.cumul_all.mean, N1, oppLCagap.cumul_all.std, oppLCagap.cumul_all.mean, N2, oppLCbgap.cumul_all.std, oppLCbgap.cumul_all.mean, N3, manLCagap.cumul_all.std, manLCagap.cumul_all.mean, N4, manLCbgap.cumul_all.std, manLCbgap.cumul_all.mean, N5, N, SCI1, SCI2, SCI3, SCI4, SCI5])    
    
    while N > iterrations_ran and iterrations_ran < max_itt:
        
        if commands.verbose is True:
            print 'Starting the ' + str(iterrations_ran + 1) + "th iteration"        
        
        #building the old_data
        old_nb_opp = [oppLCcount]
        old_nb_man = [manLCcount]
        old_flow   = [flow]
        old_FM     = [ forFMgap.distributions[i].raw for i in range(len(forFMgap.distributions)) ]
        old_oppA   = [ oppLCagap.distributions[i].raw for i in range(len(oppLCagap.distributions)) ]
        old_oppB   = [ oppLCbgap.distributions[i].raw for i in range(len(oppLCbgap.distributions)) ]
        old_manA   = [ manLCagap.distributions[i].raw for i in range(len(manLCagap.distributions)) ]
        old_manB   = [ manLCbgap.distributions[i].raw for i in range(len(manLCbgap.distributions)) ]
        old_num    = iterrations_ran
        old_data   = [old_nb_opp, old_nb_man, old_flow, old_FM, old_oppA, old_oppB, old_manA, old_manB, old_num]        
        
        #incrementing needed parameters                
        parameters[1] = first_seed + iterrations_ran    #need to increment the starting Rand Seed by the number of it. already ran
        parameters[2] = 1                               #need to do only one simulation
        iterrations_ran += 1
        
        #calling vissim
        if commands.mode:  #this serves to bypass Vissim while testing the code
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
        else:
            
            #Initialize the new Vissim simulation
            Simulation = Vissim.Simulation
            Simulation.SetAttValue("RandSeed", parameters[1])
            Simulation.SetAttValue("NumRuns", parameters[2])
                                
            #Starting the simulation            
            Simulation.RunContinuous()                                
            
            #determining current file
            file_to_run = ["Statistical_test_" + str(iterrations_ran).zfill(3) + ".fzp"]            

            #output treatment
            inputs = [outputspath, config.sim_steps, config.warm_up_time, commands.verbose, old_data]
            flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs(file_to_run, inputs)
        
        #generating the needed means and std
        t_student = t.ppf(0.975, iterrations_ran -1)
        N1 = ( t_student * forFMgap.cumul_all.std / (err * forFMgap.cumul_all.mean) )**2
        N2 = ( t_student * oppLCagap.cumul_all.std / (err * oppLCagap.cumul_all.mean) )**2
        N3 = ( t_student * oppLCbgap.cumul_all.std / (err * oppLCbgap.cumul_all.mean)  )**2
        N4 = ( t_student * manLCagap.cumul_all.std / (err * manLCagap.cumul_all.mean)  )**2
        N5 = ( t_student * manLCbgap.cumul_all.std / (err * manLCbgap.cumul_all.mean)  )**2
        
        N =  max(N1, N2, N3, N4, N5)        
        
        #std confidence intervals             
        SCI1 = [forFMgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 ,  forFMgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI2 = [oppLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]   
        SCI3 = [oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , oppLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI4 = [manLCagap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCagap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        SCI5 = [manLCbgap.cumul_all.std*((N-1)/chi2.ppf(1-0.05/2,N-1))**0.5 , manLCbgap.cumul_all.std*((N-1)/chi2.ppf(0.05/2,N-1))**0.5 ]
        
        text.append([iterrations_ran, t_student, forFMgap.cumul_all.std,forFMgap.cumul_all.mean, N1, oppLCagap.cumul_all.std, oppLCagap.cumul_all.mean, N2, oppLCbgap.cumul_all.std, oppLCbgap.cumul_all.mean, N3, manLCagap.cumul_all.std, manLCagap.cumul_all.mean, N4, manLCbgap.cumul_all.std, manLCbgap.cumul_all.mean, N5, N, SCI1, SCI2, SCI3, SCI4, SCI5])     
        
    if iterrations_ran == max_itt and commands.verbose is True:
        print "Maximum number of iterations reached - Stoping calculations and generating report"
    elif commands.verbose is True:
        print "Statistical precision achieved - generating report"     
                
    #closing vissim
    vissim.stopVissim(Vissim)

    '''
    MUST ADD GRAPH OPTION
    '''
    
    return text        
        

################################ 
#        Sensitivity Analisis       
################################

def setCalculatingValues(default_values, current_name, nbr_points, current_range = [], default = False):
    '''Creates the working array to work with for the current iteration 
       NB: current_range = [[min, max], pos]  | for default_values = True, current_range is not needed'''
    
    working_values = copy.deepcopy(default_values)
    if default is True:        
        points_array = [default_values[0]]
        position = 0
    else:
        position = current_range[1]
        if current_name == "CoopLnChg":
            points_array = current_range[0]
        else:
            points_array = []
            if nbr_points > 1:
                for point in range(nbr_points):
                    points_array.append(current_range[0][0] + point * (current_range[0][1] - current_range[0][0]) /  (nbr_points - 1) )
            else:
                points_array.append((current_range[0][0] + current_range[0][1]) / 2)
            
    return working_values, points_array, position
        
def varDict(variable_names, default_values):
    '''creates a dictionary for faster search of variables'''
    
    var_dict = {}
    for i in range(len(variable_names)):
        var_dict[variable_names[i]] = [default_values[i], i]
        
    return var_dict    
        
def correctingValues(default_values, current_value, current_name, var_dict):
    '''Checks if the value is in the following list and corrects the linked values accordingly'''
    
    message = []
    working_values = copy.deepcopy(default_values)
    if current_name == "CoopLnChgSpeedDiff":
        working_values[var_dict["CoopLnChg"][1]] = True
    elif current_name == "CoopLnChgCollTm":
        working_values[var_dict["CoopLnChg"][1]] = True
    elif current_name == "LookAheadDistMin":
        if working_values[var_dict["LookAheadDistMax"][1]] < current_value:
            working_values[var_dict["LookAheadDistMax"][1]] = current_value + 0.1
            message.append('LookAheadDistMax was set to a value lower than the value set to LookAheadDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookAheadDistMax":
        if working_values[var_dict["LookAheadDistMin"][1]] > current_value:
            working_values[var_dict["LookAheadDistMin"][1]] = current_value - 0.1
            message.append('LookAheadDistMin was set to a value higher than the value set to LookAheadDistMax. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookBackDistMin":
        if working_values[var_dict["LookBackDistMax"][1]] < current_value:
            working_values[var_dict["LookBackDistMax"][1]] = current_value + 0.1
            message.append('LookBackDistMax was set to a value lower than the value set to LookBackDistMin. To avoid a crash of Vissim, the value was adjusted')
    elif current_name == "LookBackDistMax":
        if working_values[var_dict["LookBackDistMin"][1]] > current_value:
            working_values[var_dict["LookBackDistMin"][1]] = current_value - 0.1
            message.append('LookBackDistMin was set to a value higher than the value set to LookBackDistMax. To avoid a crash of Vissim, the value was adjusted')
        
    return working_values, message

def prepareFolderforVissimAnalysis(outputspath, folder_name, InpxName, InpxPath, default = False):
    #creating a folder containing the files for that iteration
    if default is True:
        filename = 'Default_values.inpx'
        folder = 'Default_values'
    else:
        filename = folder_name + '.inpx'
        folder = folder_name

    folderpath = os.path.join(outputspath, folder)
    newfolderpath = write.createSubFolder(folderpath, folder)
    
    if newfolderpath is False:
        print 'Newfolderpath = False, must find a way to handle this issue'
        sys.exit()
    
    #renaming the inpx and moving it to the new folder
    if os.path.exists(os.path.join(folderpath, filename)) is False:
        shutil.copy(InpxPath, os.path.join(folderpath, InpxName))
        os.rename(os.path.join(folderpath, InpxName), os.path.join(folderpath, filename))
    
    return folderpath, filename
	
def sensitivityAnalysis(rangevalues, inputs, default = False):
    '''Runs the sensitivity analysis for a set of predetermined values
    
       note: rangevalues = [range, position in the complete list]
    '''    

    #unpacking inputs - should eventually be changed directly in the code
    concat_variables    = inputs [0]
    default_values      = inputs [1]
    InpxPath            = inputs [2]
    InpxName            = inputs [3]
    outputspath         = inputs [4]
    graphspath          = inputs [5]
    config              = inputs [6]
    commands            = inputs [7]
    running             = inputs [8]
    parameters          = inputs [9]
    verbose             = inputs [10]
    if default is False:
        firstrun_results = inputs[11]      
    
    #preparing the outputs    
    text = []
    
    #creating a dictionnary
    var_dict = varDict(concat_variables, default_values)    

    #treating the values given in rangevalues    
    for value in range(len(rangevalues)):        
        #defining the variable being worked on and the range of values it can take
        if default is True:
            current_range = []
            value_name = "Default"
        else:
            current_range = rangevalues[value]   
            value_name = concat_variables[rangevalues[value][1]]
        
        #defining the values needed for the current cycle
        working_values, points_array, position = setCalculatingValues(default_values, value_name, config.nbr_points, current_range, default)

        #iterating on the number points
        for point in points_array:
            iteration_values = copy.deepcopy(working_values)
            iteration_values[position] = point
            
            #correcting the value array for variables that need to interact with others
            corrected_values, message = correctingValues(iteration_values, point, value_name, var_dict)
            
            if message != []:
                print'*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***' 
                print message
                print' occured for variable ' + str(value_name) + ' = ' + str(point) 
                print'*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'
            
            #creating a folder containing the files for that iteration
            folderpath, filename = prepareFolderforVissimAnalysis(outputspath, value_name + '_' + str(round(point,3)), InpxName, InpxPath, default)
    
            #Starting a Vissim instance
            if commands.mode:  #this serves to bypass Vissim while testing the code
                flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.generateRandomOutputs(parameters)
            else:
                Vissim = vissim.startVissim(running, os.path.join(folderpath, filename))
                                    
                #Vissim initialisation and simulation running
                simulated = vissim.initializeSimulation(Vissim, parameters, corrected_values, concat_variables, commands.save_swp)
                
                if simulated is not True:
                    text.append([value_name, corrected_values,''.join(str(simulated))])    #printing the exception in the csv file
                else:
                    #print '*** Simulation completed *** Runtime: ' + str(time.clock())                    
                
                    vissim.stopVissim(Vissim) #unsure if i should stop and start vissim every iteration... to be tested.
                    
                    #output treatment
                    inputs = [folderpath, config.sim_steps, config.warm_up_time, verbose]
                    flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs([f for f in os.listdir(folderpath) if f.endswith("fzp")], inputs)
                    #print '*** Output treatment completed *** Runtime: ' + str(time.clock())
                
                if default is True:
                    firstrun_results = []
                    firstrun_results.append(float(forFMgap.cumul_all.mean))
                    firstrun_results.append(float(oppLCagap.cumul_all.mean))
                    firstrun_results.append(float(oppLCbgap.cumul_all.mean))
                    firstrun_results.append(float(manLCagap.cumul_all.mean))
                    firstrun_results.append(float(manLCbgap.cumul_all.mean))
                    firstrun_results.append(float(oppLCcount))
                    firstrun_results.append(float(manLCcount))
    
                    
                else:           
                    delta_mean_fgap = (forFMgap.cumul_all.mean - firstrun_results[0])/firstrun_results[0]
                    delta_mean_Aoppgap = (oppLCagap.cumul_all.mean - firstrun_results[1])/firstrun_results[1]
                    delta_mean_Boppgap = (oppLCbgap.cumul_all.mean - firstrun_results[2])/firstrun_results[2]
                    delta_mean_Amangap = (manLCagap.cumul_all.mean - firstrun_results[3])/firstrun_results[3]
                    delta_mean_Bmangap = (manLCbgap.cumul_all.mean - firstrun_results[4])/firstrun_results[4]
                    delta_oppLCcount = (oppLCcount - firstrun_results[5])/firstrun_results[5]
                    delta_manLCcount = (manLCcount - firstrun_results[6])/firstrun_results[6]
                
                #printing graphs
                if commands.vis_save:
                    variables = [forFMgap,oppLCagap,oppLCbgap,manLCagap,manLCbgap]
                    variables_name =["Forward_gaps","Opportunistic_lane_change_'after'_gaps","Opportunistic_lane_change_'before'_gaps","Mandatory_lane_change_'after'_gaps","Mandatory_lane_change_'before'_gaps"]
                    for var in range(len(variables)):
                        if default is True:
                            name = "Default_values"
                            subpath = "Default_values"
                        else:
                            name = filename.strip('.inpx')
                            subpath = value_name[:]
                        
                        write.printStatGraphs(graphspath,variables[var], name, variables_name[var], commands.fig_format, config.nbr_runs, subpath)
                    
                #writing to file
                if default is True:
                    text.append(["Default_values", corrected_values, flow, oppLCcount, "---", manLCcount, "---", forFMgap.cumul_all.mean, "---", oppLCagap.cumul_all.mean, "---", oppLCbgap.cumul_all.mean, "---", manLCagap.cumul_all.mean, "---", manLCbgap.cumul_all.mean,  "---"])
                else:
                    text.append([value_name, corrected_values, flow, oppLCcount, delta_oppLCcount, manLCcount, delta_manLCcount, forFMgap.cumul_all.mean, delta_mean_fgap, oppLCagap.cumul_all.mean, delta_mean_Aoppgap, oppLCbgap.cumul_all.mean, delta_mean_Boppgap, manLCagap.cumul_all.mean, delta_mean_Amangap, manLCbgap.cumul_all.mean, delta_mean_Bmangap])       
        
        #breaking the outer loop because the default only needs to be ran once
        if default is True:
            break
    
    if default is True:    
        return text, firstrun_results
    else:
        return text