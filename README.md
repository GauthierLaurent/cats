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
	
	Due to the sheer volume of data, it is recommended to use a 64-bit Python
	interpreter and libraries.
	
Instructions
============
	This package uses Vissim 6.0 to perform the required calculations. Vissim
	outputs are transformed into trajectory data by Traffic-Intelligence. To
	perform its analysis, PvcTools will need to be directed to the folder 
	containing the Vissim network to be analysed and told the name of the .inpx
	file corresponding to that network.

	This package provides a library of tools used for parameters calibration 
	of Vissim 6.0, including a Student t-test analysis to determine the number
	of simulations needed to achieve a certain degree of confidence with the
	simulation results, a Sensitivity analysis to determine to witch extent does
	certain parameters affect a given master variable, and a Calibration analysis
	to find the values of a set of parameters best describing a real life scenario
	provided in to form of a video that can be executed successfully analysed by
	Traffic-Intelligence.
	
	To run the program, simply execute pvctools.py with a series of commands.
	Run with -h for help. 
	
        -w    default='99',   Set the car following model - Default is Wiedemann 99
        -c    default=False,  Set the working analysis to "Calibration"
        -d    default=False,  Set the working analysis to "Student t-test"
        -m    default=True,   Enables or disables multiprocessing
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

   

	
	PvcTools will create itself the result folders and files directly into that 
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