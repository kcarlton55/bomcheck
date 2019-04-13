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
#f = '/home/ken/projects/bomdata/top_level/082009_top_sw.xlsx'
df = pd.read_excel(f, na_values=[' '])
#f = '/home/ken/projects/bomdata/top_level/082009_top_sw.xlsx'
#df = pd.read_excel(f, na_values=[' '], skiprows=1)

#for i, x in enumerate(df['Level']):
#    print(i, x)




def appendLevel2(df, top='TOPLEVEL'):
    ''' If a SyteLine BOM is a multilevel BOM a SolidWorks BOM is multilevel,
    then append a new column to that BOM named Level2.  Level2 contains the
    parent subassembly number corresponding to the part at a given row.    
    '''
    # Find the column name that contains the pns.  The column name varies
    # depending on whether it came from SolidWorks or SyteLine, and varies
    # based upon which section of the program generated the BOM.
    if 'Item' in df.columns:
        ptno = 'Item'
    elif 'Material' in df.columns:
        ptno = 'Material'
    elif 'PARTNUMBER' in df.columns:
        ptno = 'PARTNUMBER'
    else:
        ptno = 'PART NUMBER'
    # if BOM is from SW, generate a column named Level based on the column
    # ITEM NO.  This column constains values like 1, 2, 3, 3.1, 3.1.1, 3.1.2,
    # 3.2, etc. where item 3.1 is a member of subassy 3.
    if 'ITEM NO.' in df.columns:
        df['ITEM NO.'] = df['ITEM NO.'].astype('str')
        df['Level'] = df['ITEM NO.'].str.count('\.')
    # Take the the column named "Level" and create a new column: "Level2".
    # Instead of the level at which a part exists with in an assembly, like
    # Level which contains integers like [0, 1, 2, 2, 1], Level2 contains
    # the parent part no. of the part at a particular level, i.e. 
    # ['TOPLEVEL', '068278', '2648-0300-001', '2648-0300-001', '068278']
    lvl = 0
    level2 = []  # record pn of subassy corresponding to a part at rows 0, 1, 2, 3, ...
    poplist = []  # add or remove pns depending on the integer in column "Level"
    assys = []  # get a list of all subassys found... don't record stand-alone pns
    for item, row in df.iterrows():
        if row['Level'] == 0:
            level2.append(top)
            poplist.append(row[ptno].strip())
        # part is a member of the subassy whose pn is givin in the previous row:
        elif row['Level'] > lvl: 
            lvl = row['Level']
            if poplist[-1] in assys:  # If subassy already acounted for, ignore it.
                level2.append('repeat')
            else:
                level2.append(poplist[-1])
            assys.append(poplist[-1])  # collect all subassy pns, not part pns
            poplist.append(row[ptno].strip())
        elif row['Level'] == lvl:
            # If subassy already acounted for, ignore it.
            if poplist[-2] in assys and assys.count(poplist[-2]) > 1:
                level2.append('repeat')
            else:
                level2.append(poplist[-2])
            poplist.pop() # get rid of previouly recorded pn.  Not needed.
            poplist.append(row[ptno].strip()) # pn at row we're on may be the next subassy pn 
        elif row['Level'] < lvl:
            i = -(1 + lvl - row['Level'])  # how much to pop
            poplist = poplist[:i]   # remove, i.e. pop, i items from end of list
            poplist.append(row[ptno].strip())
            level2.append(poplist[-2])
            lvl = row['Level']        
    df['Level2'] = level2
            
    for i, x in enumerate(level2):
        print(i+2, x)
        
    return df
        
        

#appendLevel2(df)





def temp(df, top='TOP'):
    df['ITEM NO.'] = df['ITEM NO.'].astype('str')
    df['LEVEL'] = df['ITEM NO.'].str.count('\.') + 1
#    if 'PART NUMBER' in df.columns:
#        colName = 'PART NUMBER'
#    else:
#        colName = 'PARTNUMBER'
       
   
       
#    df = df.sort_index(axis=1 ,ascending=True)
#    print(pn, colName)
#    df2 = pd.DataFrame([['descrip', 23, 0, 0, pn, 5]], columns=df.columns)
#    df2 = pd.DataFrame([[0, pn]], columns=['LEVEL', colName])
    #df2 = pd.DataFrame([[pn]], columns=[pnColName])
    #df2 = pd.DataFrame([[0]], columns=['LEVEL'])
#    df = df.append(df2, sort=True)
#    df = df.sort_index(axis=1 ,ascending=True)
   
    return df 
        
        

    