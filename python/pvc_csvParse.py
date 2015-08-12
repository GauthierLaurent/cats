# -*- coding: utf-8 -*-
"""
Created on Tue Mar 03 17:08:54 2015

@author: Laurent
"""
##################
# Import libraries
##################
## Native
from pylab import csv2rec
import StringIO, sys, os, traceback

##################
# Import Traffic Intelligence
##################
#disabling outputs
import nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import moving
sys.stdout = oldstdout #Re-enable output

##################
# Data storing classes
##################
class Alignments:
    '''built as a subclass of Videos - contains the raw x,y points to build
       an alignment using Traffic Intelligence'''
    def __init__(self,data):
        self.name       = data[0]
        self.point_list = data[1]

class Approach:
    def __init__(self,data):
        self.name      = data[0]
        self.direction = data[1]
        self.link_list = data[2]
        self.to_eval   = data[3]

class Corridor:
    def __init__(self,data):
        self.name      = data[0]
        self.direction = data[1]
        self.link_list = data[2]
        self.to_eval   = data[3]

class SpeedZones:
    def __init__(self,data):
        self.type       = data[0]
        self.vissim_num = data[1]
        self.speedDist  = data[1]
        
    def convertToVariable(self):
        return Variable(include = True, name = 'SpeedZone', vissim_name = self.type & self.vissim_num, desired_value = self.speedDist, value_type = 'C')
        
class Variable:
    def __init__(self, include = None, name = None, vissim_name = None, vissim_min = None, vissim_max = None, vissim_default = None, desired_min = None, desired_max = None, desired_value = None, value_type = 'R', point = None):
        self.include        = Variable.yesorTrue(include)
        self.name           = name
        self.vissim_name    = vissim_name
        self.vissim_default = Variable.floatOrBool(vissim_default)
        self.desired_min    = Variable.floatOrBool(desired_min)
        self.desired_max    = Variable.floatOrBool(desired_max)
        self.desired_value  = Variable.floatOrBool(desired_value)
        self.vissim_min     = Variable.floatOrNone(vissim_min)
        self.vissim_max     = Variable.floatOrNone(vissim_max)
        self.type           = Variable.defVarTypes(value_type)
        self.point          = Variable.floatOrNone(point)
        
    @staticmethod
    def defVarTypes(stringvalue):
        if stringvalue.lower() == 'r' or stringvalue.lower() == 'real':
            return 'R'
        if stringvalue.lower() == 'i' or stringvalue.lower() == 'int' or stringvalue.lower() == 'interger':
            return 'I'
        if stringvalue.lower() == 'bo' or stringvalue.lower() == 'bool' or stringvalue.lower() == 'boolean':
            return 'reject'
        if stringvalue.lower() == 'bi' or stringvalue.lower() == 'bin' or stringvalue.lower() == 'binary':
            return 'B'
        if stringvalue.lower() == 'c' or stringvalue.lower() == 'cat' or stringvalue.lower() == 'category':
            return 'C'
            
    @staticmethod
    def yesorTrue(stringvalue):
        if stringvalue != None:
            if stringvalue.lower() == 'yes' or stringvalue.lower() == 'true':
                return True
            if stringvalue.lower() == 'no' or stringvalue.lower() == 'flase':
                return False
        else:
            return None

    @staticmethod
    def floatOrBool(stringvalue):
        try:
            return float(stringvalue)
        except:
            if stringvalue != None:
                if stringvalue.lower() == 'false':
                    return False
                elif stringvalue.lower() == 'true':
                    return True
            else:
                return None

    @staticmethod
    def floatOrNone(stringvalue):
        try:
            return float(stringvalue)
        except:
            return None

class Videos:
    '''contains video information'''
    def __init__(self,name, aligns, ignore):
        self.video_name = name
        self.alignments = []
        for i in aligns:
            self.alignments.append(Alignments(i))
        self.to_ignore = ignore

