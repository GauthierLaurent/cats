# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:32:08 2014

@author: Laurent
"""

##################
# Import Libraries
##################
#Native
import os, time, shutil
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

#Internal
import lib.define as define

##################
# Writing tools
##################

def createSubFolder(folderpath, filename, Archives = True):
    '''Creates a folder named "filename"
    
       If such a folder already exists at the designated location and Archives = True, creates a subfolder 
       named "Archives" and another subfolder named "yyyymmdd_hhmmss" and moves all files in the folder 
       to that subfolder'''
       
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

def writeListToCSV(lists, name):    
    out = open(name, 'w')
    for sublist in lists:
        writeInFile(out,sublist)
    out.close()
    
def defineName(dirname, TypeOfAnalysis):
    '''Finds the folders named after the analysis type and find the greatest increment'''
    last_num = 0
    
    past_analysis  = [f for f in os.listdir(dirname) if "Analysis" in f]
    if past_analysis != []:
        for f in past_analysis:
            striped = f.strip('.csv')
            if TypeOfAnalysis in f:
                num = int(striped.split('_')[-1])
                if num > last_num: last_num = num
    
    last_num += 1  
    filename = TypeOfAnalysis + '_Analysis_' + str(last_num)
    
    return filename, last_num

def findCalibName(dirname):
    '''Finds the folders named after the analysis type and find the greatest increment'''
    last_num = 0
    
    past_analysis  = [f for f in os.listdir(dirname) if "point" in f]
    if past_analysis != []:
        for f in past_analysis:
            striped = f.strip('.csv')
            num = int(striped.split('_')[-1])
            if num > last_num: last_num = num
    
    last_num += 1  
    filename = 'point' + str(last_num)
    
    return filename
    
    
def writeHeader(dirname, variables, TypeOfAnalysis, first_seed, nbr_runs, warmUpTime, desiredSimulatedTime, Inpxname, values = None, multiProcTempFile = False):
    '''writes the header. For sensitivity analysis, the header has 19 lines'''
    
    if multiProcTempFile is False:
        name, last_num = defineName(dirname, TypeOfAnalysis) 
        subdirname = createSubFolder(os.path.join(dirname,name), name, Archives = False)
        filename = '{}/'+ name + '.csv'
    else:
        subdirname = dirname
        filename = '{}/' + multiProcTempFile + '.csv'
        last_num = int(multiProcTempFile.split('_')[2])
    
    #header writing
    out = open(filename.format(subdirname), "w")
    out.write("Vissim filename: " + str(Inpxname) + "\n")
    out.write("Analysis number: " + str(last_num) + "\n")
    out.write("Type of analysis: " + str(TypeOfAnalysis) + "\n")
    if TypeOfAnalysis != "Student":
        out.write("Number of runs per tested variables: " + str(nbr_runs) + "\n")  
    out.write("First seed: " + str(first_seed) + "      (increment: 1) \n")       
    out.write("Simulation lenght: " + str(desiredSimulatedTime) + "\n")  
    out.write("Warm up time: " + str(warmUpTime) + "\n")  
    out.write("Date: " + str(time.localtime().tm_year) + '/' + str(time.localtime().tm_mon).zfill(2) + '/'  + str(time.localtime().tm_mday).zfill(2) + "\n")
    out.write("\n")
    
    #Statistical-precision header
    if TypeOfAnalysis == "Statistical-precision":  
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
    if TypeOfAnalysis == 'Sensitivity' or TypeOfAnalysis == 'Monte Carlo': 
        out.write("*var_name: Name of the tested variable\n"
                  "Note: m = mean, fq = first quartile, md = median, tq = third quartile, std = standard deviation, %diff = relative difference with the default values results"
                  "*flow: Vehicular flow\n"
                  "*nbr_opp: Number of opportunistic lane changes\n"
                  "*nbr_man: Number of mandatory lane changes\n"
                  "*forward: Forward gaps (all lanes concatenated, calculated at the middle of each link)\n"
                  "*LC_Aopp: Opportunistic lane change gap calculated after the lane changing vehicule inserted into the new lane \n"
                  "*LC_Bopp: Opportunistic lane change gap calculated before the lane changing vehicule began changing lane\n"
                  "*LC_Aman: Mandatory lane change gap calculated after the lane changing vehicule inserted into the new lane \n"
                  "*LC_Aman: Mandatory lane change gap calculated before the lane changing vehicule began changing lane \n"
                  "\n"
                  "var_name;")
        for var in variables:
            out.write(str(var) + ";")
        if TypeOfAnalysis == 'Sensitivity': 
            out.write("flow;nbr_opp;% diff;nbr_man;% diff;"
                      "m_forward;% diff;fq_forward;% diff;md_forward;% diff;tq_forward;% diff;std_forward;% diff;"
                      "m_LC_Aopp;% diff;fq_LC_Aopp;% diff;md_LC_Aopp;% diff;tq_LC_Aopp;% diff;std_LC_Aopp;% diff;"
                      "m_LC_Bopp;% diff;fq_LC_Bopp;% diff;md_LC_Bopp;% diff;tq_LC_Bopp;% diff;std_LC_Bopp;% diff;"
                      "m_LC_Aman;% diff;fq_LC_Aman;% diff;md_LC_Aman;% diff;tq_LC_Aman;% diff;std_LC_Aman;% diff;"
                      "m_LC_Bman;% diff;fq_LC_Bman;% diff;md_LC_Bman;% diff;tq_LC_Bman;% diff;std_LC_Bman;% diff\n")        
        else:
            out.write("flow;nbr_opp;nbr_man;m_forward;m_LC_Aopp;m_LC_Bopp;m_LC_Aman;m_LC_Bman;\n")        
   
    #Calibration header
   
    return out, subdirname
    
def intoList(out, mylist):
    '''iterates over mylist to write it's content into the list given in out'''
    for i in mylist:
        if isinstance(i, list) is True:
            intoList(out, i)            
        else:
            out.append(i)
    return out   

def writeToOneList(*args):
    '''Take any number of arguments and returns a single list'''  
    out = []    
    for arg in list(args):
        if isinstance(arg, list) is True:
            out = intoList(out, arg)
        else:
            out.append(arg)
    return out
    
def writeInFile(out, *args):
    '''Writes any number of arguments into the file given in out'''
    
    variables = writeToOneList(list(args))
    for var in variables:
        if isinstance(var,float) is True:
                out.write(str(round(var,4)) + ";")
        else:
            out.write(str(var) +";")
    out.write("\n")

def verboseIntro(commands, config, TypeOfAnalysis):
    print ('--> Starting a ' + TypeOfAnalysis + ' Analysis with the following options: ')
    if commands.multi or commands.multi_test or commands.mode or commands.vis_save:
        print ('      -- -- -- -- -- -- -- -- -- -- -- -- -- --   ')
        if commands.multi:
            print (' |-> Multiprocessing activated ')
        if commands.multi_test:
            print (' |-> Multiprocessing debug mode activated ')
        if commands.mode:
            print (' |-> Test mode activated ')
        if commands.vis_save:
            print (' |-> Graphic saving mode activated \n'
                   '        *files will be saved as ' + str(commands.fig_format))                   
            
    print ('      -- -- -- -- -- -- -- -- -- -- -- -- -- --     \n'
           'Inpx to process:       ' + str(config.inpx_name) + '\n'   
           'Simulation steps:      ' + str(config.sim_steps)      )
    print ('      -- -- -- -- -- -- -- -- -- -- -- -- -- --         ')
    if TypeOfAnalysis == 'Sensitivity': 
        print('Number of points:      ' + str(config.nbr_points)    + '\n'
              'Number of simulations: ' + str(config.nbr_runs)       )
    print ('Simulation time:       ' + str(config.simulation_time)   + '\n'
           'Simulation warm up:    ' + str(config.warm_up_time)      )
    if TypeOfAnalysis == 'Statistical-precision':
        print('      -- -- -- -- -- -- -- -- -- -- -- -- -- --         \n'
              'Desired pourcentage error on the mean confidence interval: ' + str(config.desired_pct_error) +' %')
    print''
    
def timeStamp(variables, points, sim, itt = None):
    text = []
    total_time = time.clock()
    avg_per_point = total_time/(len(variables) * points + 1 ) 
    avg_per_sim   = total_time/((len(variables) * points + 1 )*sim)
    
    #the append([]) serves to add an empty line before the time marker when using writeInFile
    text.append([])
    text.append(["Total elapsed time (sec) :",total_time])
    if itt is not None: text.append(["Number of itaration required :", itt])
    text.append(["Average time per point (sec) :",avg_per_point])
    text.append(["Average time per simulation (sec): ",avg_per_sim])
    
    return text
        
def printStatGraphs(graphspath,variable,value_name, variable_name, graphformat, nsim, subpath = ""):
    '''create graphs for a type 'Stats' variable'''

    #creating the cumulative graph                         
    if variable.distributions[0].value != []:    #checks if the variable is empty
        plt.plot(variable.distributions[0].value, variable.distributions[0].cumul)
        plt.xlabel(variable_name.replace("_"," "))
        plt.ylabel("Count")
        plt.title("Cumulated distribution for " + variable_name.replace("_"," "))
        plt.savefig(os.path.join(graphspath, "cumul_dist_graphs", subpath, value_name + "_cumulative_distribution_for_"+ variable_name + "." + graphformat), format =  graphformat)
        plt.clf()
        plt.close()
    
    #creating the distributions graph
    ##concatenated distributions
    if variable.cumul_all.raw != []:                                                        #checks if the variable is empty  
        fig = plt.figure()
        fig.add_axes((0.1,0.1,0.65,0.80))
        nbr, bins, patches = plt.hist(variable.cumul_all.raw,100,histtype = 'step')
        #kde is the equation of the cumulated gaussians
        kde = stats.gaussian_kde(variable.cumul_all.raw)                                    
        test = np.arange(min(variable.cumul_all.raw) -1,max(variable.cumul_all.raw) +1,0.1)
        #kde(array) returns the probability (0..1) for each variables in the array.
        #The integral of the resulting curve = 1, so to scale it with the raw data, we multiply it by the number of variables in the data... ie: len(raw_data)       
        line = plt.plot(test, len(variable.cumul_all.raw)*kde(test), '--')                            
        plt.xlabel(variable_name.replace("_"," "))
        plt.ylabel("Count")
        plt.title("Concatenated distributions for\n" + variable_name.replace("_"," "))
        plt.xlim(min(variable.cumul_all.raw) -1, max(variable.cumul_all.raw) +1 )
        plt.ylim(ymax = max(nbr) +2)
        plt.figlegend([patches[0], line[0]],["Raw","Best fit"],"center right")
        plt.savefig(os.path.join(graphspath, "distribution_graphs", subpath, value_name + "_concatenated_distributions_for_"+ variable_name + "." + graphformat), format =  graphformat) 
        plt.clf()
        plt.close(fig)
    
        ##all simulations - linked to the concatenated because it allows us to have bins that convers equally each distributions and so make them comparable   
        simline = []
        simtext = []
        bestline = []
        besttext = []
        find_ymax = 0
        fig = plt.figure()
        fig.add_axes((0.1,0.1,0.63,0.80))
        
        if variable_name == "Forward_gaps":
            chunks = define.toChunks(len(variable.distributions)//nsim, range(len(variable.distributions)))
        for i in range(len(variable.distributions)):
            if variable.distributions[i].raw != []: #checks if the variable is empty
                nbr, bins, patches = plt.hist(variable.distributions[i].raw,range=(bins[0],bins[-1]),histtype = 'step')
                
                if variable_name == "Forward_gaps":
                    for chunk in chunks:
                        if i in chunk:                    
                            simtext.append("Simulation "+ str(i//(len(variable.distributions)//nsim) + 1) +"\nLane " + str(i - chunk[0] +1) + "/" + str(len(variable.distributions)//nsim) )

                else:
                    simtext.append("Simulation "+ str(i+1))
                
                simline.append(patches[0])
                if max(nbr) > find_ymax:
                    find_ymax = max(nbr)
                kde = stats.gaussian_kde(variable.distributions[i].raw)
                dist = np.arange(min(variable.distributions[i].raw) -1,max(variable.distributions[i].raw) +1,0.1)
                lines = plt.plot(dist, len(variable.distributions[i].raw)*kde(dist), '--')            
                if variable_name == "Forward_gaps":
                    besttext.append("Best fit for\n"+ str(i+1))
                else:
                    besttext.append("Best fit for\nsimulation"+ str(i+1))
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
        plt.close(fig)                  
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