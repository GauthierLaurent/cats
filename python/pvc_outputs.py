# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 11:38:05 2014

@author: Laurent
"""
##################
# Import Libraries
##################
##natives
import os, sys, StringIO, copy, pandas, tempfile, subprocess
import numpy as np
import random, time
from contextlib import contextmanager

##internals
import pvc_mathTools as mathTools
import pvc_workers   as workers
import pvc_write     as write

##################
# Import Traffic Intelligence
##################
#disabling outputs
import nullwriter as nullwriter; oldstdout = sys.stdout;sys.stdout = nullwriter.NullWriter()
import storage
sys.stdout = oldstdout #Re-enable output

##################
# Data classes
##################
def dist(x):
    xx = np.array(x)
    nlist = np.unique(xx)
    l = float(len(x))
    if len(nlist)==len(x):
        stats = [1./l]*len(x)
    else:
        stats = [np.sum(xx==i)/l for i in nlist]
    cumul = np.cumsum(stats)
    return cumul,nlist

class Sublvl:
    def __init__(self, raw):
        if raw != []:
            cumul,nlist  = dist(raw)
            self.raw        = raw
            self.value      = nlist
            self.cumul      = cumul
        else:
            self.raw        = []
            self.value      = None
            self.cumul      = None
        self.computeStats()

    def addFileName(self,filename):
        self.filename = filename

    def getPercentile(self, percent):
        return np.percentile(self.raw, percent)

    def computeStats(self):
        if self.raw != []:
            self.mean       = np.mean(self.raw)
            self.firstQuart = self.getPercentile(25)
            self.median     = self.getPercentile(50)
            self.thirdQuart = self.getPercentile(75)
            self.var        = np.var(self.raw)
            self.std        = self.var**0.5
        else:
            self.mean       = None
            self.firstQuart = None
            self.median     = None
            self.thirdQuart = None
            self.var        = None
            self.std        = None

    def getStats(self):
        return self.mean, self.firstQuart, self.median, self.thirdQuart, self.var, self.std

class Stats:
    def __init__(self, raw):
        self.distributions  = []

        if raw != []:
            for l in raw:
                self.distributions.append(Sublvl(l))
            self.regen_cumul_all()
        else:
            self.cumul_all = Sublvl(raw)

    def addInfo(self,info):
        self.info = info

    def add_one_dist_list(self, raw):
        '''adds a raw data list to the distributions'''
        self.distributions.append(Sublvl(raw))
        self.regen_cumul_all()

    def add_many_dist_list(self, raw_list):
        '''needs a list of raw data list'''
        for raw in raw_list:
            self.distributions.append(Sublvl(raw))
        self.regen_cumul_all()

    def pop_dist_list(self, mylist):
        '''mylist must refer to the indexes of the list of distributions to pop'''
        if len(mylist) > 0:
            for i in reversed(sorted(mylist)):
                if len(self.distributions) > i:
                    self.distributions.pop(i)
            self.regen_cumul_all()

    def regen_cumul_all(self):
        '''recalculates the cumum_all distribution'''
        allvalues = []
        for dist in self.distributions:
            allvalues += list(dist.raw)
        self.cumul_all = Sublvl(allvalues)
        self.cumul_all.raw.sort()

    @classmethod
    def concat(cls, stats1, *stats):
        '''concanate all the distributions of the stats class variables into the first one'''
        for stat in stats:
            for dist in stat.distributions:
                stats1.add_one_dist_list(dist.raw)
                if hasattr(dist,'filename'):
                    stats1.distributions[-1].addFileName(dist.filename)

    def cleanStats(self, threshold):
        for d in xrange(len(self.distributions)):
            self.distributions[d] = Sublvl(makeitclean(self.distributions[d].raw, threshold))
        self.regen_cumul_all()

class SingleValueStats:
    def __init__(self,raw):
        self.raw = raw
        self.recalculate()

    def addOne(self,number):
        self.raw.append(number)
        self.raw.sort()
        self.recalculate()

    def addMany(self,mylist):
        for i in mylist:
            self.raw.append(i)
        self.raw.sort()
        self.recalculate()

    def popList(self,mylist):
        '''mylist must refer to the indexes of the numbers to pop'''
        if len(mylist) > 0:
            for i in reversed(sorted(mylist)):
                if len(self.raw) >= i:
                    self.raw.pop(i)
            self.recalculate()

    def recalculate(self):
        '''calculates usfull data'''
        if self.raw != []:
            self.mean = np.mean(self.raw)
            self.var = np.var(self.raw)
            self.std = np.std(self.raw)
        else:
            self.mean = 0
            self.var = 0
            self.std = 0

        self.count = len(self.raw)
        self.sum = sum(self.raw)
        self.raw.sort()

    @classmethod
    def concat(cls, stats1, *stats):
        '''concanate all the distributions of the stats class variables into the first one'''
        new_raw = []
        for stat in stats:
            new_raw += stat.raw
        stats1.addMany(new_raw)

class FileConstraint:
    def __init__(self):
        self.constraints = []
        self.names = []

    def addCi(self,ci,name):
        if name not in self.names:
            self.constraints.append(ci)
            self.names.append(name)
        else:
            self.constraints[self.names.index(name)] = ci

    def addFilename(self,filename):
        self.filename = filename

    def setDefaults(self, nameList,valueList):
        self.constraints = copy.deepcopy(valueList)
        self.names = nameList

    def setAll(self,nameList,valueList,ci,name,filename):
        self.setDefaults(nameList,valueList)
        self.addCi(ci,name)
        self.addFilename(filename)

class Constraints:
    def __init__(self):
        self.master = []
        self.files = []
        self.actives = ActiveConstraints()

    def getFilenames(self):
        return [f.filename for f in self.files]

    def addCi(self,name,value,filename):
        if name in self.actives.getActiveNames():
            if value is None:
                value = 0
            ci = self.actives.calculateConstraint(name, value)

            if filename in self.getFilenames():
                self.files[self.getFilenames().index(filename)].addCi(ci,name)
            else:
                self.files += [FileConstraint()]
                self.files[-1].setAll(self.actives.getActiveNames(),[-1* t for t in self.actives.getActiveThresholdList()],ci,name,filename)
            self.regenMaster()

    def regenMaster(self):
        if self.files == []:
            self.master = list(-1*np.asarray(self.actives.getActiveThresholdList()))
        else:
            array = [f.constraints for f in self.files]
            if isinstance(map(None, *array)[0],tuple):
                self.master = [max(row) for row in map(None, *array)]
            else:
                self.master = [row for row in map(None, *array)]

    def popOne(self, i):
        self.files.pop(i)
        self.regenMaster()

    def popMany(self, ilist):
        for i in reversed(ilist):
            self.popOne(i)

    @classmethod
    def concat(cls, const1, *consts):
        '''concanate all the distributions of the constraints class variables into the first one'''
        for const in consts:
            for FileConst in const.files:
                if FileConst not in const1.files:
                    const1.files.append(FileConst)
                    const1.regenMaster()
                else:
                    for ci in xrange(len(FileConst.constraints)):
                        name = FileConst.names[ci]
                        value = FileConst.constraints[ci]

                        const1.addCi(name, value, FileConst.filename)

class Derived_data:
    def __init__(self):
        self.flow       = SingleValueStats([])
        self.oppLCcount = SingleValueStats([])
        self.manLCcount = SingleValueStats([])
        self.forFMgap   = Stats([])
        self.oppLCagap  = Stats([])
        self.oppLCbgap  = Stats([])
        self.manLCagap  = Stats([])
        self.manLCbgap  = Stats([])
        self.forSpeeds  = Stats([])
        self.constraint = Constraints()
        self.travelTms  = [Stats([])]
        self.delay      = [Stats([])]

    def addLanes(self):
        self.flow.lane = []

    def addInfos(self, attr_name, info_list):
        if isinstance(getattr(self, attr_name),list):
            if isinstance(getattr(self, attr_name)[0],Stats):
                for i in xrange(len(info_list)):
                    getattr(self, attr_name)[i].addInfo(info_list[i])

    def editLaneCount(self, lane_num, count):
        if not hasattr(self.flow,'lane'):
            self.addLanes()

        if not isinstance(count, list):
            count = [count]

        if lane_num < len(self.flow.lane):
            self.flow.lane[lane_num] = SingleValueStats(count)
        else:
            pad = float('NaN')
            for l in xrange(len(self.flow.lane),lane_num-1):
                self.flow.lane.append(pad)
            self.flow.lane.append(SingleValueStats(count))

    def getLaneCounts(self):
        if hasattr(self.flow,'lane'):
            out = []
            for c in xrange(len(self.flow.lane)):
                if isinstance(self.flow.lane[c], SingleValueStats):
                    out.append(self.flow.lane[c].sum)
                else:
                    out.append(self.flow.lane[c])
            return out

    def getLanePercent(self):
        counts = np.asarray(self.getLaneCounts())
        return list(counts/float(sum(counts))*100)


    def addSingleOutput(self, attr_name, value, filename):
        '''adds the value and the filename to the attribute given'''
        if isinstance(getattr(self, attr_name),SingleValueStats):
            getattr(self, attr_name).addOne(value)

        if isinstance(getattr(self, attr_name),Stats):
            getattr(self, attr_name).add_one_dist_list(value)
            getattr(getattr(self, attr_name),'distributions')[-1].addFileName(filename)

        if isinstance(getattr(self, attr_name),list):
            if isinstance(getattr(self, attr_name)[0],Stats):
                if len(getattr(self, attr_name)) < len(value):
                    for i in xrange(len(value) - len(getattr(self, attr_name))):
                        getattr(self, attr_name).append(Stats([]))
                for j in xrange(len(value)):
                    getattr(self, attr_name)[j].add_one_dist_list(value[j])
                    getattr(getattr(self, attr_name)[j],'distributions')[-1].addFileName(filename)

    def addConstraintValue(self, constraintName, value, filename):
        self.constraint.addCi(constraintName, value, filename)

    def addManyOutputs(self, output_list):
        '''calls addSingleOutput() for each output in output_list
           output_list = [attr_name, value, filename]'''
        for output in output_list:
            self.addSingleOutput(self, output[0], output[1], output[2])

    def popSingleOutputList(self, attr_name, index_list):
        if isinstance(getattr(self, attr_name),SingleValueStats):
            getattr(self, attr_name).popList(index_list)

        if isinstance(getattr(self, attr_name),Stats):
            getattr(self, attr_name).pop_dist_list(index_list)

        if isinstance(getattr(self, attr_name),Constraints):
            getattr(self, attr_name).popMany(index_list)

        if isinstance(getattr(self, attr_name),list):
            if isinstance(getattr(self, attr_name)[0],Stats):
                getattr(self, attr_name)[0].popMany(index_list)

    def popManyOutputList(self, output_list, index_list):
        '''calls popSingleOutputList() for each output in output_list
           output_list = [attr_name, index_list]'''
        for output in output_list:
            self.popSingleOutputList(output, index_list)

    def getConstraints(self):
        return self.constraint.master

    def getActiveConstraintNames(self):
        return self.constraint.actives.getActiveNames()

    def getConstraintsForFile(self,filename):
        return self.constraint.files[self.constraint.getFilenames().index(filename)].constraints

    def testConstraints(self):
        tmp = self.getConstraints()
        for f in tmp:
            if f > 0:
                return 'Unfeasible'
            else:
                pass
        return 'Feasible'

    def getFilenames(self):
            filenames = []
            for attr in [attr for attr in dir(self) if callable(attr) is False and '__' not in attr and 'get' not in attr and 'add' not in attr and 'edit' not in attr]:
                if isinstance(getattr(self, attr),Stats):
                    try:
                        filenames += [getattr(f,'filename') for f in getattr(self, attr).distributions if getattr(f,'filename') not in filenames]
                    except:
                        pass
            return filenames

    @classmethod
    def concat(cls, outputs1, outputs2):
        for attr in [attr for attr in dir(outputs2) if callable(attr) is False and '__' not in attr and 'Get' not in attr and 'add' not in attr]:

            if isinstance(getattr(outputs2, attr),SingleValueStats):
                SingleValueStats.concat(getattr(outputs1,attr),getattr(outputs2,attr))

            if isinstance(getattr(outputs2, attr),Stats):
                Stats.concat(getattr(outputs1,attr),getattr(outputs2,attr))

            if isinstance(getattr(outputs2, attr),Constraints):
                Constraints.concat(getattr(outputs1,attr),getattr(outputs2,attr))

            if isinstance(getattr(outputs2, attr),list):
                if isinstance(getattr(outputs2, attr)[0],Stats):

                    if hasattr(getattr(outputs2, attr)[0],'info'):
                        values1 = [getattr(outputs1, attr)[a].infos for a in xrange(len(getattr(outputs1, attr)))]

                        for j in xrange(len(getattr(outputs2, attr))):
                            if getattr(outputs2,attr)[j].info in values1:
                                Stats.concat(getattr(outputs1,attr)[values1.index(getattr(outputs2,attr)[j].info)], getattr(outputs2,attr)[j])
                            else:
                                getattr(outputs1,attr).append(getattr(outputs2,attr)[j])

                    else:
                        for j in xrange(len(getattr(outputs2, attr))):
                            Stats.concat(getattr(outputs1,attr)[j],getattr(outputs2,attr)[j])

        if hasattr(outputs2.flow,'lane'):
                if hasattr(outputs1.flow,'lane'):
                    concat_lanes = mathTools.addLists(outputs2.flow.lane, outputs2.flow.lane)
                    for c in xrange(len(concat_lanes)):
                        outputs1.editLaneCount(c, concat_lanes[c])
                else:
                    for c in xrange(len(outputs2.flow.lane)):
                        outputs1.editLaneCount(c, outputs2.flow.lane[c])

    def activateConstraints(self,config):
        self.constraint.actives.activate(config)
        self.constraint.regenMaster()

##################
### Constraints
##################
class ActiveConstraints:

    def __init__(self, config = None):
        self.numActive = 0
        self.activeList = []
        self.tresholdList = []
        self.typeList = []
        self.nameList = []

        if config is not None:
            self.activate(config)

    def activate(self,config):
        self.activeList.append(config.collis_constraint[0])
        self.activeList.append(config.nonGen_constraint[0])
        self.activeList.append(config.decelp_constraint[0])
        self.activeList.append(config.accel0_constraint[0])
        self.activeList.append(config.diFlow_constraint[0])

        self.tresholdList.append(config.collis_constraint[1])
        self.tresholdList.append(config.nonGen_constraint[1])
        self.tresholdList.append(config.decelp_constraint[1])
        self.tresholdList.append(config.accel0_constraint[1])
        self.tresholdList.append(config.diFlow_constraint[1])

        self.typeList.append(config.collis_constraint[2])
        self.typeList.append(config.nonGen_constraint[2])
        self.typeList.append(config.decelp_constraint[2])
        self.typeList.append(config.accel0_constraint[2])
        self.typeList.append(config.diFlow_constraint[2])

        self.nameList.append('collisions')
        self.nameList.append('nonGen')
        self.nameList.append('deceleration')
        self.nameList.append('acceleration')
        self.nameList.append('flowPasses')

        for i in xrange(len(config.saturation_values)):
            self.activeList.append(config.saturation_values[i][0])
            self.tresholdList.append(config.saturation_values[i][2])
            self.typeList.append(config.saturation_values[i][3])
            self.nameList.append('saturation_'+str(i))

    def getActiveNames(self):
        return [self.nameList[i] for i in xrange(len(self.nameList)) if self.activeList[i]]

    def getThresholdList(self):
        return self.tresholdList

    def getActiveThresholdList(self):
        return [self.tresholdList[i] for i in xrange(len(self.tresholdList)) if self.activeList[i]]

    def getInfoByName(self,name,key = None):
        '''If key is provided, returns the value of constraint "name" for the
           specific sublist "key".
           Otherwise, returns a list of the values of each sublist for "name"'''
        if key is None:
            return [self.activeList[self.nameList.index(name)], self.tresholdList[self.nameList.index(name)], self.typeList[self.nameList.index(name)]]

        else:
            return getattr(self, key)[self.nameList.index(name)]

    def calculateConstraint(self, name, value):
        '''converts num, dp and a0 errors into constraint values'''
        if name in self.nameList:
            if name == 'flowPasses':
                return value
                #TODO
            elif 'saturation' in name:
                return calculateflowPassesConstraint(value, self.tresholdList[self.nameList.index(name)], 10)
            else:
                return value - self.tresholdList[self.nameList.index(name)]

    @staticmethod
    def getConstraintsTypes(config):
        tmp = ActiveConstraints(config)
        return tmp.typeList

    @staticmethod
    def getActiveConstraintsTypes(config):
        tmp = ActiveConstraints(config)
        return [tmp.typeList[i] for i in xrange(len(tmp.typeList)) if tmp.activeList[i]]

    @staticmethod
    def getNumberOfConstraints(config):
        tmp = ActiveConstraints(config)
        return len([i for i in tmp.activeList if i is True])

class Queue:
    def __init__(self):
        self.time = []
        self.Stopedveh = []
        self.longestQueue = 0
        self.timeOfLonguestQueue = 0

    def calculateMaxQueue(self):
        for q in xrange(len(self.StopedVeh)):
            if len(self.StopedVeh[q]) > self.longestQueue:
                self.longestQueue = self.StopedVeh[q]
                self.timeOfLonguestQueue = self.time[q]

    def addVehicule(self,time,vehNbr):
        if time not in self.time:
            self.time.append(time)
            self.Stopedveh.append([vehNbr])
            self.time, self.Stopedveh = mathTools.sort2lists(self.time,self.Stopedveh)

        else:
            self.Stopedveh[self.time.index(time)].append(vehNbr)
        self.calculateMaxQueue()

class ApproachQueue:
    def __init__(self):
        self.laneQueues = []
        self.laneNames  = []
        self.longestQueue = 0
        self.timeOfLonguestQueue = 0

    def getMaxQueueForSingleLane(self,laneName):
        return self.laneQueues[self.laneNames.index(laneName)].longestQueue

    def getTimeOfMaxQueueForSingleLane(self,laneName):
        return self.laneQueues[self.laneNames.index(laneName)].timeOfLonguestQueue

    def calculateApproachMaxQueue(self):
        for laneName in self.laneNames:
            if self.getMaxQueueForSingleLane(laneName) > self.longestQueue:
                self.longestQueue = self.getMaxQueueForSingleLane(laneName)
                self.timeOfLonguestQueue = self.getTimeOfMaxQueueForSingleLane(laneName)

    def addVehicule(self,time,vehNbr,laneName):
        if laneName in self.laneNames:
            self.laneQueues[self.laneNames.index(laneName)].addVehicule(time,vehNbr)
        else:
            self.laneNames.append(laneName)
            self.laneQueues.append(Queue())
            self.laneQueues[-1].addVehicule(time,vehNbr)
            self.laneNames, self.laneQueues = mathTools.sort2lists(self.laneNames,self.laneQueues)

        self.calculateApproachMaxQueue()

def smartCountCollisionsVissim(dirname, filename, maxLines, lanes = None, collisionTimeDifference = 0.2):
    '''Splits the fzp in smaller fzp files to prevent overflow errors when invoking
       moving.countCollisionsVissim

       If the default number of lines provided by maxLines results in a MemoryError,
       the function will automatically reduce the number of lines until it reaches a
       point were it works

       The act of cutting the file skew the exact count of the number of collisions
       and the result should not be used for a PB or PEB calibration constraint
    '''
    #check for lenght
    temp_file_lines = []
    header = []
    with open(os.path.join(dirname,filename),'r') as fzp:
        for line in fzp:
            if line.startswith('$'):
                header += line
            else:
                temp_file_lines += line

    nCollisions = 0
    #the while loop is used because for some files, the designated default lines is still too high
    test_again = True
    while test_again is True:

        #creating temp fzp files
        chunks = workers.cleanChunks(maxLines, temp_file_lines)
        for c in xrange(len(chunks)):
            tmp = ''
            for line in header:
                tmp += line
            for line in chunks[c]:
                tmp += line

            try:
                nCollisions +=  storage.countCollisionsVissim(StringIO.StringIO(tmp), lanes = lanes, collisionTimeDifference = 0.2, lowMemory = False)
                test_again = False
            except:
                if maxLines > 400000:
                    maxLines += - 200000
                    test_again = True
                else:
                    return

    return nCollisions

def saturationFlowDistribution(objects, s, lane, centile, max_tiv, min_nb_tiv, simSecPerTimeUnit):
    '''calculates the maximum flow (85th percentile) for each flow peak on a given lane

       returns a list of the peaks - list is empty if no tiv under the min tiv is detected'''

    gaps, speeds = forwardGaps(objects, s, lane)

    saturation_flow = []
    #spliting TIV in sublists, if gaps are below a certain gap threshold, they are considered
    #part of the same group and are given a incremental value given by an interger contained in
    #"counter". Otherwise, they are labels as -1 (a dead zone in terms of vehicular flow):
    #
    #       caract_gaps = [1,1,1,1,-1,-1,-1,-1,2,2,2,-1,-1,-1,-1,3,3,3,3,3,3,3,...]
    #
    caract_gaps = []
    counter = 0
    for gap in gaps:
        if gap > max_tiv*simSecPerTimeUnit:
            caract_gaps.append(-1)
            counter += 1
        else:
            caract_gaps.append(counter)

    #For each of those sublists that have a lenght greater than min_nb_tiv, we calculate
    #the saturation flow by taking the inverse of the mean of every gaps that are below the
    #15th percentile
    for num in np.unique(caract_gaps):
        if num != -1:
            num_gaps = np.asarray(gaps)[np.asarray(caract_gaps) == num]/simSecPerTimeUnit

            if len(num_gaps) >= min_nb_tiv:
                saturation_flow.append(1/np.percentile(num_gaps, centile)*3600)

    return saturation_flow

def saturationFlow(objects, s, lane, centile, max_tiv, min_nb_tiv, simSecPerTimeUnit):
    tiv_list = saturationFlowDistribution(objects, s, lane, centile, max_tiv, min_nb_tiv, simSecPerTimeUnit)
    if len(tiv_list) > 0:
        return max(tiv_list)
    else:
        return 0

def compareSimAndInputFlows(linkDict, VehiculeInputs, acceptable_error):
    value_list = []
    target_list = []

    for i in xrange(len(VehiculeInputs)):
        if int(VehiculeInputs[i].link) in linkDict.keys():
            value_list.append(linkDict[int(VehiculeInputs[i].link)])
        else:
            value_list.append(0)
        target_list.append(VehiculeInputs[i].vehInput)

    return calculateAllflowConstraint(value_list, target_list, acceptable_error)

def calculateflowPassesConstraint(value, target, acceptable_error):
    '''checks if a single flow point is reached'''
    if value in [target*(1-float(acceptable_error)/100), target*(1+float(acceptable_error)/100)]:
        return 0
    else:
        return (abs(target-value)- target*float(acceptable_error)/100)/target #relative error

def calculateAllflowConstraint(value_list, target_list, acceptable_error):
    C = 0
    for i in xrange(len(value_list)):
        value = calculateflowPassesConstraint(value_list[i], target_list[i], acceptable_error)
        if value > C:
            C = copy.deepcopy(value)
    return C

def calculate_jam_constraint(objects, threshold):
    '''From the fzp, calculates if a jam occurs'''
    jam = 0
    for o in objects:
        boolarray = np.asarray(o.curvilinearVelocities.getXCoordinates()) == 0
        nbr_zeros = np.count_nonzero(boolarray)
        if nbr_zeros > threshold:
            jam += 1
    return jam

def read_error_file(dirname,filename):
    '''reads an error file and returns the number of
            deceleration is positive errors
            accelaration is zero errors
            the total number of vehicules that could not be generated
    '''
    case_dp = 0     #deceleration is positive
    case_a0 = 0     #acceleration is zero
    num = 0         #number of vehicles to generate
    with open(os.path.join(dirname,filename),'r') as err:
        for line in err:

            if 'The expected trajectory of vehicle' in line and 'cannot be determined' in line:
                if 'expected deceleration is positive' in line:
                    case_dp += 1
                if 'expected acceleration is zero' in line:
                    case_a0 += 1

            if 'Vehicle input' in line and 'could not be finished completely' in line:
                num += float(line.strip().split('remain: ')[-1].split(' ')[0])

    return num, case_dp, case_a0

def search_folder_for_error_files(dirname, fzpname = None):
    '''search a directory and returns the mean value, for every fzp files, of
            deceleration is positive errors
            accelaration is zero errors
            the total number of vehicules that could not be generated
    '''
    filenames = [f for f in os.listdir(dirname) if f.endswith('err')]
    fzp_files = [f for f in os.listdir(dirname) if f.endswith('fzp')]

    if len(fzp_files) > 0:
        num_list = []; dp_list = []; a0_list = []
        for filename in filenames:
            num, dp, a0 = read_error_file(dirname,filename)
            num_list.append(num); dp_list.append(dp); a0_list.append(a0)

        if len(filenames) < len(fzp_files):
            for i in xrange(len(fzp_files)-len(filenames)):
                num_list.append(0); dp_list.append(0); a0_list.append(0)

        return max(num_list), max(dp_list), max(a0_list)
    else:
        return float('nan'), float('nan'), float('nan')

def makeitclean(video_forward_gaps, threshold):
    for g in reversed(range(len(video_forward_gaps))):
        if video_forward_gaps[g] < threshold:
            video_forward_gaps.pop(g)
    return video_forward_gaps

def buildFout(config, dStat_forgaps, dStat_oppLCgaps, dStat_manLCgaps, ttms):
    '''returns a single value from the list of possible outputs'''
    lists = []
    #add car-following gaps
    if config.output_forward_gaps and config.cmp_for_gaps:
        lists.append(dStat_forgaps)

    #add lane change information
    if config.output_lane_change_gaps:
        if config.cmp_man_lcgaps:
            lists.append(dStat_manLCgaps)
        if config.cmp_opp_lcgaps:
            lists.append(dStat_oppLCgaps)

    if config.output_travel_times:
        lists.append(ttms)

    if 'DNE' in lists:
        return 'inf'
    else:
        return max(lists)

def sort_fout_and_const(fout_lists):
    '''sort many outputs f1, f2, f3, etc. to keep the worst one
       if all fi respect the constraints, then fi are sorted to give worst fout
       if not all fi respect constraint, the first one to not respect it is returned
    '''

    valids = []
    #check constraints:
    for l in fout_lists:
        if np.all(np.asarray(l[1:]) <= 0):      #all constraints are <= 0
            valids.append(fout_lists.index(l))

    #sort valids
    if len(valids) == len(fout_lists) and len(valids) > 0:
        to_conserve = fout_lists[valids[0]]
        for i in valids:
            if fout_lists[i][0] > to_conserve[0]:
                to_conserve = fout_lists[i]

        return to_conserve
    else:
        for i in xrange(len(fout_lists)):
            if i not in valids:
                return fout_lists[i]  #constains [fout, C_0, C_1, ...]

##################
# Output treatment tools
##################
def calculateInstants(objects, s, lane):
    instants = []
    speeds = []
    for o in objects:
        t = o.curvilinearPositions.getIntersections(s, lane)
        if t != []:
            instants.append(o.getFirstInstant()+t[0])
            speeds.append(o.curvilinearVelocities.getXCoordinates()[int(np.floor(t[0]))])
    instants.sort()
    return instants, speeds

def calculateGaps(sorted_instants):
    x = np.asarray(sorted_instants)
    return list(x[1:]-x[:-1])

def forwardGaps(objects, s, lane):
    '''Calculates all gaps on a given lane and for a given point s'''

    instants, speeds = calculateInstants(objects, s, lane)
    gaps = calculateGaps(instants)
    #for g in reversed(xrange(len(gaps))):
    #    if gaps[g] >= 30:
    #        gaps.pop(g)
    return gaps, speeds

def laneChangeGaps(listDict, laneDict, objects):
    '''Determines the width of lane change gaps for a list of objects who make
       lane changes
        - agaps represent the gap present after the insertion of the lane
          changing vehicule
        - bgaps reprensent the gap present before the insertion of the lane
          changing vehicule'''

    x = []  #agaps construction variable
    y = []  #bgaps construction variable
    for obj in listDict.keys():

        for change in range(len(listDict[obj])):
            lane = listDict[obj][change][2]                                                     #Dict[i][1] = lane after lane change
            stepNum = listDict[obj][change][4]                                                  #Dict[i][2] = time of the lane change
            s = objects[obj].curvilinearPositions.getXCoordinates()[listDict[obj][change][3]]

            #determining the gap
            instants = []
            for candidate in laneDict[lane]:
                if candidate != obj:
                    t = objects[candidate].curvilinearPositions.getIntersections(s, lane)
                    if t != []:
                        #if objects[candidate].getFirstInstant()+t[0] > stepNum:
                        instants.append(objects[candidate].getFirstInstant()+t[0] - stepNum)

            instants.sort()
            if instants != []:
                for i in range(len(instants)):
                    if instants[i] > 0:
                        x.append(instants[i])
                        y.append(instants[i] - instants[i -1])

                        break

    agaps = np.asarray(x)
    bgaps = np.asarray(y)

    return agaps, bgaps

def appendDicts(candidate, dictionnary, vissim_number, lane_before, lane_after, trajectory_pos, exact_time, position):
    '''adds {candidate: position_before, position_after, frame_after} to dictionnary'''
    if candidate not in dictionnary:
        dictionnary[candidate] = [[vissim_number,lane_before,lane_after,trajectory_pos,exact_time,position]]
    else:
        dictionnary[candidate].append([vissim_number,lane_before,lane_after,trajectory_pos,exact_time,position])

    return dictionnary

def start_is_same_corridor_as_end(single_object, corridors, data_type):
    '''checks data to determine if the start corridor  is the same as the end corridor'''
    first_appeareance = None
    last_appeareance = None
    for i in xrange(len(corridors)):
        if data_type == 'vissim':
            if int(single_object.curvilinearPositions.lanes[0].split('_')[0]) in corridors[i].link_list: first_appeareance = i
            if int(single_object.curvilinearPositions.lanes[-1].split('_')[0]) in corridors[i].link_list: last_appeareance = i
        else:
            if int(single_object.curvilinearPositions.lanes[0]) in corridors[i].link_list: first_appeareance = i
            if int(single_object.curvilinearPositions.lanes[-1]) in corridors[i].link_list: last_appeareance = i
    return first_appeareance == last_appeareance

def find_all_LC(single_object, to_eval, link_corr_dict, data_type):
    '''iterates over the lanes taken by an object and checks for lane changes

       for vissim, it is considered that a link change is not a lane change

       returns a list of observed changes perr corridor (list of list):
           [corridor{0}_LC_list, corridor{1}_LC_list, ...]

           with corridor{i}_LC_list = [LC{0}, LC{1}, ...]

           and LC{i} the occuring position in o.curvilinearPositions.lanes
    '''

    LC_positions = []
    LC_on_this_corr = []

    current_corr = None
    #itterating over lanes
    for i in (xrange(len(single_object.curvilinearPositions.lanes)-1)):

        if data_type == 'vissim':
            O_lane = int(single_object.curvilinearPositions.lanes[i].split('_')[1])
            D_lane = int(single_object.curvilinearPositions.lanes[i+1].split('_')[1])
            O_link = int(single_object.curvilinearPositions.lanes[i].split('_')[0])
        else:
            O_lane = int(single_object.curvilinearPositions.lanes[i])
            D_lane = int(single_object.curvilinearPositions.lanes[i+1])
            O_link = int(single_object.curvilinearPositions.lanes[i])

        if data_type == 'vissim':
            if int(single_object.curvilinearPositions.lanes[i].split('_')[0]) != int(single_object.curvilinearPositions.lanes[i+1].split('_')[0]):
                continue

        #keeping only LC which origine is in an evaluated link
        if int(O_link) in to_eval:
            #if current_link is None, we never yet saw a valid point. Thus, we need to set the current working corridor the the present corridor
            if current_corr is None:
                current_corr = link_corr_dict[O_link]

            #if we observe a lane change:
            if O_lane != D_lane:

                #if the corridor of the observed point is the same as the current working corridor
                if current_corr == link_corr_dict[O_link]:
                    #simple append
                    LC_on_this_corr.append(i)
                #otherwise, we start a new working list for the new corridor, first appending the old corridor to the global list
                else:
                    LC_positions.append(LC_on_this_corr)
                    LC_on_this_corr = [i]
                    current_corr = link_corr_dict[O_link]
    #end of the loop: adding the last corridor we worked on
    LC_positions.append(LC_on_this_corr)

    return LC_positions

def LC_is_toward_exit(lane1,lane2,exits):
    '''checks if a LC is in the same direction as the exit direction given for the corridor'''
    if int(lane2) > int(lane1):
        turn = 'g'
    else:
        turn = 'r'
    return turn == exits

def caractLC(previous, lane1, lane2, exits):
    '''finds if a LC is considered opportunist ('opp') or mandatory ('man')

       only for case: start corridor != end corridor'''
    if LC_is_toward_exit(lane1,lane2,exits):
        #if the LC is the last LC of the corridor, and finishes at the rightmost,
        #it is set as 'man', if it finisheds in lans > 1, then 'opp'
        #  --> the last one of the last corridor is actually undefined if on lane 1,
        #      but will be set as 'man' since the case of never changing
        #      corridor is already adressed by the first 'if'
        if previous == None:
            if int(lane2) > 1:
                return 'opp'
            else:
                return 'man'
        else:
            #if it is not the first, it depends on the last observed LC
            if previous == 'man':
                return 'man'
            else:
                return 'opp'
    else:
        return 'opp'

def calculate_laneChange(objects, corridors, data_type):
    '''Sorts mandatory and opportunistic lane changes'''
    #Dictionaries
    oppObjDict = {}
    manObjDict = {}
    link_exits = {}
    link_corr  = {}
    laneDict = {}

    to_eval = []
    for j in xrange(len(corridors)):
        to_eval += corridors[j].to_eval
        for l in corridors[j].to_eval:
            if l not in link_exits:
                link_exits[l] = corridors[j].direction
            if l not in link_corr:
                link_corr[l] = j

    for o in objects:

        #building the lane dictionnary
        for i in set(o.curvilinearPositions.lanes):
            if i not in laneDict: laneDict[i] = []
            if objects.index(o) not in laneDict[i]: laneDict[i].append(objects.index(o))

        #getting all lane changes in the trajectory
        LC_positions = find_all_LC(o, to_eval, link_corr, data_type)
        LC_type_list = []
        #if there is at least one LC
        if len(mathTools.intoList([],LC_positions)) > 0:
            #checking if all the trajectory is in the same corridor
            if start_is_same_corridor_as_end(o, corridors, data_type):
                #all turns are added as 'opp'
                for co in reversed(xrange(len(LC_positions))):
                    for i in reversed(LC_positions[co]):
                        oppObjDict = appendDicts(objects.index(o), oppObjDict, o.getNum(), o.curvilinearPositions.lanes[i], o.curvilinearPositions.lanes[i+1], i+1, i+1+o.getFirstInstant(), o.curvilinearPositions.getXCoordinates()[i+1])
            else:
                for co in reversed(xrange(len(LC_positions))):
                    for i in reversed(LC_positions[co]):
                        if data_type == 'vissim':
                            lane1 = o.curvilinearPositions.lanes[i].split('_')[1]
                            lane2 = o.curvilinearPositions.lanes[i+1].split('_')[1]
                            exits = link_exits[int(o.curvilinearPositions.lanes[i].split('_')[0])]
                        else:
                            lane1 = o.curvilinearPositions.lanes[i]
                            lane2 = o.curvilinearPositions.lanes[i+1]
                            exits = link_exits[int(o.curvilinearPositions.lanes[i])]

                        if LC_positions[co].index(i) == len(LC_positions[co])-1:
                            previous = None
                        else:
                            previous = LC_type_list[-1]

                        LC_type = caractLC(previous, lane1, lane2, exits)
                        LC_type_list.append(LC_type)

                        if LC_type == 'opp':
                            oppObjDict = appendDicts(objects.index(o), oppObjDict, o.getNum(), o.curvilinearPositions.lanes[i], o.curvilinearPositions.lanes[i+1], i+1, i+1+o.getFirstInstant(), o.curvilinearPositions.getXCoordinates()[i+1])
                        else:
                            manObjDict = appendDicts(objects.index(o), manObjDict, o.getNum(), o.curvilinearPositions.lanes[i], o.curvilinearPositions.lanes[i+1], i+1, i+1+o.getFirstInstant(), o.curvilinearPositions.getXCoordinates()[i+1])

    return laneDict, oppObjDict, manObjDict

def laneChange(objects, corridors):
    '''classifies the lane changes between vissim and video data then passes to the calculating function'''
    #Vissim data
    if isinstance(objects[0].curvilinearPositions.lanes[0],str):
        laneDict, oppObjDict, manObjDict = calculate_laneChange(objects, corridors, 'vissim')
    else:
        laneDict, oppObjDict, manObjDict = calculate_laneChange(objects, corridors, 'video')

    return oppObjDict, manObjDict, laneDict

def getTTFromVissimFile(filename, warmUpLastInstant = None, lowMemory = True, output = 'travelTimes'):
    '''filename has to be a .rsr'''
    #import pandas
    from pandas import read_csv
    data = read_csv(filename, delimiter=';', comment='*', header=0, skiprows = 7, low_memory = lowMemory)#, converters = myStrip)

    if warmUpLastInstant is not None:
        data = data[data['  Time']>=warmUpLastInstant]

    travelTimes = {}
    delays = {}
    for row_index, row in data.iterrows():
        if row['   No.'] in delays.keys():
            delays[row['   No.']].append(row[' Delay'])
        else:
            delays[row['   No.']] = [row[' Delay']]

        if row['   No.'] in travelTimes.keys():
            travelTimes[row['   No.']].append(row['  Trav'])
        else:
            travelTimes[row['   No.']] = [row['  Trav']]

    if output == 'Delays':
        return delays.values(), delays.keys()
    if output == 'travelTimes':
        return travelTimes.values(), travelTimes.keys()

def extract_num_from_fzp_name(filename):
    '''returns the numerical component of a vissim fzp file'''
    return int(os.path.splitext(filename)[0].split('_')[-1])

def extract_num_from_fzp_list(filenames):
    '''returns the numerical component of a list of vissim fzp files'''
    num_list = []
    for filename in filenames:
        num_list.append(extract_num_from_fzp_name(filename))
    return num_list

def calculateQueues(objects,approaches):
        pass    #v = 3km/h à mettre dans config

def randomGaussRange(low, high, n):
    out = []
    mu = random.uniform(low, high)
    sigma = random.uniform(0, (mu - low) )
    while len(out) < n:
        num = (random.normalvariate(mu, sigma))
        if num < high and num > low:
            out.append(num)

    return out

def generateRandomOutputs(parameters, rand_seed_shake, outputs):
    '''This fonction serves to bypass everything produced by Vissim to gain
       speed while testing the code'''
    RandSeed = parameters[1]
    NumRuns = parameters[2]

    for i in range(NumRuns):
        random.seed(RandSeed + i + rand_seed_shake)
        outputs.addSingleOutput('flow',       random.uniform(2,30),       'random_gen')
        outputs.addSingleOutput('oppLCcount', random.uniform(2,30),       'random_gen')
        outputs.addSingleOutput('manLCcount', random.uniform(1200,2000),  'random_gen')
        outputs.addSingleOutput('forFMgap',   randomGaussRange(1,20,100), 'random_gen')
        outputs.addSingleOutput('forSpeeds',  randomGaussRange(1,20,100), 'random_gen')
        outputs.addSingleOutput('manLCagap',  randomGaussRange(1,20,100), 'random_gen')
        outputs.addSingleOutput('manLCagap',  randomGaussRange(5,10,100), 'random_gen')
        outputs.addSingleOutput('oppLCagap',  randomGaussRange(7,10,100), 'random_gen')
        outputs.addSingleOutput('oppLCagap',  randomGaussRange(7,10,100), 'random_gen')

    return outputs

def treatVissimOutputs(files, inputs):
    '''Treat outputs in the given folder '''

    for filename in files:
        outputs = treat_Single_VissimOutput(filename, inputs)
        inputs[3] = outputs

    return outputs

def convert_fzp_to_sqlite(folderpath, filename):
    #create the sqlite3 create_table file
    name, num = write.Sqlite.create_table(folderpath, filename)

    #save current working directory
    saved_cwd = os.getcwd()

    #move current working directory
    os.chdir(os.path.join(folderpath))

    #call sqlite3 to create the actual table
    out = open('sqlite_error_file_'+str(num)+'.txt','w')
    subprocess.check_call('sqlite3.exe ' + os.path.splitext(filename)[0] +'.sqlite' + ' < ' + name, stderr = out, shell = True)
    out.close()

    #move back the current working directory
    os.chdir(saved_cwd)

    #delete fzp
    os.remove(os.path.join(folderpath, filename))

    #delete create_table.sql
    os.remove(os.path.join(folderpath, name))

    #delete sqlite_error_file.txt
    os.remove(os.path.join(folderpath, 'sqlite_error_file_'+str(num)+'.txt'))

    return os.path.join(folderpath, os.path.splitext(filename)[0] +'.sqlite')

def treat_Single_VissimOutput(filename, inputs):
    '''Treat outputs in the given folder '''

    folderpath                 = inputs[0]
    verbose                    = inputs[1]
    corridors                  = inputs[2]
    outputs                    = inputs[3]
    config                     = inputs[4]
    VehiculeInputs             = inputs[5]
    SignalHeads                = inputs[6]

    if verbose:
        print ' === Starting calculations for ' + filename + ' ===  |'

    #building to eval lanes
    to_eval = []
    for j in xrange(len(corridors)):
        to_eval += corridors[j].to_eval
    for s in xrange(len(config.saturation_values)):
        if config.saturation_values[s][1] not in to_eval:
            to_eval.append(config.saturation_values[s][1])

    if filename.endswith('fzp'):
        sqlite_db_path = convert_fzp_to_sqlite(folderpath, filename)
    else:
        sqlite_db_path = os.path.join(folderpath, filename)

    objNums = storage.loadObjectNumbersInLinkFromVissimFile(sqlite_db_path, to_eval)

    objects = storage.loadTrajectoriesFromVissimFile(sqlite_db_path, config.sim_steps, objectNumbers = objNums, warmUpLastInstant = config.warm_up_time, usePandas = False, lowMemory = False)
    outputs.addSingleOutput('flow', len(objects), filename)

    #lane building block
    lanes = {}
    all_lanes = {}
    for o in objects:
        o.curvilinearVelocities = o.curvilinearPositions.differentiate(True)
        for i in xrange(len(o.curvilinearPositions.lanes)):
            p = o.curvilinearPositions[i]
            lane = p[2]
            s = p[0]
            if int(lane.split('_')[0]) in to_eval:
                if lane not in lanes:
                    lanes[lane] = [s, s]
                else:
                    if s < lanes[str(lane)][0]:
                        lanes[str(lane)][0] = s
                    elif s > lanes[str(lane)][1]:
                        lanes[str(lane)][1] = s

            if lane not in all_lanes:
                all_lanes[lane] = [s, s]
            else:
                if s < all_lanes[str(lane)][0]:
                    all_lanes[str(lane)][0] = s
                elif s > all_lanes[str(lane)][1]:
                    all_lanes[str(lane)][1] = s

    #lane change count by type
    oppObjDict, manObjDict, laneDict = laneChange(objects,corridors)

    if verbose:
        print ' == Lane change compilation done ==  |' + str(time.clock())

    #constraint
    if 'flowPasses' in outputs.getActiveConstraintNames():
        linkDict = {}
        for vehInput in VehiculeInputs:
            linkDict[int(vehInput.link)] = len(storage.loadObjectNumbersInLinkFromVissimFile(sqlite_db_path, [int(vehInput.link)]))
        outputs.addConstraintValue('flowPasses', compareSimAndInputFlows(linkDict, VehiculeInputs, config.diFlow_constraint[1]), filename)
    if 'collisions' in outputs.getActiveConstraintNames():
        outputs.addConstraintValue('collisions', smartCountCollisionsVissim(folderpath, filename, config.fzp_maxLines), filename)

    if os.path.isfile(os.path.join(folderpath, filename.strip('.fzp')+'.err')):
        num, dp, a0 = read_error_file(folderpath, filename.strip('.fzp')+'.err')
    else:
        num = None; dp = None; a0 = None

    outputs.addConstraintValue('nonGen', num, filename)
    outputs.addConstraintValue('deceleration', dp, filename)
    outputs.addConstraintValue('acceleration', a0, filename)

    #saturation volume constraint
    #
    #the calculation is done lane by lane and we return the maximum observed on any lane of the link at any given point in the simulation
    lane_saturation_flow = [ [] for i in xrange(len(config.saturation_values))]
    lanes_to_process = [config.saturation_values[i][1] for i in xrange(len(config.saturation_values))]
    for i in xrange(len(config.saturation_values)):
        for index,lane in enumerate(all_lanes):
            if int(lane.split('_')[0]) in lanes_to_process:

                #if lane has a Signal head, we use the signal head position
                sh_lanes = [str(sh[1].split('-')[0])+'_'+str(sh[1].split('-')[1]) for sh in SignalHeads]
                if lane in sh_lanes:
                    s = SignalHeads[sh_lanes.index(lane)][2]

                #otherwise, we use the middle of the link
                else:
                    s = (0.5*all_lanes[str(lane)][1]-0.5*all_lanes[str(lane)][0])
                lane_saturation_flow[lanes_to_process.index(int(lane.split('_')[0]))].append(saturationFlow(objects, s, lane, config.saturation_centile, config.saturation_max_tiv, config.saturation_min_nb_tiv, config.sim_steps))

    for i in xrange(len(lane_saturation_flow)):
        if len(lane_saturation_flow[i]) > 0:
            outputs.addConstraintValue('saturation_'+str(i), max(lane_saturation_flow[i]), filename)
        else:
            outputs.addConstraintValue('saturation_'+str(i), 0, filename)

    if verbose:
        print ' == Constraints calculations done ==  |' + str(time.clock())

    outputs.addSingleOutput('oppLCcount', sum([len(oppObjDict[i]) for i in oppObjDict]), filename)
    outputs.addSingleOutput('manLCcount', sum([len(manObjDict[i]) for i in manObjDict]), filename)

    #Forward GAPS
    if config.cmp_for_gaps:
        raw_forward_gaps = []
        raw_forward_speeds = []
        #forward gap analysis
        for index,lane in enumerate(lanes):
            s = (0.5*lanes[str(lane)][1]-0.5*lanes[str(lane)][0])
            raw_gaps, raw_speeds = forwardGaps(objects, s, lane)
            if raw_gaps != []: raw_forward_gaps += list(raw_gaps)
            if raw_speeds != []: raw_forward_speeds += list(raw_speeds)
            if verbose:
                print ' == Forward gaps calculation done for lane ' + str(index +1) + '/' + str(len(lanes)) + ' ==  |' + str(time.clock()) + ' | ' + str(len(raw_gaps))
        outputs.addSingleOutput('forFMgap', raw_forward_gaps, filename)
        outputs.addSingleOutput('forSpeeds', raw_forward_speeds, filename)

    #Mandatory lane changes headway acceptance
    if config.cmp_man_lcgaps:
        raw_man_LC_agaps    = []
        raw_man_LC_bgaps    = []
        #mandatory lane change gaps
        agaps, bgaps = laneChangeGaps(manObjDict, laneDict, objects)
        if agaps.any(): raw_man_LC_agaps = agaps.tolist()
        if bgaps.any(): raw_man_LC_bgaps = bgaps.tolist()
        if verbose:
            print ' == Mandatory lane change gaps calculation done  ==  |' + str(time.clock())
        outputs.addSingleOutput('manLCagap', raw_man_LC_agaps, filename)
        outputs.addSingleOutput('manLCbgap', raw_man_LC_bgaps, filename)

    #Opportunistic lane changes headway acceptance
    if config.cmp_opp_lcgaps:
        raw_opp_LC_agaps    = []
        raw_opp_LC_bgaps    = []

        #opportunistic lane change gaps
        agaps, bgaps = laneChangeGaps(oppObjDict, laneDict, objects)
        if agaps.any(): raw_opp_LC_agaps = agaps.tolist()
        if bgaps.any(): raw_opp_LC_bgaps = bgaps.tolist()
        if verbose:
            print ' == Opportunistic lane change gaps calculation done ==  |' + str(time.clock())
        outputs.addSingleOutput('oppLCagap', raw_opp_LC_agaps, filename)
        outputs.addSingleOutput('oppLCbgap', raw_opp_LC_bgaps, filename)

    if config.cmp_travel_times:
        if os.path.isfile(os.path.splitext(sqlite_db_path)[0]+'.rsr'):
            travelTimes, keys = getTTFromVissimFile(os.path.splitext(sqlite_db_path)[0]+'.rsr', warmUpLastInstant = config.warm_up_time, lowMemory = False)
            outputs.addSingleOutput('travelTms', travelTimes, filename)
            outputs.addInfos('travelTms',keys)

    if verbose:
        print ' === Calculations for ' + filename + ' done ===  |' + str(time.clock()) + '\n'

    if config.delete_simulated_data is True:
        os.remove(sqlite_db_path)

    return outputs