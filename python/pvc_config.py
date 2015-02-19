# -*- coding: utf-8 -*-
"""
Created on Wed Jul 09 10:18:28 2014

@author: Laurent
"""
##################
# Forword
##################
#This code is mainly imported from pvatools from Paul St-Aubin with his expressed
#permission with minor modifications to make it work within pvctools

##################
# Import Native Libraries
##################
## Native
import ConfigParser, os

##################
## The following functions are used for parsing config string data
##################
def config(config, key, default, c_type='int', c_struct='simple', section='Main'):
    ''' Handle configuration file values. '''
    if(not config.has_section(section)):    config.add_section(section)
    if(not config.has_option(section,key)): config.set(section,key,default)
    if(c_type == 'int'):
        if(c_struct == 'list1D'): return list1D(config.get(section, key))
        else:                     return config.getint(section, key)
    elif(c_type == 'float'):
        if(c_struct == 'list1D'): return list1D(config.get(section, key), i_type='float')
        else:                     return config.getfloat(section, key)
    elif(c_type == 'bool'):
        if(c_struct == 'list1D'): return list1D(config.get(section, key), i_type='bool')
        else:                     return config.getboolean(section, key)
    else:
        if(c_struct == 'list1D'): return list1D(config.get(section, key), i_type='string')
        else:                     return config.get(section, key)

def expandLiteralListRange(item, i_type='int'):
    ''' TODO: '''
    return


def list1D(item, i_type='int'):
    ''' Parse string format into 1 dimensional array (values). Will automatically generate range for int values (i.e. [1,3-5] -> [1,3,4,5]).
        
        Alternative:
        ============
        import ast
        x = '[0.90837,0.90837]'
        ast.literal_eval(x)
        '''
    item = item.translate(None, '[] \n')
    item = item.split(',')
    item = filter(None, item)
    if(len(item) > 0):
        if(i_type == 'float'):  return [float(x) for x in item]
        elif(i_type == 'bool'): return [str2bool(x) for x in item]
        elif(i_type == 'int'):  
            if(len(list(set(item))) != len(item)): allowDuplicates = True
            else:                                  allowDuplicates = False
            for i in range(len(item)):
                if('-' in item[i]):
                    temp    = item[i].split('-')
                    item.append(range(int(temp[0]),int(temp[-1])+1))
                    item[i] = None
            item = filter(None, item)
            item.sort()
            if(not allowDuplicates):
                item = list(set(item))
            return [int(x) for x in item]  
        else:                   return [x for x in item]
    else:
        return []
             

def list2D(item, i_type='int'):
    ''' Parse string format into 2 dimensional array (values). '''
    parsing = item.translate(None, ' \n')
    parsing = parsing.split('],[')
    parsing = filter(None, parsing)
    item =[]
    if(len(parsing) > 0):
        for i in range(len(parsing)):
            parsingx = parsing[i].split(',')
            for j in range(len(parsingx)):
                parsingx[j] = parsingx[j].translate(None, '[](),')
            if(i_type == 'float'):  item.append([float(x) for x in parsingx])
            elif(i_type == 'bool'): item.append([str2bool(x) for x in parsingx])
            elif(i_type == 'int'):  item.append([int(x) for x in parsingx])
            else:                   item.append([x for x in parsingx])
        return item
    else:
        return [[]]    
   

def list3D(item, i_type='int'):
    ''' Parse string format into 3 dimensional array (values). '''
    parsing = item.translate(None, ' \n')
    parsing = parsing.split(']],[[')
    parsing_i_r = []
    for i in parsing:
        parsing_i = i.split('],[')
        parsing_j_r = []
        for j in parsing_i:
            parsing_j = j.split(',')
            parsing_k_r = []
            for k in parsing_j:
                clean_k = k.translate(None, '[] \n')
                if(i_type == 'float'):  parsing_k_r.append(float(clean_k))
                elif(i_type == 'bool'): parsing_k_r.append(str2bool(clean_k))
                elif(i_type == 'int'):  parsing_k_r.append(int(clean_k))
                else:                   parsing_k_r.append(clean_k)
            parsing_j_r.append(parsing_k_r)
        parsing_i_r.append(parsing_j_r)     
    return parsing_i_r
  
