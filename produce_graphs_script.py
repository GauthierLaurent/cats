# -*- coding: utf-8 -*-
#%run produce_graphs_script.py Statistical-precision_Analysis_38
"""
Created on Thu Jul 17 11:29:28 2014

@author: Laurent
"""

################################ 
#        Importing dependencies       
################################ 
#Native dependencies
import os, sys, optparse

#Internal
import lib.outputs as outputs
import lib.tools_write as write 
import lib.tools_config as config

################################ 
#        Load settings       
################################    
commands = config.commands(optparse.OptionParser())
config   = config.Config('pvc.cfg')

################################ 
#        working function       
################################
def processFolder(working_dir, graphspath, working_variable, config):
    if working_variable is not None:
        print("Traitement des fichiers zfp dans le repertoire .\outputs\{}".format(working_variable))
    else:
        print("Traitement des fichiers zfp dans le repertoire .\outputs")
    
    #opening the files and calculating needed information
    flow, oppLCcount, manLCcount, forFMgap, oppLCagap, oppLCbgap, manLCagap, manLCbgap = outputs.treatVissimOutputs([f for f in os.listdir(working_dir) if f.endswith("fzp")], [working_dir, config.sim_steps, config.warm_up_time, False])
    
    #printing graphs
    variables = [forFMgap,oppLCagap,oppLCbgap,manLCagap,manLCbgap]
    variables_name =["Forward_gaps","Opportunistic_lane_change_'after'_gaps","Opportunistic_lane_change_'before'_gaps","Mandatory_lane_change_'after'_gaps","Mandatory_lane_change_'before'_gaps"]
    for var in range(len(variables)):
            
        write.printStatGraphs(graphspath,variables[var], str(working_variable), variables_name[var], commands.fig_format, config.nbr_runs, working_variable)

################################ 
#        Treat calling arguments       
################################ 
dirname = ""
dir_pos = 0
variable_name = ""

if len(sys.argv) > 3 or len(sys.argv) < 2:
    sys.exit("This scripts accepts minimum 1 argument and maximum 2 arguments")

if len(sys.argv) >= 2:
    for i in range(len(sys.argv)):
        if "analysis" in str(sys.argv[i].lower()):
            dirname = sys.argv[i]
            dir_pos = i

if not dirname:
    sys.exit("No Analysis directory could be found in the arguments given")
            
if len(sys.argv) == 3:
    variable_name = sys.argv[3 - dir_pos]

################################ 
#        Actual program code       
################################

#getting the name of the file associated with the graphs
if commands.file:
    mainfile = commands.file.strip('.inpx') 
else:
    mainfile = config.inpx_name.strip('.inpx')

#working path
dirpath = os.path.join(config.path_to_inpx, "Analysis_on__" + mainfile, dirname)

#looking if the outputs subfolder exists
if not os.path.isdir(os.path.join(dirpath , "outputs")):
    sys.exit("The output folder for that Analysis does not exist")
    
#creating the main subfolders
if not os.path.isdir(os.path.join(dirpath , "graphs")):
    graphspath = write.createSubFolder(os.path.join(dirpath ,"graphs"), "graphs")
    if not os.path.isdir(os.path.join(graphspath, "cumul_dist_graphs")):
        write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs"), "cumul_dist_graphs")
        write.createSubFolder(os.path.join(graphspath, "distribution_graphs"), "distribution_graphs")
else:
    graphspath = os.path.join(dirpath , "graphs")

#getting the names of the folders containing the files
if 'precision' not in dirname:
    if not variable_name:   
        variable_folder_list = [f for f in os.listdir(os.path.join(dirpath , "outputs")) if os.path.isdir(os.path.join(dirpath , "outputs", f))]
    else:
        variable_folder_list = [variable_name]
    
    for i in range(len(variable_folder_list)):
        
        #checking if the output folder contains files:
        filenames  = [f for f in os.listdir(os.path.join(dirpath , "outputs", variable_folder_list[i])) if f.endswith("fzp")]
        if filenames == []:
            print "No .fzp files found in the folder " + str(os.path.join(dirpath, "outputs", variable_folder_list[i]))
            pass
        
        else:    
            #creating the graphics subfolders          
            write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs", str(variable_folder_list[i])), "cumul_dist_graphs" + os.sep + str(variable_folder_list[i]))
            write.createSubFolder(os.path.join(graphspath, "distribution_graphs", str(variable_folder_list[i])), "cumul_dist_graphs" + os.sep + str(variable_folder_list[i]))

            processFolder(os.path.join(dirpath , "outputs", variable_folder_list[i]), graphspath, str(variable_folder_list[i]), config)    
else:   
    #checking if the output folder contains files:
    filenames  = [f for f in os.listdir(os.path.join(dirpath , "outputs")) if f.endswith("fzp")]
    if filenames == []:
        print "No .fzp files found in the folder " + str(os.path.join(dirpath, "outputs"))
        pass
    
    else:    
        #creating the graphics subfolders          
        write.createSubFolder(os.path.join(graphspath, "cumul_dist_graphs"), "cumul_dist_graphs")
        write.createSubFolder(os.path.join(graphspath, "distribution_graphs"), "cumul_dist_graphs")

        processFolder(os.path.join(dirpath , "outputs"), graphspath, None, config)
#
#filenames  = [f for f in os.listdir(dirname) if f.endswith("knr")]
#out = open("{}/concat.csv".format(dirname), "w")
#out.write("VehNo; VehType; TStart; TEnd; StartLink; StartLane; StartPos; NodeNo; Movement; FromLink; ToLink; ToLane; ToPos; Delay; TStopd; Stops; No_Pers;Filename\n")
#for filename in filenames:
#	f = open(dirname+"/"+filename)
#	for i in range(9):
#		f.readline()
#	for l in f:
#		out.write(l.strip()+filename+"\n")
#	f.close()
#out.close()