##################
# CSV config file data extracting tools
##################
def extractAlignmentsfromCSV(dirname, inpxname):
    '''Reads alignment information for a csv named like the inpx
       CSV file must be build as:
       Video_name
       Alignment_name;point_list with point_list as: (x1,y1),(x2,y2),etc
    '''
    if inpxname in dirname: dirname = dirname.strip(inpxname)
    if os.path.exists(os.path.join(dirname, inpxname)):

        filename  = [f for f in os.listdir(dirname) if f == (inpxname.strip('.inpx') + '.csv')]
        f = open(os.path.join(dirname,filename[0]))
        for line in f:
            if '$Video_alignments' in line.strip(): break

        video_names = []
        ignore = []
        sublvl = []
        brute = []
        for line in f:
            if line.strip() == '':
                if sublvl != []: brute.append(sublvl)
                sublvl = []
            if '$' in line.strip():
                break
            if 'sqlite' in line:
                video_names.append(line.replace('\t','').strip().split('#')[0])
                if sublvl != []: brute.append(sublvl)
                sublvl = []
            if 'ignore' in line.lower():
                if len(ignore) < len(video_names) -1:
                    for add in xrange(len(video_names) -1 -len(ignore)):
                        ignore.append('')

                objects_to_ignore = []
                text_list = line.lower().strip().split('#')[0].strip().strip('ignore').strip(':').replace(';','-').replace(',','-').split('-')
                for text in text_list:
                    objects_to_ignore.append(int(text))
                ignore.append(objects_to_ignore)

            if 'sqlite' not in line and 'ignore' not in line.lower() and line.strip() != '':
                sublvl.append(line.strip().split('#')[0])

        if sublvl != []: brute.append(sublvl)
        if len(ignore) < len(video_names):
            for add in xrange(len(video_names) -len(ignore)):
                ignore.append('')

        videos = {}
        for vid in xrange(len(brute)):
            align_list = {}
            for b in xrange(len(brute[vid])):
                name = brute[vid][b].split(';')[0]
                inter = brute[vid][b].split(';')[1].replace(' ','')
                inter = [inter.replace(')','').replace('(','')]

                point = []
                while len(inter) > 0:
                    inter = inter[0].split(',',2)
                    point.append(moving.Point(float(inter[0]),float(inter[1])))
                    inter = inter[2:]
                align_list[b] = [name, point]
            videos[vid] = Videos(video_names[vid], align_list.values(), ignore[vid])

        return videos.values()
    else:
        print 'No vissim file named ' + str(inpxname) + ', closing program '
        sys.exit()

def extractDataFromVariablesCSV(filename):
    '''works inside convertParameterstoString'''
    variablesInfo = csv2rec(filename)
    vissimInclu = variablesInfo['includetoanalysis']
    vissimNames = variablesInfo['vissimname']
    vissimMinVa = variablesInfo['vissimmin']
    vissimMaxVa = variablesInfo['vissimmax']
    vissimDefau = variablesInfo['vissimdefault']
    value_names = variablesInfo['varname']
    value_type  = variablesInfo['valuetype']
    desiredMinV = variablesInfo['desiredmin']
    desiredMaxV = variablesInfo['desiredmax']
    desiredV    = variablesInfo['desiredvalue']

    return vissimInclu, vissimNames, vissimMinVa, vissimMaxVa, vissimDefau, value_names, value_type, desiredMinV, desiredMaxV, desiredV

def extractNumberList(dirname, inpxname):
    '''Reads a list of intergers for a csv.
       The list may be written on multiple lines and can be separated by
       either ';' ',' or '-'
    '''
    if inpxname in dirname: dirname = dirname.strip(inpxname)
    if os.path.exists(os.path.join(dirname, inpxname)):

        filename  = [f for f in os.listdir(dirname) if f == (inpxname.strip('.inpx') + '.csv')]
        f = open(os.path.join(dirname,filename[0]))
        for line in f:
            if '$Ignore-Objects' in line.strip(): break

        objects_to_ignore = []
        for line in f:
            if '$' in line.strip():
                break
            elif line.strip() == '' or line.startswith('#'):
                pass
            else:
                text_list = line.strip().split('#')[0].strip().replace(';','-').replace(',','-').split('-')
                for text in text_list:
                    objects_to_ignore.append(int(text))
        objects_to_ignore.sort()
        return objects_to_ignore
    else:
        print 'No vissim file named ' + str(inpxname) + ', closing program '
        sys.exit()

def extractParamFromCSV(dirname, filename):
    '''Reads variable information for a csv file
       CSV file must be build as:
             1rst  line:     $Variables
             2nt   line:     VarName,VissimMin,VissimMax,DesiredMin,DesiredMax,
                             VissimName
             other lines:    stringfloat,float,float,float,string,

             where:
                     VarName is a name given by the user and will be used to
                     write pcvtools reports
                     VissimName is the name of the variable found in the Vissim
                     COM manual
                     VissimMin and VissimMax are the min and max values found in
                     the Vissim COM manual
                     DesiredMin and DesiredMax are the range to be used for the
                     evaluation
    '''

    if filename in dirname: dirname = dirname.strip(filename)
    if os.path.exists(os.path.join(dirname, filename)) or os.path.exists(os.path.join(dirname,os.path.splitext(filename)[0] + '.csv')):

        files  = [f for f in os.listdir(dirname) if f == (os.path.splitext(filename)[0] + '.csv')]      #extension can be obtained as os.path.splitext(filename)[1]
        f = open(os.path.join(dirname,files[0]))
        for line in f:
            if '$Variables' in line.strip(): break

        brutestring = ''
        for line in f:
            if '$' in line.split('#')[0]: break
            if line.startswith('#') is False and line.strip() != '': brutestring += line.replace('\t', '').strip('\n').split('#')[0]+'\n'

        vissimInclu, vissimNames, vissimMinVa, vissimMaxVa, vissimDefau, value_names, value_type, desiredMinV, desiredMaxV, desiredV = extractDataFromVariablesCSV(StringIO.StringIO(brutestring.replace(" ", "")))

        parameters = {}
        for i in xrange(len(vissimNames)):
            parameters[i] = Variable(vissimInclu[i], value_names[i], vissimNames[i], vissimMinVa[i], vissimMaxVa[i], vissimDefau[i], desiredMinV[i], desiredMaxV[i], desiredV[i], value_type[i])

        parameters = verifyDesiredRanges(parameters.values())

        return parameters
    else:
        print 'No vissim file or csv file named ' + str(filename) + ' were found, closing program '
        sys.exit()