def str2bool(string):
    ''' Interpret a string to a boolean. '''
    if(string in ['True','true','1','y','Y']): return True
    else:                                      return False

def raw(string):
    ''' Returns a raw string representation of text. '''
    escape_dict={'\a':r'\a','\b':r'\b','\c':r'\c','\f':r'\f','\n':r'\n','\r':r'\r','\t':r'\t','\v':r'\v','\'':r'\'','\"':r'\"','\0':r'\0','\1':r'\1','\2':r'\2','\3':r'\3','\4':r'\4','\5':r'\5','\6':r'\6','\7':r'\7','\8':r'\8','\9':r'\9'}
    new_string=''
    for char in string:
        try: new_string+=escape_dict[char]
        except KeyError: new_string+=char
    return new_string 
    
def path_slashes(string):
    ''' Convert windows' backslashes or unix slashes to OS's type . '''    
    inter = raw(string).replace('\\', os.sep)   
    return raw(inter).replace('/', os.sep)

##################
# Configuration
##################
class Config:
    #config_name = 'pvc.cfg'
    
    def __init__(self,config_name):
        self.config = ConfigParser.ConfigParser(allow_no_value=True)        
        self.config.read(config_name)
        
        self.section = 'General'
        self.path_to_inpx             = path_slashes(self.parse('path_to_inpx', 'Path\to\Inpx',  c_type='string'))
        self.inpx_name                = self.parse('inpx_name',            '',        c_type='string')
        self.path_to_trafint          = self.parse('path_to_trafint',      '',        c_type='string')                 
        self.path_to_csv              = self.parse('path_to_csv',          '',        c_type='string')
        
        self.section = 'Video'
        self.path_to_sqlite           = self.parse('path_to_sqlite',       '',        c_type='string')
        self.path_to_image            = self.parse('path_to_image',        '',        c_type='string')
        self.image_name               = self.parse('image_name',           '',        c_type='string')
        self.pixel_to_unit_ratio      = self.parse('pixel_to_unit_ratio',  '',        c_type='string')
        self.fps                      = self.parse('fps',                  '30',      c_type='int')
                                                                                        
        self.section = 'Simulation'                                                              
        self.sim_steps                = self.parse('steps_per_sec',        '10',      c_type='int')      #10 recommended
        self.first_seed               = self.parse('first_seed',           '42',      c_type='int')  
        self.nbr_runs                 = self.parse('nbr_runs',             '10',      c_type='int')      #May eventually build up something to test this
        self.simulation_time          = self.parse('simulation_time',      '900',     c_type='int')
        self.warm_up_time             = self.parse('warm_up_time',         '120',     c_type='int')
        
        self.section = 'Sensitivity'
        self.nbr_points               = self.parse('nbr_points',           '5',       c_type='int')
        
        self.section = 'Statistical precision'
        self.desired_pct_error        = self.parse('desired_pct_error',    '20' ,     c_type='float')
        
        self.section = 'Calibration'
        self.output_forward_gaps      = self.parse('output_forward_gaps',      'True',   c_type='bool')
        self.output_lane_change       = self.parse('output_lane_change',       'False',  c_type='bool')
        self.NOMAD_solution_filename  = self.parse('NOMAD_solution_filename',  '',       c_type='string')
        self.ks_threshold             = self.parse('ks_threshold',             '0.3',    c_type='float')    #may want to check out that treshold
        self.ks_switch                = self.parse('reject_vissim_dist',       'False',  c_type='bool')
        
        self.section = 'Networks'
        self.active_network_1         = self.parse('active_network_1',     'False',  c_type='bool')       
        self.active_network_2         = self.parse('active_network_2',     'False',  c_type='bool')  
        self.active_network_3         = self.parse('active_network_3',     'False',  c_type='bool')  
        self.active_network_4         = self.parse('active_network_4',     'False',  c_type='bool')  

        self.section = 'Calibration paths (fullpath = complete paths)'
        self.path_to_NOMAD	         = self.parse('fullpath_to_NOMAD',         '',       c_type='string')
        self.path_to_NOMAD_param      = self.parse('fullpath_to_NOMAD_param',   '',       c_type='string')
        self.path_to_output_folder    = self.parse('path_of_output_folder',     '',       c_type='string')
        self.path_to_inpx_file_1      = self.parse('fullpath_to_inpx_file_1',   '',       c_type='string')
        self.path_to_inpx_file_2      = self.parse('fullpath_to_inpx_file_2',   '',       c_type='string')
        self.path_to_inpx_file_3      = self.parse('fullpath_to_inpx_file_3',   '',       c_type='string')
        self.path_to_inpx_file_4      = self.parse('fullpath_to_inpx_file_4',   '',       c_type='string')
        self.path_to_video_data_1     = self.parse('fullpath_to_video_data_1',  '',       c_type='string')
        self.path_to_video_data_2     = self.parse('fullpath_to_video_data_2',  '',       c_type='string')
        self.path_to_video_data_3     = self.parse('fullpath_to_video_data_3',  '',       c_type='string')
        self.path_to_video_data_4     = self.parse('fullpath_to_video_data_4',  '',       c_type='string')
        self.path_to_csv_net1         = self.parse('fullpath_to_csv_network_1', '',       c_type='string')
        self.path_to_csv_net2         = self.parse('fullpath_to_csv_network_2', '',       c_type='string')
        self.path_to_csv_net3         = self.parse('fullpath_to_csv_network_3', '',       c_type='string')
        self.path_to_csv_net4         = self.parse('fullpath_to_csv_network_4', '',       c_type='string')
        
        if(not os.path.isfile(config_name)):
            print('Notice: No default configuration found. Creating new ' + str(config_name))
            self.write()      

        
    def write(self,config_name):
        with open(config_name, 'w') as new_file:
            new_file.write('[Main]\n'
                           'path_to_inpx       = '+self.path_to_inpx+'\n'
                           'inpx_name          = '+self.inpx_name+'\n'
                           'path_to_trafint    = '+self.path_to_trafint+'\n'
                           '\n'
                           '[Video]\n'
                           'path_to_sqlite     = '+self.path_to_sqlite+'\n'
                           '\n'
                           '[Simulation]\n'
                           'sim_steps          = '+str(self.sim_steps)+'\n'
                           'first_seed         = '+str(self.first_seed)+'\n'
                           'nbr_runs           = '+str(self.nbr_runs)+'\n'
                           'simulation_time    = '+str(self.simulation_time)+'\n'
                           'warm_up_time       = '+str(self.warm_up_time)+'\n'
                           'nbr_points         = '+str(self.nbr_points)+'\n'
                           '\n'
                           '[Statistical precision]'
                           'desired_pct_error  = '+str(self.desired_pct_error)+'\n'
                           '\n'
                           )
        
    def parse(self, key, default, c_type='int', c_struct='simple'):
        ''' Handle configuration file values. '''
        if(not self.config.has_section(self.section)):    self.config.add_section(self.section)
        if(not self.config.has_option(self.section,key)): self.config.set(self.section,key,default)
        if(c_type == 'int'):
            if(c_struct == 'list1D'): return list1D(self.config.get(self.section, key))
            else:                     return self.config.getint(self.section, key)
        elif(c_type == 'float'):
            if(c_struct == 'list1D'): return list1D(self.config.get(self.section, key), i_type='float')
            else:                     return self.config.getfloat(self.section, key)
        elif(c_type == 'bool'):
            if(c_struct == 'list1D'): return list1D(self.config.get(self.section, key), i_type='bool')
            else:                     return self.config.getboolean(self.section, key)
        else:
            if(c_struct == 'list1D'): return list1D(self.config.get(self.section, key), i_type='string')
            else:                     return self.config.get(self.section, key)


