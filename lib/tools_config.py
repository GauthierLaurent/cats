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
        
        self.section = 'Sensitivity'
        self.path_to_inpx             = path_slashes(self.parse('path_to_inpx', 'Path\to\Inpx',  c_type='string'))
        self.inpx_name                = self.parse('inpx_name',            '',        c_type='string')
        self.path_to_trafint          = self.parse('path_to_trafint',      '',        c_type='string')                 
        self.path_to_csv              = self.parse('path_to_csv',          '',        c_type='string')
        
        self.section = 'Video'
        self.path_to_sqlite           = self.parse('path_to_sqlite',       '',        c_type='string')
                                                                                        
        self.section = 'Simulation'                                                              
        self.sim_steps                = self.parse('steps_per_sec',        '10',      c_type='int')      #10 recommended
        self.first_seed               = self.parse('first_seed',           '42',      c_type='int')  
        self.nbr_runs                 = self.parse('nbr_runs',             '10',      c_type='int')      #May eventually build up something to test this
        self.simulation_time          = self.parse('simulation_time',      '900',     c_type='int')
        self.warm_up_time             = self.parse('warm_up_time',         '120',     c_type='int')
        self.nbr_points               = self.parse('nbr_points',           '5',       c_type='int')
        self.wiedemann                = self.parse('wiedemann',            '99',      c_type='int')
        
        self.section = 'Statistical precision'
        self.desired_pct_error        = self.parse('desired_pct_error',    '20' ,     c_type='float')
        
        self.section = 'Calibration'
        self.output_forward_gaps      = self.parse('output_forward_gaps',  'True',   c_type='bool')
        self.output_lane_change       = self.parse('output_lane_change',   'False',  c_type='bool')

        self.section = 'Networks'
        self.active_network_1         = self.parse('active_network_1',     'False',  c_type='bool')       
        self.active_network_2         = self.parse('active_network_2',     'False',  c_type='bool')  
        self.active_network_3         = self.parse('active_network_3',     'False',  c_type='bool')  
        self.active_network_4         = self.parse('active_network_4',     'False',  c_type='bool')  

        self.section = 'Paths'
        self.path_to_calib_csv		  = self.parse('path_to_calib_csv',     '',       c_type='string')
        self.path_to_NOMAD			  = self.parse('path_to_NOMAD',         '',       c_type='string')
        self.path_to_NOMAD_param      = self.parse('path_to_NOMAD_param',   '',       c_type='string')
        self.path_to_output_folder    = self.parse('path_to_output_folder', '',       c_type='string')
        self.path_to_inpx_file_1      = self.parse('path_to_inpx_file_1',   '',       c_type='string')
        self.path_to_inpx_file_2      = self.parse('path_to_inpx_file_2',   '',       c_type='string')
        self.path_to_inpx_file_3      = self.parse('path_to_inpx_file_3',   '',       c_type='string')
        self.path_to_inpx_file_4      = self.parse('path_to_inpx_file_4',   '',       c_type='string')
        self.path_to_video_data_1     = self.parse('path_to_video_data_1',  '',       c_type='string')
        self.path_to_video_data_2     = self.parse('path_to_video_data_2',  '',       c_type='string')
        self.path_to_video_data_3     = self.parse('path_to_video_data_3',  '',       c_type='string')
        self.path_to_video_data_4     = self.parse('path_to_video_data_4',  '',       c_type='string')
        self.path_to_csv_net1         = self.parse('path_to_csv_network_1', '',       c_type='string')
        self.path_to_csv_net2         = self.parse('path_to_csv_network_2', '',       c_type='string')
        self.path_to_csv_net3         = self.parse('path_to_csv_network_3', '',       c_type='string')
        self.path_to_csv_net4         = self.parse('path_to_csv_network_4', '',       c_type='string')
        
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
def commands(parser):
    ## Trajectory extraction (Traffic Intelligence), off by default
    parser.add_option(      '--concat',         action='store_true',   dest='concat',         default=False,  help='[bool] Run concatenation functions')
    parser.add_option(      '--undistort',      action='store_true',   dest='undistort',      default=False,  help='[bool] Run undistortion functions')
    parser.add_option(      '--homo',           type='int',            dest='homo',           default=0,      help='[int]  Run homography functions with this many points')
    parser.add_option(      '--trafint',        action='store_true',   dest='trafint',        default=False,  help='[bool] Run trajectory extraction functions')
    parser.add_option(      '--trafint-watch',  action='store_true',   dest='trafint_watch',  default=False,  help='[bool] Watch trajectory extraction')
    
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
    (commands, args) = parser.parse_args() 

    return commands

