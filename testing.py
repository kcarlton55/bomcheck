#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 22:12:44 2019

@author: ken
"""

import pprint
import pandas as pd



f = '/home/ken/projects/bomdata/top_level/084387_truncated_sltop.xlsx'
f = '/home/ken/projects/bomdata/top_level/084387_sltop2.xlsx'
f = '/home/ken/projects/bomdata/top_level/068278_TOP.xlsx'
df = pd.read_excel(f, na_values=[' '])

#for i, x in enumerate(df['Level']):
#    print(i, x)


def appendLevel2(df):
    ''' If a SyteLine BOM is a multilevel BOM a SolidWorks BOM is multilevel,
    then append a new column to that BOM named Level2.  Level2 contains the
    parent subassembly number corresponding to the part at a given row.    
    '''
    level2 = []  # record pn of subassy corresponding to a part at rows 0, 1, 2, 3, ...
    poplist = []  # add or remove pns depending on the integer in column "Level"
    assys = []  # get a list of all subassys found.  Don't record stand-alone pns
    for item, row in df.iterrows():
        if row['Level'] == 0:
            level2.append('TOP')
            poplist.append(row['Item'].strip())
        # part is a member of the subassy whose pn is givin in the previous row:
        elif row['Level'] > lvl: 
            lvl = row['Level']
            if poplist[-1] in assys:  # If subassy already acounted for, ignore it.
                level2.append('repeat')
            else:
                level2.append(poplist[-1])
            assys.append(poplist[-1])  # collect all subassy pns, not part pns
            poplist.append(row['Item'].strip())
        elif row['Level'] == lvl:
            # If subassy already acounted for, ignore it.
            if poplist[-2] in assys and assys.count(poplist[-2]) > 1:
                level2.append('repeat')
            else:
                level2.append(poplist[-2])
            poplist.pop() # get rid of previouly recorded pn.  not needed.
            poplist.append(row['Item'].strip()) # pn at row we're on may be the next subassy pn 
        elif row['Level'] < lvl:
            i = -(1 + lvl - row['Level'])  # how much to pop
            poplist = poplist[:i]   # remove, i.e. pop, i items from end of list
            poplist.append(row['Item'].strip())
            level2.append(poplist[-2])
            lvl = row['Level']
            
    for i, x in enumerate(level2):
        print(i+2, x)
        
    print(assys)
        
        

appendLevel(df)        
        
        

    