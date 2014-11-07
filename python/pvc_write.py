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
import matplotlib.pylab as plb
import numpy as np
from scipy import stats
import cPickle as pickle

#Internal
import pvc_define as define

##################
# Folder tools
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
    '''Finds the folders named point_x and find the greatest increment x'''
    last_num = 0
    
    past_analysis  = [f for f in os.listdir(dirname) if "point" in f]
    if past_analysis != []:
        for f in past_analysis:
            striped = f.strip('.csv')
            num = int(striped.split('_')[-1])
            if num > last_num: last_num = num
    
    last_num += 1  
    filename = 'point_' + str(last_num)
    
    return filename

################################ 
#        Calibration history functions       
################################
def read_history(filename):
    '''finds the number of the last recorded evaluation and returns the number of the new evaluation'''
    last_num = 0
    with open(os.path.join(os.getcwd(),filename), 'r') as hist:
        for l in hist:
            if l.strip() != '' and l.startswith('#') is False:
                last_num += 1
    return last_num + 1

def create_history(dirname, filename, networks):
    with open(os.path.join(dirname, filename), 'r') as hist:
        hist.write('Itt\t|\tpoint\t|\t')
        for net in xrange(len(networks)):
            for comp in xrange(len(networks[net].videoComparison)):
                hist.write('Network_'+str(net)+'Video_'+str(comp)+'|\t')
		
        hist.write('fout\n')		
	
def write_history(last_num, points, networks, fout,  dirname, filename):   
    with open(os.path.join(dirname, filename), 'a') as hist:
        hist.write(str(last_num)+'\t')
        hist.write("|\t")

        #tried point
        for p in points:
            hist.write(str(p)+'\t')
        hist.write("|\t")

        #secondary comparaison
        for net in xrange(len(networks)):
            for comp in networks[net].videoComparison:
                variables = writeToOneList(list(comp))
                for v in xrange(len(variables)):
                    if v == 4:
                        hist.write('*\t')
                    hist.write(str(variables[v]) +'\t')
                hist.write("|\t")

        #fout
        hist.write(str(fout)+'\n')

################################ 
#        NOMAD handling functions       
################################ 
def read_from_NOMAD(input_name):
    points = []
    with open(input_name, 'r') as f:
        for l in f:
            inter = l.strip().replace('\t',' ').split(' ')
            for i in inter:
                points.append(float(i))
    return points

def write_for_NOMAD(output_name, fout):
    with open(output_name, 'w') as f:
        f.write(str(fout))
        
################################ 
#        Serialized data files     
################################
def write_traj(depositpath,name,opp_LC_count,man_LC_count,flow,forward_gaps,opp_LC_agaps,opp_LC_bgaps,man_LC_agaps,man_LC_bgaps,forwar_speed):
    '''dumps data into a file named name.traj in the folder provided in depositpath'''    
    with open(os.path.join(depositpath, name + '.traj'), 'wb') as output:       
        pickle.dump(define.version(),    output, protocol=2)
        pickle.dump(opp_LC_count, output, protocol=2)
        pickle.dump(man_LC_count, output, protocol=2)
        pickle.dump(flow,         output, protocol=2)
        pickle.dump(forward_gaps, output, protocol=2)
        pickle.dump(opp_LC_agaps, output, protocol=2)
        pickle.dump(opp_LC_bgaps, output, protocol=2)
        pickle.dump(man_LC_agaps, output, protocol=2)
        pickle.dump(man_LC_bgaps, output, protocol=2)
        pickle.dump(forwar_speed, output, protocol=2)

def load_traj(fullpath):
    '''loads data from the traj file provided in full path
    full path must end with \name.traj'''
    with open(fullpath, 'rb') as input_file:
        version      = pickle.load(input_file)
        opp_LC_count = pickle.load(input_file)
        man_LC_count = pickle.load(input_file)
        flow         = pickle.load(input_file)
        forward_gaps = pickle.load(input_file)
        opp_LC_agaps = pickle.load(input_file)
        opp_LC_bgaps = pickle.load(input_file)
        man_LC_agaps = pickle.load(input_file)
        man_LC_bgaps = pickle.load(input_file)
        forwar_speed = pickle.load(input_file)
        
    if define.verify_data_version(version):
        return [opp_LC_count, man_LC_count, flow, forward_gaps, opp_LC_agaps, opp_LC_bgaps, man_LC_agaps, man_LC_bgaps, forwar_speed]
    else:
        return ['TrajVersionError']

