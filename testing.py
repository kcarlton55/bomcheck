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
# f = '/home/ken/projects/bomdata/080493_3rd_go/6875-080493-1_sl.xlsx'
f = '/home/ken/projects/bomdata/top_level/081779-LH_081779-RH_sl.xlsx'
# f = '/home/ken/projects/bomdata/top_level/081779-RH_sl.xlsx'
# f = '/home/ken/projects/bomdata/top_level/test_sl.xlsx'
dfsl = pd.read_excel(f, na_values=[' '])
f = '/home/ken/projects/bomdata/top_level/082009_top_sw.xlsx'
f = '/home/ken/projects/bomdata/080493_3rd_go/6875-080493-1_sw.xlsx'
dfsw = pd.read_excel(f, na_values=[' '], skiprows=1)

#for i, x in enumerate(df['Level']):
#    print(i, x)


[('Qty', 'Quantity'), 'Material Description', 'U/M', ('Item', 'Material')]

def multilevelbom(df, top='TOPLEVEL'):
    ''' If the BOM is a multilevel BOM, pull out the components thereof; that
    is, pull out the main assembly and the subassemblies thereof.  These 
    assys/subassys are  placed in a python dictionary and returned.

    Parmeters
    =========

    df : Pandas DataFrame
        The DataFrame is that of a SolidWorks or SyteLine BOM.
        
    top : string
        If df is derived from a file such as 082009_sw.xlxs, "top" should be
        assigned "082009" since the top level part number is not given in the 
        Excel file and therefore can't be derived from the file.  Likewise for a
        single level Syteline BOM.  On the other hand a mulilevel SyteLine BOM,
        which has a column named "Level", has the top level pn contained within
        (assigned at "Level" 0).  In this case use the default "TOPLEVEL".
        
    Returns
    =======
    
    out : python dictionary
        The dictionary has the form {assypn1: BOM1, assypn2: BOM2, ...}.
        Where assypn is a string object and is the part number of a BOM.
        The BOMs are pandas DataFrame objects.
    '''
    # Find the column name that contains the pns.  This column name varies
    # depending on whether it came from SW or SL, and varies based upon which
    # section of the program generated the BOM.
    for pncolname in ['Item', 'Material', 'PARTNUMBER', 'PART NUMBER']:
        if pncolname in df.columns:
            ptno = pncolname
    df[ptno] = df[ptno].str.strip() # make sure pt nos. are "clean"
    df[ptno].replace('', 'pn missing', inplace=True)
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
    # Take the the column named "Level" and create a new column: "Level_pn".
    # Instead of the level at which a part exists with in an assembly, like
    # "Level", which contains integers like [0, 1, 2, 2, 1], "Level_pn" contains
    # the parent part no. of the part at a particular level, i.e. 
    # ['TOPLEVEL', '068278', '2648-0300-001', '2648-0300-001', '068278']
    lvl = 0
    level_pn = []  # storage of pns of parent assy/subassy of the part at rows 0, 1, 2, 3, ...
    assys = []  # storage of all assys/subassys found (stand alone parts ignored)
    for item, row in df.iterrows():
        if row['Level'] == 0:
            poplist = []
            level_pn.append(top)
            if top != "TOPLEVEL":
                assys.append(top)
        elif row['Level'] > lvl: 
            if p in assys:
                poplist.append('repeat')
            else:
                assys.append(p)
                poplist.append(p)
            level_pn.append(poplist[-1]) 
        elif row['Level'] == lvl:
            level_pn.append(poplist[-1])
        elif row['Level'] < lvl:
            i = row['Level'] - lvl  # how much to pop.  i is a negative number.
            poplist = poplist[:i]   # remove, i.e. pop, i items from end of list
            level_pn.append(poplist[-1])
        p = row[ptno]
        lvl = row['Level']
    df['Level_pn'] = level_pn
    # collect all assys/subassys within df and return a dictionary.  keys
    # of the dictionary are pt. numbers of assys/subassys.
    dic_assys = {}
    for k in assys:
        dic_assys[k] = df[df['Level_pn'] == k]         
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
        _, file_extension = os.path.splitext(v)
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
        _, file_extension = os.path.splitext(v)
        if file_extension == '.csv':
            df = pd.read_csv(v, na_values=[' '], engine='python',
                             encoding='utf-16', sep='\t')
        elif file_extension == '.xlsx' or file_extension == '.xls':
            df = pd.read_excel(v, na_values=[' '])
        sldfsdic.update(multilevelbom(df, k))
    dirname = os.path.dirname(filename[0])
    if dirname and not os.path.exists(dirname):
        print('directory not found: ', dirname)
        sys.exit(0)
        
    swdfsdic = missing_columns('sw', swdfsdic, [('QTY', 'QTY.'), 'DESCRIPTION',
                                                ('PART NUMBER', 'PARTNUMBER')])
    sldfsdic = missing_columns('sl', sldfsdic, [('Qty', 'Quantity'), 
                                                'Material Description', 'U/M', 
                                                ('Item', 'Material')])
    return dirname, swdfsdic, sldfsdic     