def extractCorridorsFromCSV(dirname, filename, structure_type = 'corridor', data_types = 'vissim'):
    '''Reads corridor or approach information for a csv named like the inpx
        - CSV file must be build as: Corridor_name,vissim list,traffic intelligence
          list
        - Both list must be separated by "-"
    '''

    if structure_type == 'corridor':
        struc_type = '$Corridors'
    if structure_type =='approach':
        struc_type = '$Approaches'

    if filename in dirname: dirname = dirname.strip(filename)
    if os.path.exists(os.path.join(dirname, filename)) or os.path.exists(os.path.join(dirname,os.path.splitext(filename)[0] + '.csv')):

        files  = [f for f in os.listdir(dirname) if f == (os.path.splitext(filename)[0] + '.csv')]      #extension can be obtained as os.path.splitext(filename)[1]
        f = open(os.path.join(dirname,files[0]))
        for line in f:
            if struc_type in line.strip(): break

        brute = []
        for line in f:
            if '$' in line.strip(): break
            if line.startswith('#') is False and line.strip() != '': brute.append(line.strip().replace(' ','\t').replace('\t','').split('#')[0])

        vissimCorridors = {}
        trafIntCorridors = {}
        for b in xrange(len(brute)):
            try:
                vissimCorridors[b] = Corridor([ brute[b].split(';')[0], brute[b].split(';')[1], [int(s) for s in brute[b].split(';')[2].split('-')], [int(s) for s in brute[b].split(';')[3].split('-')] ])
            except:
                pass
            
            try:
                trafIntCorridors[b] = Corridor([ brute[b].split(';')[0], brute[b].split(';')[1], [int(s) for s in brute[b].split(';')[4].split('-')], [int(s) for s in brute[b].split(';')[5].split('-')] ])
            except:
                pass

        if data_types == 'vissim':
            return vissimCorridors.values()
        if data_types == 'trafint':
            return trafIntCorridors.values()
    else:
        print 'No vissim file or csv file named ' + str(filename) + ' were found, closing program '
        sys.exit()

def extractSpeedZonesFromCSV(dirname, filename):
    '''Reads detector information for a csv named like the inpx
        - CSV file must be build as:
                ReductionZones_number,desired_speed         --> 1rst detector in vissim
                ReductionZones_number,desired_speed         --> 2nd detector in vissim
                ReductionZones_number,desired_speed         --> 3rd detector in vissim
                ...
    '''

    if filename in dirname: dirname = dirname.strip(filename)
    if os.path.exists(os.path.join(dirname, filename)) or os.path.exists(os.path.join(dirname,os.path.splitext(filename)[0] + '.csv')):

        files  = [f for f in os.listdir(dirname) if f == (os.path.splitext(filename)[0] + '.csv')]      #extension can be obtained as os.path.splitext(filename)[1]
        f = open(os.path.join(dirname,files[0]))
        for line in f:
            if '$Detectors' in line.strip(): break

        brute = []
        for line in f:
            if '$' in line.strip(): break
            if line.startswith('#') is False and line.strip() != '': brute.append(line.strip().replace(' ','\t').replace('\t','').split('#')[0])

        speedZones = {}
        for b in xrange(len(brute)):
            speedZones[b] = SpeedZones([brute[b].split(';')[0],brute[b].split(';')[1],brute[b].split(';')[2] ])

        return speedZones.values()

    else:
        print 'No vissim file or csv file named ' + str(filename) + ' were found, closing program '
        sys.exit()

