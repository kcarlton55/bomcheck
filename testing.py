#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 22:12:44 2019

@author: ken
"""

import glob, argparse, sys, warnings
import pandas as pd
import os.path
import tempfile
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)




f = '/home/ken/projects/bomdata/top_level/084387_truncated_sltop.xlsx'
f = '/home/ken/projects/bomdata/top_level/084387_sltop2.xlsx'
f = '/home/ken/projects/bomdata/top_level/068278_TOP.xlsx'
f = '/home/ken/projects/bomdata/080493_3rd_go/6875-080493-1_sl.xlsx'
f = '/home/ken/projects/bomdata/top_level/081779-LH_081779-RH.xlsx'
dfsl = pd.read_excel(f, na_values=[' '])
f = '/home/ken/projects/bomdata/top_level/082009_top_sw.xlsx'
f = '/home/ken/projects/bomdata/080493_3rd_go/6875-080493-1_sw.xlsx'
dfsw = pd.read_excel(f, na_values=[' '], skiprows=1)

#for i, x in enumerate(df['Level']):
#    print(i, x)


[('Qty', 'Quantity'), 'Material Description', 'U/M', ('Item', 'Material')]

def multilevelbom(df, top='TOPLEVEL'):
    ''' If the BOM is a multilevel BOM, pull out the components of; that is
    pull out the main assembly and the subassemblies.  These assmblies are 
    placed in a dictionary and returned.

    Parmeters
    =========

    df : Pandas DataFrame
        The DataFrame is that of a SolidWorks or SyteLine BOM.
        
    top : string
        If df is derived a file such as 082009_sw.xlxs, "top" should be
        assigned "082009" because the top level part number is not shown
        in the Excel file.  On the other hand, in a SyteLine BOM the
        top level part number is present.  Use the default "TOPLEVEL".
        
    Returns
    =======
    
    out : dictionary
        The dictionary has the from {assypn1: BOM1, assypn2: BOM2, ...}.
        Where assypn is a string object and is the part number of a BOM.
        Each BOM in the dictionary is a DataFrame object and is the BOM 
        pertaining to an assembly part number.
    '''
    # Find the column name that contains the pns.  The column name varies
    # depending on whether it came from SW or SL and varies based upon which
    # section of the program generated the BOM.
    for pncolname in ['Item', 'Material', 'PARTNUMBER', 'PART NUMBER']:
        if pncolname in df.columns:
            ptno = pncolname
    df[ptno] = df[ptno].str.strip()  # At times SW pn values are like: "    "
    df[ptno].replace('', 'description missing', inplace=True)
    values = {'QTY':0, 'QTY.':0, 'Qty':0, 'Quantity':0, 'LENGTH':0, 
              'DESCRIPTION': 'description missing', 
              'Material Description': 'description missing',
              'PART NUMBER': 'pn missing', 'PARTNUMBER': 'pn missing', 
              'Item': 'pn missing', 'Material':'pn missing'} 
    df.fillna(value=values, inplace=True)
    # if BOM is from SW, generate a column named Level based on the column
    # ITEM NO.  This column constains values like 1, 2, 3, 3.1, 3.1.1, 3.1.2,
    # 3.2, etc. where item 3.1 is a member of subassy 3.
    if 'ITEM NO.' in df.columns:  # is a sw bom
        df['ITEM NO.'] = df['ITEM NO.'].astype('str')
        df['Level'] = df['ITEM NO.'].str.count('\.')
    elif 'Level' not in df.columns:  # is a single level sl bom
        df['Level'] = 0
    # Take the the column named "Level" and create a new column: "Level2".
    # Instead of the level at which a part exists with in an assembly, like
    # Level, which contains integers like [0, 1, 2, 2, 1], Level2 contains
    # the parent part no. of the part at a particular level, i.e. 
    # ['TOPLEVEL', '068278', '2648-0300-001', '2648-0300-001', '068278']
    lvl = 0
    level2 = []  # record pn of subassy corresponding to a part at rows 0, 1, 2, 3, ...
    poplist = []  # add or remove pns depending on the integer in column "Level"
    assys = []  # get a list of all subassys found... don't record stand-alone pns
    for item, row in df.iterrows():
        if row['Level'] == 0:
            level2.append(top)
            poplist.append(row[ptno])
            if top != "TOPLEVEL":
                assys.append(top)
        # part is a member of the subassy whose pn is givin in the previous row:
        elif row['Level'] > lvl: 
            lvl = row['Level']
            if poplist[-1] in assys:  # If subassy already acounted for, ignore it.
                level2.append('repeat')
            else:
                level2.append(poplist[-1])
            assys.append(poplist[-1])  # collect all subassy pns, not part pns
            poplist.append(row[ptno])
        elif row['Level'] == lvl:
            # If subassy already acounted for, ignore it.
            if poplist[-2] in assys and assys.count(poplist[-2]) > 1:
                level2.append('repeat')
            else:
                level2.append(poplist[-2])
            poplist.pop() # get rid of previouly recorded pn.  Not needed.
            poplist.append(row[ptno]) # pn at row we're on may be the next subassy pn 
        elif row['Level'] < lvl:
            i = -(1 + lvl - row['Level'])  # how much to pop
            poplist = poplist[:i]   # remove, i.e. pop, i items from end of list
            poplist.append(row[ptno])
            level2.append(poplist[-2])
            lvl = row['Level']
    df['Level2'] = level2  # attach column named Level2 to the dataframe
    # collect all assemblies within df and return a dictionary.  keys
    # of the dictionary are assembly pt. numbers.
    assys = set(assys)
    dic_assys = {}
    for k in assys:
        if k != 'repeat':
            dic_assys[k] = df[df['Level2'] == k]         
    return dic_assys
        
        

def gatherBOMs(filename):
    ''' Gather all SolidWorks and SyteLine BOMs derived from "filename".
    "filename" can be a string containing wildcards, e.g. 6890-085555-*, which
    allows the capture of multiple files; or "filename" can be a list of such 
    strings.  These BOMs will be converted to Pandas DataFrame objects.
    
    Only files prefixed with _sw.xlsx, _sw.csv, _sl.xlsx, or _sl.csv will be
    chosen.  These files will then be converted to two python dictionaries.  
    One dictionary will contain SolidWorks BOMs only.  The other will contain
    only SyteLine BOMs.  The dictionary keys (i.e., "handles" allowing access
    to each BOM) will be the part numbers of the BOMs.
    
    If a filename corresponds to a BOM containing a multiple level BOM, then
    that BOM will be broken down to subassemblies and will be added to the
    dictionaries.
    
    Parmeters
    =========

    filename : string or list
        
    Returns
    =======
    
    out : tuple
        The output tuple contains three items.  The first is the directory
        corresponding the the first file in the filename list.  If this
        directory is an empty string, then it refers to the current working
        directory.  The remainder of the tuple items are python dictionararies.
        The first dictionary contains only SolidWorks BOMs,  The second, 
        SyteLine BOMs.
    '''
    if type(filename) == str:
        filename = [filename]     
    swfilesdic = {}
    slfilesdic = {}
    for x in filename:
        dirname = os.path.dirname(x)
        if dirname and not os.path.exists(dirname):
             print('directory not found: ', dirname)
             sys.exit(0)
        gatherednames = sorted(glob.glob(x))
        for f in gatherednames:
            i = f.rfind('_')
            if f[i:i+4].lower() == '_sw.' or f[i:i+4].lower() == '_sl.':
                dname, fname = os.path.split(f)
                k = fname.rfind('_')
                fntrunc = fname[:k]  # Name of the sw file, excluding path, and excluding _sw.xlsx
                if f[i:i+4].lower() == '_sw.':
                    swfilesdic.update({fntrunc: f})
                elif f[i:i+4].lower() == '_sl.':
                    slfilesdic.update({fntrunc: f})                 
    swdfsdic = {}
    for k, v in swfilesdic.items():
        filename, file_extension = os.path.splitext(v)
        if file_extension == '.csv':
            data = fixcsv(v)
            temp = tempfile.TemporaryFile(mode='w+t')
            for d in data:
                temp.write(d)
            temp.seek(0)
            df = pd.read_csv(temp, na_values=[' '], skiprows=1, sep=';',
                                   encoding='iso8859_1', engine='python')
            temp.close()
        elif file_extension == '.xlsx' or file_extension == '.xls':
            df = pd.read_excel(v, na_values=[' '], skiprows=1)
        swdfsdic.update(multilevelbom(df, k))
        
    sldfsdic = {}
    for k, v in slfilesdic.items(): 
        filename, file_extension = os.path.splitext(v)
        if file_extension == '.csv':
            df = pd.read_csv(v, na_values=[' '], engine='python',
                             encoding='utf-16', sep='\t')
        elif file_extension == '.xlsx' or file_extension == '.xls':
            df = pd.read_excel(v, na_values=[' '])
        swdfsdic.update(multilevelbom(df, k))
    
    dirname = os.path.dirname(filename[0])
    if dirname and not os.path.exists(dirname):
        print('directory not found: ', dirname)
        sys.exit(0)
        
    return dirname, swdfsdic, sldfsdic     







        

    