def missing_tuple(tpl, lst):
    ''' If none of the items of tpl (tuple) are in lst (list) return
    tpl.  Else return None
    '''
    flag = True
    for t in tpl:
        if t in lst:
            flag = False
    if flag:
        return tpl


def missing_columns(bomtype, dfdic, required_columns):
    ''' SolidWorks and SyteLine BOMs require certain columns to be
    present.  This function looks at those BOMs that are within dfdic
    to see if any required columns are missing.  If missing columns found,
    prints them to screen.  Then returns a dictionary like that input less
    the faulty BOMs.

    Parameters
    ==========

    bomtype : string
        "sw" or "sl"

    dfdic : dictionary
        Dictionary keys are strings and they are of assembly part numbers.
        Dictionary values are pandas DataFrame objects which are
        BOMs for those assemblies.

    required_columns : list
        List items are strings or tuples.  If a string, then it is
        the name of a required column.  If a tuple, they are column
        names where only one of which is a required column.  For example:
        [('QTY', 'QTY.'), 'DESCRIPTION', ('PART NUMBER', 'PARTNUMBER')]
        Note that column names are case sensitive.   

    Returns
    =======

    out : dictionary
        Returns dfdic except any items that fail the test are removed. 
    '''
    missing = []   # list of strings detailing missing column info
    dfdic_screened = dict(dfdic)
    for key, df in dfdic.items():
        missing_per_df = []
        flag = True
        for r in required_columns:
            if ((isinstance(r, str) and r in df.columns) or
                 (isinstance(r, tuple) and not missing_tuple(r, df.columns))):
                flag = False
            elif flag and isinstance(r, str) and r not in df.columns:
                missing_per_df.append(r)
            elif flag and isinstance(r, tuple) and missing_tuple(r, df.columns):
                missing_per_df.append(' or '.join(missing_tuple(r, df.columns)))
        if missing_per_df:
            missing.append(key + '_' + bomtype + ' has missing columns: ')
            missing.append(' ,'.join(missing_per_df))
            del dfdic_screened[key]
    print('\n'.join(missing))
    return dfdic_screened


def combine_tables(swdic, sldic):
    ''' Match SolidWorks assembly nos. to those from SyteLine and then merge
    their BOMs to create a BOM check.  For any SolidWorks assemblies for which
    no SyteLine BOM was found, put those in a separate dictionary for output.

    Parameters
    ==========

    swdic : dictionary
        Dictinary of SolidWorks BOMs.  Dictionary keys are strings and they 
        are of assembly part numbers.  Dictionary values are pandas DataFrame 
        objects which are BOMs for those assemblies.

    sldic : dictionary
        Dictinary of SyteLine BOMs.  Dictionary keys are strings and they 
        are of assembly part numbers.  Dictionary values are pandas DataFrame 
        objects which are BOMs for those assemblies.

    Returns
    =======

    out : tuple
        The output tuple contains two values: 1.  Dictionary containing SolidWorks
        BOMs for which no matching SyteLine BOM was found.  The BOMs have been
        converted to a SyteLine like format.  Keys of the dictionary are assembly
        part numbers.  2.  Dictionary of merged SolidWorks and SyteLine BOMs, thus
        creating a BOM check.  Keys for the dictionary are assembly part numbers.
    '''
    lone_sw_dic = {}  # sw boms with no matching sl bom found
    combined_dic = {}   # sl bom found for given sw bom.  Then merged
    for key, swdf in swdic:
        if key in sldic:
            combined_dic[key] = sl(sw(swdf), sldic[key])
        else:
            lone_sw_dic[key + '_sw'] = su(sldic[key])
    return lone_sw_dic, combined_dic




        

    