def write_calib(working_path, parameters, variables, networks):
    with open(os.path.join(working_path,'pvcdata.calib'), 'wb') as trans:
        pickle.dump(parameters, trans, protocol=2)
        pickle.dump(variables, trans, protocol=2)
        pickle.dump(networks, trans, protocol=2)

def load_calib():
    '''loads pvcdata.calib''' 
    with open(os.path.join(os.getcwd(),'pvcdata.calib'), 'rb') as input_file:
        parameters   = pickle.load(input_file)
        variables    = pickle.load(input_file)
        networks     = pickle.load(input_file)

    return parameters, variables, networks
    
##################
# Report tools
##################    
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
    
    #Statistical-precision subheader
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
        
    #Sensitivity subheader
    if TypeOfAnalysis == 'Sensitivity' or TypeOfAnalysis == 'Monte Carlo': 
        out.write("*var_name: Name of the tested variable\n"
                  "Note: m = mean, fq = first quartile, md = median, tq = third quartile, std = standard deviation, %diff = relative difference with the default values results"
                  "*flow: Vehicular flow\n"
                  "*nbr_opp: Number of opportunistic lane changes\n"
                  "*nbr_man: Number of mandatory lane changes\n"
                  "*forward: Forward gaps (all specified lanes concatenated, calculated at the middle of each link)\n"
                  "*LC_Aopp: Opportunistic lane change gap calculated after the lane changing vehicule inserted into the new lane \n"
                  "*LC_Bopp: Opportunistic lane change gap calculated before the lane changing vehicule began changing lane\n"
                  "*LC_Aman: Mandatory lane change gap calculated after the lane changing vehicule inserted into the new lane \n"
                  "*LC_Aman: Mandatory lane change gap calculated before the lane changing vehicule began changing lane \n"
                  "*f_speed: Speed distribution (all specified lanes concatenated, calculated at the same point as forward gaps)\n"
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
                      "m_LC_Bman;% diff;fq_LC_Bman;% diff;md_LC_Bman;% diff;tq_LC_Bman;% diff;std_LC_Bman;% diff;"
                      "m_f_speed;% diff;fq_f_speed;% diff;md_f_speed;% diff;tq_f_speed;% diff;std_f_speed;% diff\n"
                      )        
        else:
            out.write("flow;nbr_opp;nbr_man;"
                      "m_forward;fq_forward;md_forward;tq_forward;std_forward;"
                      "m_LC_Aopp;fq_LC_Aopp;md_LC_Aopp;tq_LC_Aopp;std_LC_Aopp;"
                      "m_LC_Bopp;fq_LC_Bopp;md_LC_Bopp;tq_LC_Bopp;std_LC_Bopp;"
                      "m_LC_Aman;fq_LC_Aman;md_LC_Aman;tq_LC_Aman;std_LC_Aman;"
                      "m_LC_Bman;fq_LC_Bman;md_LC_Bman;tq_LC_Bman;std_LC_Bman;"
                      "m_f_speed;fq_f_speed;md_f_speed;tq_f_speed;std_f_speed;\n"
                      )
   
    #Calibration header
   
    return out, subdirname
    
def writeRealDataReport(dirname, video_name, inpxname, min_time, max_time, speed_centiles, other_info):
    '''writes the report file.
       Speed_centiles MUST be of the form [list_of_name,list_of_values]
       other_info Must include directly the format to output'''
    
    name = 'Video_analysis_of_'+str(video_name).strip('.sqlite')
    filename = '{}/'+ name + '.csv'
    
    #header writing
    out = open(filename.format(dirname), 'w')
    out.write('Video analysed: ' + str(video_name) + '\n')
    out.write('Associated Vissim file: ' + str(inpxname) + '\n')
    if min_time or max_time is not None:
        if min_time is None:
            out.write('Video analysed from time 0 to '+str(max_time)+' (frames)\n')
        elif max_time is None:
            out.write('Video analysed from time '+str(min_time)+' (frames) till end\n')
        else:
            out.write('Video analysed from time '+str(min_time)+' to '+str(max_time)+' (frames)\n') 
    out.write('Date: ' + str(time.localtime().tm_year) + '/' + str(time.localtime().tm_mon).zfill(2) + '/'  + str(time.localtime().tm_mday).zfill(2) + '\n')
    out.write('\n')

    #speed centile description
    out.write('Usefull speed centiles for vissim calibration:\n')
    writeInFile(out, ['centile (%)'] + speed_centiles[0])
    writeInFile(out, ['speed (m/frame)*'] + speed_centiles[1])
    out.write('*m/s = (m/frame)*fps  and km/h = (m/frame)*fps*3.6\m')
    out.write('\n')
    
    #subheader
    for i in other_info:       
        writeInFile(out, i)  
      
    out.close()
   
    return
    
