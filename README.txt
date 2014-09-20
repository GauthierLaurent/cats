################################################################################
                                  PVCTOOLS                                       
Laurent Gauthier, Ecole Polytechnique de Montreal, 2014
version ALPHA u. 17-07-2014
################################################################################
	
Licence
========
	
Platform and mandatory programs
===========
	Windows 7 to 8.1 32-bit or 64-bit
	Vissim 6.0 32-bit or 64-bit COM enabled (no student or demo version)
	Python 2.7 or higher
	Developed and tested on:
		Spyder 2.2.5 Windows 7 to 8.1 64-bit
		ipython Windows 7 to 8.1 64-bit
		Vissim 6.0 64-bit
Dependencies
============
	Python 2.7				http://www.python.org/
	scipy stack 			http://www.scipy.org/stackspec.html
		numpy               (included)
		scipy               (included)
		matplotlib          (included)
	Traffic-Intelligence	http://bitbucket.org/Nicolas/trafficintelligence/
		openCV				http://opencv.willowgarage.com/wiki/
		PIL					http://www.pythonware.com/products/pil/
		SQLAlchemy			http://www.sqlalchemy.org/
	Win32com				https://wiki.python.org/moin/PythonWin	
	Optional:	
		Mencoder
	
Installation
============
	Traffic-Intelligence python modules do not need to be compiled, simply add
	.../traffic-inteligence/Python/ to your PYTHONPATH.	All other precompiled
	python dependencies can be installed in Linux through the usual channels or 
	downloaded for Windows here: http://www.lfd.uci.edu/~gohlke/pythonlibs/
	
	
Instructions
============
	This package uses Vissim 6.0 to perform the required calculations. Vissim
	outputs are transformed into trajectory data by Traffic-Intelligence. To
	perform its analysis, PvcTools will need to be directed to the folder 
	containing the Vissim network to be analysed and told the name of the .inpx
	file corresponding to that network. A .csv file containing upper level
	informations about the network need also be included in the folder containing
	the .inp file. More on that file below.

	This package provides a library of tools used for parameters calibration 
	of Vissim 6.0, including a Student t-test analysis to determine the number
	of simulations needed to achieve a certain degree of confidence with the
	simulation results, a One at a time Sensitivity analysis to determine to
	witch extent does certain parameters affect a given master variable, a Monte
	Carlo analysis to push this study further by capturing the interaction effects
	between parameters at the cost of a lot more calculation time, and a Calibration
	analysis to find the values of a set of parameters best describing a real life
	scenario provided in to form of a video that can be executed successfully
	analysed by Traffic-Intelligence.


	Scripts
	=======
	PvcTools is in fact composed of many stand-alone scripts. PvcTools-Sensitivity
	is the main tool to run to study the effects of the vissim parameters. This
	script can be run will all the available functionalities. PvcTools-Calibration
	is designed to work in conjunction with the NOMADS optimization tool and is
	thus written as a blackbox scripts that will take its own decisions based on
	the .cfg file and the inputs given by NOMADS. Most commands are unavailable due
	to the fact that the program is called by NOMADS and not by the user. Finally, a
	script to produce related graphs is provided.


	Options and commands
	====================
	To run the program, simply execute pvctools.py with a series of commands.
	Run with -h for help. 
	
        -d    default=False,  Sets the working analysis to "Student t-test"
	-o    default=False,  Sets the working analysis to "Monte Carlo"
        -m    default=True,   Enables or disables multiprocessing
	-u    default=False,  Enables a test mode for the multiprocessing
        -s    default=True,   Set the working analysis to "Sensitivity" - on by default    
        -f                    Load specific inpx file (overrides the one provided in pvc.cfg)
        -l    default=False,  Activates Vissim lane change (.swp) outputs
        -v    default=1,      Level of detail of results')
        -t    default=False,  Put the code into test mode, bypassing Vissim and
	                      generating random outputs	
        -a    default=False,  Save figures
        --figure-format
	      default='png'   Force saving images to a particular format. 
	                      Enter a supported extensions (e.g. png, svg, pdf)

Needed files
============    
	PvcTools requires some files to run the analysis. On top of the .inpx neeeded by
	Vissim, a config (pcv.cfg) file and a network data (INPX_NAME.csv) file are
	required.


	Config file
	===========


	Network data file
	=================
	This file contains upper level informations about the vissim network to be
	analysed. It is used to store informations about corridors, that is: to merge
	vissim links and connectors into single analisis entity. This can then be used,
	amongs other things, to analyse whether a lane change is part of the O-D matrix
	of a vehicule or if it falls under an opportunistic move to preserve the desired
	speed while following a slower vehicule. The second major use of the feature is
	to allow the construction of a detailed network, while restricting the analysis
	to a subpart of it. For example, one could wish to analyse only links and skip the
	connectors during the analysis, or the analyse only the exit ramp of a highway,
	while still needing to modelise the highway in the network to produce relevant
	behaviors.

	The structure of this file is as follow:
	   - The name MUST be the same as the vissim network file (.inpx), and be placed
	     in the same directory.
	   - Any line beginning with # will be ignored
	   - For each corridors to be formed, the data to be read by PvcTools must be placed 
	     on a different line. The information contained on the line must be placed in this 
	     particular order, and be separated by semicolons:
                                  Name; Dir; Vis_corr; Vis_eval; TI_corr; TI_eval
		where:
		   'Name'     is the name of the corridor
		   'Dir'      is the side linking to the next corridor, either 'r' for right or
			      'l' for left
		   'Vis_corr' is a list of vissim links forming the corridor. The numbers must be
			      separated by '-'
		   'Vis_eval' is the list of links contained in the Vis_corr where PvcTools will 
			      perform evaluations. If all the links for Vis_corr are written, all 
			      links will be fully calculated. If no links are entered, the corridor 
			      will be ignored. This could also be achieved by not creating the 
			      corridor in the first place.
		   'TI_corr'  same as Vis_corr but for video data to be analysed by Traffic
			      Intelligence
		   'TI_eval'  same as Vis_eval but for video data to be analysed by Traffic
			      Intelligence
		


Result files
============	
	PvcTools will itself create the result folders and files directly into that 
	main folder. The general folder structure of an analysis will then look like 
	this (items marked by an * are generated by the program):
	
	**  Sensitivity analysis  **       #	**  Calibration analysis  **
	                                   #
	Vissim-Network-Folder              #	Vissim-Network-Folder	
	|--Network.inpx                    #	|--Network.inpx
	|--Sensitivity_Analysis_1*         #	|--Calibration_Analysis_1*
	|  |--Sensitivity_Analysis_1.csv*  #	  		
	|  |--outputs*                     #	   **************************
	|  |	|--variable_1*             #	   *STILL UNDER CONSTRUCTION*
	|  |	|  |--variable_1.inpx*     #	   **************************
	|  |	|  --Vissim output files   #
	|  |	|                          #	
	|  |	|--variable_2*             #
	|  |	|  |--variable_2.inpx*     #
	|  |	|  --Vissim output files   #
	|  |   ...                         #
	|  |--graphs*                      #
	|  |--cumul_dist_graphs            #
	|  |	|--variable_1*             #
	|  |	|--variable_2*             #
	|  |   ...                         #
	|  --distribution_graphs           #
	|   	|--variable_1*             #
	|   	|--variable_2*             #
	|      ...                         #
	|                                  #
	|--Sensitivity_Analysis_2*         #
   ...      |                          #
	       ...                         #
	
	


#################################################################################