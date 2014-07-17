# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:32:08 2014

@author: Laurent
"""

##################
# Import Native Libraries
##################

import os, time, shutil
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

##################
# Writing tools
##################

def createSubFolder(folderpath, filename, Archives = True):
    '''Creates a folder named "filename"
    
       If such a folder already exists at the designated location, creates a subfolder named "Archives"
       and another subfolder named "yyyymmdd_hhmmss" and moves all files in the folder to that subfolder'''
       
    newfolderpath = folderpath

    try: 
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
        
        else:
            if Archives is True:
                if os.listdir(folderpath) != []:
                    print '   =================================='                    
                    print '     Folder with the name " ' + filename + ' " already exist!'
                    print '   Moving all current files to a subfolder named "Archives" '
                    print '   ==================================' 
                     
                    if not os.path.exists(os.path.join(folderpath, 'Archives')):
                        os.makedirs(os.path.join(folderpath, 'Archives'))
                        
                    datename = str(time.localtime().tm_year)+str(time.localtime().tm_mon).zfill(2)  + str(time.localtime().tm_mday).zfill(2) + '_' + str(time.localtime().tm_hour) + 'h' + str(time.localtime().tm_min) + 'm' + str(time.localtime().tm_sec) + 's' 
                    newfolderpath = os.path.join(folderpath, 'Archives', datename)
                    os.makedirs(newfolderpath)        
                    for files in os.listdir(folderpath):
                        if files != 'Archives' and not files.endswith('inpx'):
                             shutil.move(os.path.join(folderpath, files),os.path.join(newfolderpath, files) )
    except:
        newfolderpath = False
        
    return newfolderpath

def defineName(dirname, TypeOfAnalysis):
    last_num = 0
    
    past_analysis  = [f for f in os.listdir(dirname) if "Analysis" in f]
    if past_analysis != []:
        for f in past_analysis:
            striped = f.strip('.csv')
            num = int(striped.split('_')[2])
            if num > last_num: last_num = num
    
    last_num += 1  
    filename = TypeOfAnalysis + '_Analysis_' + str(last_num)
    
    return filename, last_num
    
def writeHeader(dirname, variables, TypeOfAnalysis, first_seed, nbr_runs, warmUpTime, desiredSimulatedTime, values = None):
    '''writes the header. For sensitivity analysis, the header has 19 lines'''
     
    name, last_num = defineName(dirname, TypeOfAnalysis)
    #import pdb; pdb.set_trace()    
    subdirname = createSubFolder(os.path.join(dirname,name), name, Archives = False)  
    filename = '{}/'+ name + '.csv'
    
    #header writing
    out = open(filename.format(subdirname), "w")
    out.write("Analysis number: " + str(last_num) + "\n")
    out.write("Type of analysis: " + str(TypeOfAnalysis) + "\n")
    if TypeOfAnalysis != "Student":
        out.write("Number of runs per tested variables: " + str(nbr_runs) + "\n")  
    out.write("First seed: " + str(first_seed) + "      (increment: 1) \n")       
    out.write("Simulation lenght: " + str(desiredSimulatedTime) + "\n")  
    out.write("Warm up time: " + str(warmUpTime) + "\n")  
    out.write("Date: " + str(time.localtime().tm_year) + '/' + str(time.localtime().tm_mon).zfill(2) + '/'  + str(time.localtime().tm_mday).zfill(2) + "\n")
    out.write("\n")
    
    #Student header
    if TypeOfAnalysis == "Student":  
        out.write("Test based on a desired confidance interval of +/- S\n"
                  "       **  N = [t(1-alpha/2;N-1)*S]^2  **\n"
                  "\n"
                  "For the Confidance interval of standard deviation, a Chi-square test is used\n"
                  "       **  CI = [(N-1)^0.5*S*Xhi(N-1)]  **\n"
                  "\n"                                    
                  "Base values (default values) used to run the test:\n")
        for var in variables:
            out.write(str(var) + ";")
        out.write("\n")
        for var in values:
            out.write(str(var) + ";")
        out.write("\n")
        out.write("\n"
                  "*Nbr_itt: number of itterations ran to run the t-test\n"
                  "*N1: minimum number of iterrations needed to give a CI of 1.0 for the forward gaps\n"
                  "*N2: minimum number of iterrations needed to give a CI of 1.0 for the opportunistic lane change gaps calculated after lane change\n"
                  "*N3: minimum number of iterrations needed to give a CI of 1.0 for the opportunistic lane change gaps calculated before lane change\n"
                  "*N4: minimum number of iterrations needed to give a CI of 1.0 for the mandatory lane change gaps calculated after lane change\n"
                  "*N5: minimum number of iterrations needed to give a CI of 1.0 for the mandatory lane change gaps calculated before lane change\n"
                  "*SCI1: Confidance interval calculated for the standard deviation for the forward gaps\n"
                  "*SCI2: Confidance interval calculated for the standard deviation for the opportunistic lane change gaps calculated after lane change\n"
                  "*SCI3: Confidance interval calculated for the standard deviation for the opportunistic lane change gaps calculated before lane change\n"
                  "*SCI4: Confidance interval calculated for the standard deviation for the mandatory lane change gaps calculated after lane change\n"
                  "*SCI5: Confidance interval calculated for the standard deviation for the mandatory lane change gaps calculated before lane change\n")
        
    #Sensitivity header
    if TypeOfAnalysis == 'Sensitivity':
        out.write("*var_name: Name of the tested variable\n"
                  "*flow: Vehicular flow\n"
                  "*nbr_opp: Number of opportunistic lane changes\n"
                  "*nbr_man: Number of mandatory lane changes\n"
                  "*m_forward: Mean calculated forward gap\n"
                  "*m_LC_Aopp: Mean calculated opportunistic lane change gap calculated after the lane changing vehicule inserted into the new lane \n"
                  "*m_LC_Bopp: Mean calculated opportunistic lane change gap calculated before the lane changing vehicule began changing lane\n"
                  "*m_LC_Aman: Mean calculated mandatory lane change gap calculated after the lane changing vehicule inserted into the new lane \n"
                  "*m_LC_Aman: Mean calculated mandatory lane change gap calculated before the lane changing vehicule began changing lane \n"
                  "\n"
                  "var_name;")
        for var in variables:
            out.write(str(var) + ";")
        out.write("flow;nbr_opp;% diff;nbr_man;% diff;m_forward;% diff;m_LC_Aopp;% diff;m_LC_Bopp;% diff;m_LC_Aman;% diff;m_LC_Bman;% diff\n")        
   
    #Calibration header
   
    return out, subdirname
    
def intoList(out, mylist):
    for i in mylist:
        if isinstance(i, list) is True:
            intoList(out, i)            
        else:
            if isinstance(i,float) is True:
                out.write(str(round(i,4)) + ";")
            else:
                out.write(str(i) +";")
    return out   

def writeInFile(out, *args):
    for arg in args:
        if isinstance(arg, list) is True:
            out = intoList(out, arg)
        else:
            if isinstance(arg,float) is True:
                    out.write(str(round(arg,4)) + ";")
            else:
                out.write(str(arg) +";")
    out.write("\n")
    return out
    
def printStatGraphs(graphspath,variable,value_name, variable_name, graphformat, subpath = ""):
    '''create graphs for a type 'Stats' variable'''

    #creating the cumulative graph                         
    plt.plot(variable.distributions[0].value, variable.distributions[0].cumul)
    plt.xlabel(variable_name.replace("_"," "))
    plt.ylabel("Count")
    plt.title("Cumulated distribution for " + variable_name.replace("_"," "))
    plt.savefig(os.path.join(graphspath, "cumul_dist_graphs", subpath, value_name + "_cumulative_distribution_for_"+ variable_name + "." + graphformat), format =  graphformat)
    plt.clf()
    
    #creating the distributions graph
    ##concatenated distributions
    fig = plt.figure()
    fig.add_axes((0.1,0.1,0.70,0.80))
    nbr, bins, patches = plt.hist(variable.cumul_all.raw,100,histtype = 'step')
    kde = stats.gaussian_kde(variable.cumul_all.raw)
    test = np.arange(min(variable.cumul_all.raw) -1,max(variable.cumul_all.raw) +1,0.1)
    line = plt.plot(test, 100*kde(test), '--')
    plt.xlabel(variable_name.replace("_"," "))
    plt.ylabel("Count")
    plt.title("Concatenated distributions for " + variable_name.replace("_"," "))
    plt.xlim(min(variable.cumul_all.raw) -1, max(variable.cumul_all.raw) +1 )
    plt.ylim(ymax = max(nbr) +2)
    plt.figlegend([patches[0], line[0]],["Raw","Best fit"],"center right")
    plt.savefig(os.path.join(graphspath, "distribution_graphs", subpath, value_name + "_concatenated_distributions_for_"+ variable_name + "." + graphformat), format =  graphformat) 
    plt.clf()
    
    ##all simulations
    simline = []
    simtext = []
    bestline = []
    besttext = []
    find_ymax = 0
    fig = plt.figure()
    fig.add_axes((0.1,0.1,0.63,0.80))
    for i in range(len(variable.distributions)):
        nbr, bins, patches = plt.hist(variable.distributions[i].raw,range=(bins[0],bins[-1]),histtype = 'step')
        simtext.append("Simulation "+ str(i+1))
        simline.append(patches[0])
        if max(nbr) > find_ymax:
            find_ymax = max(nbr)
        kde = stats.gaussian_kde(variable.distributions[i].raw)
        dist = np.arange(min(variable.distributions[i].raw) -1,max(variable.distributions[i].raw) +1,0.1)
        lines = plt.plot(dist, len(variable.distributions[i].raw)*kde(dist), '--')            
        besttext.append("Best fit for\nsimulation "+ str(i+1))
        bestline.append(lines[0])
    handles = simline + bestline
    labels = simtext + besttext       
            
    plt.xlabel(variable_name.replace("_"," "))
    plt.ylabel("Count")
    plt.title("Individual distributions of all simulations for\n" + variable_name.replace("_"," "))
    plt.figlegend(handles, labels,"center right")
    #plt.legend(bbox_to_anchor = (1.3, 0.5))
    plt.ylim(ymax = find_ymax + 2) 
    plt.xlim(min(variable.cumul_all.raw) -1, max(variable.cumul_all.raw) +1 )      
    plt.savefig(os.path.join(graphspath, "distribution_graphs", subpath, value_name + "_simulations_distributions_for_"+ variable_name + "." + graphformat), format =  graphformat)    
    plt.clf()                  
    return True
    
#######   Legacy  ############
'''    
def modifyINPX(values, path, originalpath):   #path = [directory, filename]    originalpath:path to the original file
    dirname = path[0]
    name = path[1]    
    
    ''' '''
    Values: [ [variablename,value] , [variablename,value] , ... ]
    w99cc0  w99cc4  w99cc8
    w99cc1  w99cc5  w99cc9
    w99cc2  w99cc6
    w99cc3  w99cc7
    ''' '''   
    
    out = open('{}/'+name+'.inpx'.format(dirname), 'w')   
    
    original = open(originalpath)     
    for line in original:    
        if re.match('carFollowModType=', line):            
            for value in values:
                line = re.sub(values[value][0]+'="[0-9\.]"', values[value][0]+'="'+values[value][1]+'"', line)
                
        out.write(line)
    return True
'''    