def verifyDesiredRanges(variables):
    '''checks for coherence between bounds and desired min/max values entered
       in the csv file loaded to build the variables'''
    for i in xrange(len(variables)):
        if variables[i].vissim_min is not None:
            if variables[i].desired_min < variables[i].vissim_min:
                print str(variables[i].name) + ' was set to have a lower bound of ' + str(variables[i].vissim_min) + ' which is lower than the vissim minimum bound. Setting the lower bound to the vissim bound'
                variables[i].desired_min = variables[i].vissim_min

        if variables[i].vissim_max is not None:
            if variables[i].desired_max > variables[i].vissim_max:
                print str(variables[i].name) + ' was set to have a upper bound of ' + str(variables[i].vissim_max) + ' which is higher than the vissim maximum bound. Setting the upper bound to the vissim bound'
                variables[i].desired_max = variables[i].vissim_max
    return variables

def verifyDesiredPoints(variables):
    '''Checks if the point contained in variable.point respects the bounds of said
       variable'''
    chk = True
    for i in xrange(len(variables)):
        #print variables[i].name, variables[i].point, '|', variables[i].vissim_min, variables[i].vissim_max
        if variables[i].vissim_min is not None:
            if variables[i].point < variables[i].vissim_min:
                chk = False

        if variables[i].vissim_max is not None:
            if variables[i].point > variables[i].vissim_max:
                chk = False

    return chk

def writeAlignToCSV(dirname, inpxname, video_name, text_to_add):
    '''inserts the info for the video in the CSV file respecting, if applicable, the
       location of the $Video_alignments section and keeping, if applicable, other
       videos' informations'''
    def add_end(list_to_append, video_name, text_to_add):
        for i in xrange(len(text_to_add)):
            list_to_append += [str(i)+';']
            for j in xrange(len(text_to_add[i])):
                if j == len(text_to_add[i])-1:
                    list_to_append += [str(text_to_add[i][j])+'\n']
                else:
                    list_to_append += [str(text_to_add[i][j])+',']
        list_to_append += ['\n']
        return list_to_append

    if inpxname in dirname: dirname = dirname.strip(inpxname)
    if os.path.exists(os.path.join(dirname, os.path.splitext(inpxname)[0] + '.csv')):

        with open(os.path.join(dirname, os.path.splitext(inpxname)[0] + '.csv'), 'r+') as f:

            text_list = []

            for l in f:
                text_list.append(l)

            to_write_list = []

            for line in xrange(len(text_list)):
                if 'Video_alignments' in text_list[line]:
                    #$Video_alignments does exist, we must modify this section
                    section_list = []
                    for lines in xrange(line+1,len(text_list)):
                        if '$' in text_list[lines]:
                            last_line = lines
                            break
                        section_list.append(text_list[lines])

                    modified_section_list = []
                    index_list = []
                    found = False
                    for sec in xrange(len(section_list)):
                        if '.sqlite' in section_list[sec]:
                            index_list.append(sec)
                        if video_name in section_list[sec]:
                            found = sec

                    #no video of that name found
                    if found is False:
                        modified_section_list.append('$Video_alignments\n')
                        modified_section_list += section_list[:]
                        modified_section_list.append(str(video_name)+'\n')
                        modified_section_list = add_end(modified_section_list, video_name, text_to_add)

                    #name found, overwritting this section
                    else:
                        #adding the first part
                        modified_section_list.append('$Video_alignments\n')
                        modified_section_list += section_list[0:found]

                        #adding the values we are interested in
                        modified_section_list.append(str(video_name)+'\n')
                        modified_section_list = add_end(modified_section_list, video_name, text_to_add)

                        #adding the last part if it exists
                        if found < index_list[-1]:
                            modified_section_list += section_list[index_list[index_list.index(found)+1]:]

                    #making sure the section title is not followed by trailing empty lines
                    to_pop = []
                    for j in xrange(1,len(modified_section_list)):
                        if modified_section_list[j] != '\n':
                            break
                        else:
                            to_pop.append(j)
                    for p in reversed(to_pop):
                        modified_section_list.pop(p)

                    #correcting for removed section in-between empty line if the whole section was empty
                    if modified_section_list[-1] != '\n':
                        modified_section_list('\n')

                    #adding modified section and rest of the file
                    to_write_list += modified_section_list
                    to_write_list += text_list[last_line:]
                    break

                elif line == len(text_list) -1:
                    #No section $Video_alignments found, we must create it
                    to_write_list.append(text_list[line])
                    if text_list[line] != '\n':
                        if '\n' in text_list[line]:
                            to_write_list.append('\n')
                        else:
                            to_write_list.append('\n\n')
                    to_write_list.append('$Video_alignments\n')
                    to_write_list.append(str(video_name)+'\n')
                    to_write_list = add_end(to_write_list, video_name, text_to_add)

                else:
                    to_write_list.append(text_list[line])

        f.close()

        with open(os.path.join(dirname, inpxname.strip('.inpx') + '.csv'), 'w') as f:
              for i in to_write_list:
                  f.write(i)
        f.close()
    else:
        print 'CSV file not found in the specified location, please verify info entered in the pvc.cfg file'