def writeListToCSV(lists, name):    
    out = open(name, 'w')
    for sublist in lists:
        writeInFile(out,sublist)
    out.close()
    
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
    
##################
# In-console print tools
##################
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

##################
# Graphic tools
##################        
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

def plot_st(objects, alignments, fps, dirname):
    '''generates a time-space diagram for each alignment'''
    for a in xrange(len(alignments)):
        fig = plt.figure()
        for o in objects:
            t = []
            s = []
            for pos in xrange(len(o.getCurvilinearPositions().getSCoordinates())):
                if o.getCurvilinearPositions().getLanes()[pos] == a:
                    t.append((o.getFirstInstant()+pos)/float(fps))
                    s.append(o.getCurvilinearPositions().getSCoordinates()[pos])
            plt.plot(t,s,'b')
        
        plt.xlabel('time (sec)' )
        plt.ylabel('distance (m)')
        plt.title('Time-space diagram for alignment ' + alignments[a])
        plt.savefig(os.path.join(dirname, 'Time-space diagram for alignment ' + alignments[a]))
        plt.clf()
        plt.close(fig)    
    return
    
def plot_qt(time_serie, gaps_serie, align_num, dirname, fps):
    '''generates a flow on time diagram for alignment number "align_num" using gap information
       only handles one lane at a time'''
       
    time = list(np.asarray(time_serie)/fps)
    flow = list(np.asarray(gaps_serie)/fps*3600)
    
    fig = plt.figure()
    plt.plot(time, flow)
    
    plt.xlabel('time (sec)')
    plt.ylabel('flow (veh/h)')
    plt.title('Flow on alignment '+str(align_num)+' with regard to time')
    plt.savefig(os.path.join(dirname, 'Flow-time diagram for alignment ' + str(align_num)))
    plt.clf()
    plt.close(fig)    
    return
    
##################
# Drawing tools
##################
def tellMe(s, target=False):
    if(not target):
        target = plt
    
    print('Drawing console: '+s)
    plt.title(s,fontsize=14)
    plt.draw()

def drawAlign(target=False):
    ''' This module will enable user to draw alignments ontop of trajectories
        
    Note: Expects trajectory plot to be pre-drawn
    Thanks to Paul St-Aubin PvaTools
    '''
    if(not target):
        target = plt
        
    plt.setp(target.gca(), autoscale_on=False)
    
    exit_cond = False
    alignments = []
    pj = []
    j = 0
    ## Segments
    while not exit_cond:
        pts = []
        while len(pts) < 2:
            tellMe('Draw alignments. Left click: select points, right click: undo, middle click: exit.', target=target)
            pts = [list(x) for x in plb.ginput(0,timeout=-1)]
            if(len(pts) < 2):
                tellMe('Too few points, starting over.', target=target)
                time.sleep(1) # Wait a second
    
        ph = plb.plot([x[0] for x in pts], [x[1] for x in pts], 'm', lw=2 )
    
        tellMe('Save alignments? Mouse click for yes, key click for no.', target=target)
        save_cond = plb.waitforbuttonpress()
        for p in ph: p.remove()
        if(not save_cond):
            alignments.append(pts)
            pj.append(plb.plot([x[0] for x in pts], [x[1] for x in pts], 'k', lw=2))
            j += 1
        
        tellMe('Add alignments? Mouse for yes, key for no.', target=target)
        exit_cond = plb.waitforbuttonpress()
    
    return alignments


    
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