##################
# Parse commands
##################
'''
def commands(parser, script_type = 'Sensi'):
    ## Trajectory extraction (Traffic Intelligence), off by default
    parser.add_option(      '--concat',         action='store_true',   dest='concat',         default=False,  help='[bool] Run concatenation functions')
    parser.add_option(      '--undistort',      action='store_true',   dest='undistort',      default=False,  help='[bool] Run undistortion functions')
    parser.add_option(      '--homo',           type='int',            dest='homo',           default=0,      help='[int]  Run homography functions with this many points')
    parser.add_option(      '--trafint',        action='store_true',   dest='trafint',        default=False,  help='[bool] Run trajectory extraction functions')
    parser.add_option(      '--trafint-watch',  action='store_true',   dest='trafint_watch',  default=False,  help='[bool] Watch trajectory extraction')
    
    if script_type == 'Sensi':
        ## Analysis, on by default
        parser.add_option('-c', '--cali',           action='store_true',   dest='calibration',    default=False,  help='[bool] Set the working analysis to "Calibration"               - off by default')
        parser.add_option('-d', '--student',        action='store_true',   dest='student',        default=False,  help='[bool] Set the working analysis to "Student t-test"            - off by default')
        parser.add_option('-o', '--monte-carlo',    action='store_true',   dest='montecarlo',     default=False,  help='[bool] Set the working analysis to "Sensitivity Monte Carlo"   - off by default')
        parser.add_option('-s', '--sensi',          action='store_true',   dest='sensitivity',    default=False,  help='[bool] Set the working analysis to "Sensitivity One at a time" - on  by default')    
        parser.add_option('-m', '--multi',          action='store_false',  dest='multi',          default=True,   help='[bool] Disables multiprocessing while running the analysis')
        parser.add_option('-u', '--multi_testing',  action='store_true',   dest='multi_test',     default=False,  help='[bool] Enables a debugging mode for multitesting. Prevents the end of the analysis but enables to read a clear traceback')
        parser.add_option('-f', '--file',                                  dest='file',                           help='[str]  Load specific inpx file')
        parser.add_option('-a', '--save-figures',   action='store_true',   dest='vis_save',       default=False,  help='[bool] Save figures')
        parser.add_option(      '--figure-format',                         dest='fig_format',     default='png',  help='[str]  Force saving images to a particular format. Enter a supported extensions (e.g. png, svg, pdf). Default is .png.')
        parser.add_option('-l', '--save-swp',       action='store_true',   dest='save_swp',       default=False,  help='[bool] Enables Vissim lane change (.swp) outputs')
        parser.add_option('-v', '--verbose',        action='store_true',   dest='verbose',        default=False,  help='[bool]  Level of detail of results')
        parser.add_option('-t', '--test',           action='store_true',   dest='mode',           default=False,  help='[bool]  Put the code into test mode, bypassing Vissim and generating random outputs')

    if script_type == 'Cali':
        parser.add_option('-p','--point', dest = 'start_point', default = None)
        #parser.add_option('-c', '--cali',           type = list,   dest='calibration',    default=False,  help='[bool] Set the working analysis to "Calibration"               - off by default')        
    
    if script_type == 'Video':
        parser.add_option('-a', '--analysis',                             dest='analysis',        default='',     help='[str] ')    
        parser.add_option('-i', '--image',         action='store_true',   dest='loadImage',       default=False,  help='[bool] ')    
        parser.add_option('-s', '--save',          action='store_true',   dest='save',            default=False,  help='[bool] ')    
        parser.add_option('-v', '--video',                                dest='video_name',      default=None,   help='[str] ')    
        parser.add_option('-g', '--fps',           type='int',            dest='fps',             default=30,     help='[int] ')    
        parser.add_option('-m', '--min',           type='int',            dest='min_time',        default=None,   help='[int] ')    
        parser.add_option('-M', '--max',           type='int',            dest='max_time',        default=None,   help='[int] ')    
            
    (commands, args) = parser.parse_args() 
        
    return commands
'''
def commands(parser, script_type):
    if script_type == 'Sensi':
        ## Analysis, on by default
        parser.add_argument('-a', '--analysis',       choices=['S','MC','OAT'],     dest='analysis',       default='OAT',  help='Choose from either S, MC or OAT.\n      S activates the Student analysis,\n      MC activates the Monte Carlo sensitivity analysis,\n      OAT activates the One-at-a-time sensitivity analysis') 
        parser.add_argument('-m', '--multi',          action='store_false',         dest='multi',          default=True,   help='Disables multiprocessing while running the analysis')
        parser.add_argument('-u', '--multi_testing',  action='store_true',          dest='multi_test',     default=False,  help='Enables a debugging mode for multitesting. Prevents the end of the analysis but enables to read a clear traceback when a process terminates')
        parser.add_argument('-f', '--inpx_file',                                    dest='file',                           help='[str]  Load specific inpx file')
        parser.add_argument('-s', '--save-figures',   action='store_true',          dest='vis_save',       default=False,  help='Save figures')
        parser.add_argument(      '--figure-format',                                dest='fig_format',     default='png',  help='[str]  Force saving images to a particular format. Enter a supported extensions (e.g. png, svg, pdf). Default is .png.')
        parser.add_argument('-l', '--save-swp',       action='store_true',          dest='save_swp',       default=False,  help='Enables Vissim lane change (.swp) outputs')
        parser.add_argument('-v', '--verbose',        action='store_true',          dest='verbose',        default=False,  help='Level of detail of results')
        parser.add_argument('-t', '--test',           action='store_true',          dest='mode',           default=False,  help='Put the code into test mode, bypassing Vissim and generating random outputs')

    if script_type == 'Cali':
        parser.add_argument('-p','--point',          type=float, nargs='*',         dest = 'start_point',   default = None,    help='list of float (integers will be converted) | make sure the number of floats entered correspond to the number of variables to be analysed')
    
    if script_type == 'Video':
        parser.add_argument('-a', '--analysis',      choices=['trace','process','diagnose'],   dest='analysis',        default='trace', help='Chosse between trace, diagnose, and process. To draw alignements onto a visualisation of the data, select trace. To identify vehicule trajectories with aberrant speeds or global wrong way trajectories, select diagnose. To assign vehicule trajectories to predefined alignements select process')
        parser.add_argument('-i', '--image',         action='store_true',           dest='loadImage',       default=False,   help='Trace option. Loads the trajectories onto the image specified in the calib.cfg file')    
        parser.add_argument('-s', '--save',          action='store_true',           dest='save',            default=False,   help='Trace option. Saves the alignement data into the csv file specified in the calib.cfg file ')    
        parser.add_argument('-v', '--video',         nargs='*',                     dest='video_names',                      help='[str] A list of video names - works for both Trace and Process modes')    
        parser.add_argument('-k', '--keep_align',    action='store_true',           dest='keep_align',      default=False,   help='Trace option. If activated, the alignements will be drawn for the first video and the result will be saved for all specified videos')        
        parser.add_argument('-g', '--fps',           type=int,                      dest='fps',             default=30,      help='Process option. Frame per second of the choosen video. Needed to only to trace accurate graphs and if different than 30')    
        parser.add_argument('-m', '--min',           type=int,                      dest='min_time',        default=None,    help='Process option. Choose if some of the early frames of the video is to be cut out. Number is in frames (conversions with fps has to be done before input) ')    
        parser.add_argument('-M', '--max',           type=int,                      dest='max_time',        default=None,    help='Process option. Choose if some of the late frames of the video is to be cut out. Number is in frames (conversions with fps has to be done before input)  ')
        parser.add_argument('-o', '--all_once',      action='store_false',          dest='video_all_once',  default=True,    help='Process option. If activated, all the specified videos will be processed all at once and concatenated in the same report and the same traj file as thoough it was a single video. Off by default.')        
        parser.add_argument('-d', '--dia_speed',     type=int,                      dest='maxSpeed',        default=130,     help='Diagnose option. Threshold to consider that a calculated vehicule speed is aberrant in km/h. This will convert the speed to pixel/frame so it needs the fps (-g) option to be set to the correct value.                                                                             Default is 130 km/h')        
    
    return parser.parse_args()