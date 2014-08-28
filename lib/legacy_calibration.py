# -*- coding: utf-8 -*-
"""
Created on Mon Aug 25 11:25:01 2014

@author: Laurent
"""

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

