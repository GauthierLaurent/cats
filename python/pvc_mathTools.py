# -*- coding: utf-8 -*-
"""
Created on Tue Mar 03 16:30:51 2015

@author: Laurent
"""
import math

##################
# Vectors tools
##################
def merge_vectors(a,b):
    '''a, b must be arrays'''
    if len(a) < len(b):
        c = b.copy()
        c[:len(a)] += a
    else:
        c = a.copy()
        c[:len(b)] += b
    return c

  
##################
# Rounding tools
##################    
def myround(x, base=5):
    '''version of math.round that rounds to the neerest base multiple'''
    return int(base * round(float(x)/base))
    
def myceil(x, base=5):
    '''version of math.ceil that ceils to the neerest base multiple'''    
    return int(base * math.ceil((float(x)/base)))
    
def myfloor(x, base=5):
    '''version of math.floor that floors to the neerest base multiple'''  
    return int(base * math.floor((float(x)/base)))


##################
# Lists tools
##################      
def sort2lists(list1,list2,ascending_order=True):
    '''Sorts list2 according to the sorting of the content of list1
       list1 must contain values that can be sorted while
       list2 may contain any kind of data'''
       
    indexes = range(len(list1))
    indexes.sort(key=list1.__getitem__)

    if ascending_order is True:  
        sorted_list1 = map(list1.__getitem__, indexes)
        sorted_list2 = map(list2.__getitem__, indexes)
        
    if ascending_order is False:  
        sorted_list1 = map(list1.__getitem__, reversed(indexes))
        sorted_list2 = map(list2.__getitem__, reversed(indexes))
        
    return sorted_list1, sorted_list2

def sortManyLists(reference, *lists, **kwargs):

    if 'ascending_order' in kwargs:
        ascending_order=kwargs['ascending_order']
    else:
        ascending_order=True

    indexes = range(len(reference))
    indexes.sort(key=reference.__getitem__)

    out = []

    if ascending_order is True:    
        out.append(map(reference.__getitem__, indexes))

        for list_i in lists:
            out.append(map(list_i.__getitem__, indexes))
            
    if ascending_order is False:    
        out.append(map(reference.__getitem__, indexes), reversed(indexes))

        for list_i in lists:
            out.append(map(list_i.__getitem__, indexes), reversed(indexes))
            
    return out
    
def intoList(out, mylist):
    '''unpack list of list into the list given in out'''
    for i in mylist:
        if isinstance(i, list) is True:
            intoList(out, i)            
        else:
            out.append(i)
    return out   

def ToOneList(*args):
    '''Take any number of arguments and returns a single list'''  
    out = []    
    for arg in list(args):
        if isinstance(arg, list) is True:
            out = intoList(out, arg)
        else:
            out.append(arg)
    return out
    
def addLists(P, Q, direction='left'):
    A, B = sorted([P, Q], key=len)

    if direction is 'right':
        for i, x in enumerate(reversed(A), 1):
            B[-i] += x            
    else:
        for i, x in enumerate(A):
            B[i] += x    
    return B

##################
# Variable tools
##################
def isbool(lists):
    '''checks if at least one element in lists is a boolean value''' 
    for element in lists:
        if isinstance(element,bool):
            return True
    return False

def isallbool(lists):
    '''checks if all elements in lists is are boolean values''' 
    for element in lists:
        if isinstance(element,bool) is False:
            return False
    return True