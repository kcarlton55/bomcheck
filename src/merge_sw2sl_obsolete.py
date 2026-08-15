# -*- coding: utf-8 -*-
"""
Created on Sat Jan 31 19:09:34 2026

@author: a90003183
"""

import pandas as pd
import numpy as np

cfg = {'accuracy': 2,   'ignore': ['3086-*'], 'drop': [],  'exceptions': [],
       'from_um': 'IN', 'to_um': 'FT', 'toL_um': 'GAL', 'toA_um': 'SQF',
       'part_num':  ["Material", "PARTNUMBER", "PART NUMBER", "Part Number", "Item"],
       'qty':       ["QTY", "QTY.", "Qty", "Quantity", "Qty Per", "Quantity Per"],
       'descrip':   ["DESCRIPTION", "Material Description", "Description"],
       'um_sl':     ["UM", "U/M"],
       'level_sl':  ["Level"],
       'itm_sw':    ["ITEM NO."],
       'length_sw': ["LENGTH", "Length", "L", "SIZE", "AMT", "AMOUNT", "MEAS",
                     "COST", "LN.", "LN"],
       'obs': ['Obsolete Date', 'Obsolete'], 'del_whitespace': True,
       # Column names shown in the results (for a given key, one value only):
       'assy':'assy', 'Item':'Item', 'iqdu':'IQDU', 'Q':'Q', 'Item No.':'Item No.',
       'Description':'Description', 'U':'U',
       # When a SW BOM is converted to a BOM looking like that of SL, these columns and
       # values thereof are added to the SW BOM, thereby making it look like a SL BOM.
       'Op':'Op', 'OpValue':'10', 'WC':'WC',  'WCvalue':'PICK'
      }

df1sw = pd.DataFrame(
        {'Part Number': ['0300-2025-101', '3510-0500-000', '7302-0050-000'],
        'QTY': [1, 2, 2],
        'Description': ['BASE', 'GASKET', 'VALVE']})
df2sw = pd.DataFrame(
        {'Part Number': ['2728-2025-004', '6100-0000-000', '7302-0050-000'],
        'QTY': [1, 1, 1],
        'Description': ['BRACKET', 'TANK', 'VALVE']})
df3sw = pd.DataFrame(
        {'Part Number': ['3800-0050-001', '3810-0050-000'],
        'QTY': [4, 4],
        'Description': ['SCREW', 'NUT']})
df4sw = pd.DataFrame(
        {'Part Number' : ['5500-0050-000', '5500-0050-000', '3086-0050-025', '7304-0020-001'],
         'QTY': [1, 2, 4, 5],
         'Description': ['PIPE', 'PIPE', 'NIPPLE', 'VALVE'],
         'LENGTH': [35.5, 8, 3.4, np.nan]})

df1sl = pd.DataFrame(
        {'Part Number': ['0300-2025-101', '3510-0500-000', '7302-0050-000'],
        'QTY': [1, 2, 5],
        'Description': ['BASE', 'GASKET', 'VALVE']})
df2sl = pd.DataFrame(
        {'Part Number': ['2728-2025-004', '6100-0000-000', '7302-0050-000'],
        'QTY': [1, 1, 1],
        'Description': ['BRACKET', 'TANK', 'VALVE']})
df3sl = pd.DataFrame(
        {'Part Number': ['3800-0050-001', '3810-0050-000'],
        'QTY': [4, 4],
        'Description': ['SCREW', 'NUT']})
df4sl = pd.DataFrame(
        {'Part Number': ['3800-0050-001', '3810-0050-000', '0300-2025-101', '2728-2024-005'],
        'QTY': [5, 4, 1, 1],
        'Description': ['SCREW', 'NUT', 'BASE', 'BRACKET']})
df5sl = pd.DataFrame(
        {'Part Number': ['4305-0125-000', '3510-0050-010', '3210-0200-001', '3210-0400-000'],
        'QTY': [1, 4, 1, 1],
        'Description': ['ENCLOSURE', 'GASKET', 'FLANGE', 'FLANGE']})
files_list = [{'assembly_pn1sw': df1sw, 'assembly_pn2sw': df2sw, 'assembly_pn3sw': df3sw, 'assembly_pn4sw': df4sw},
             {'assembly_pn1sl': df1sl, 'assembly_pn2sl': df2sl, 'assembly_pn3sl': df3sl,
              'assembly_pn4sl': df4sl, 'assembly_pn5sl': df5sl }]

#files_list = [{},  {'assembly_pn1sl': df1sl, 'assembly_pn2sl': df2sl, 'assembly_pn3sl': df3sl,
#              'assembly_pn4sl': df4sl, 'assembly_pn5sl': df5sl }]




def merge_swtosl(files_list = files_list):
    '''
    Extract part nos. from SolidWorks BOMs and part nos. from SyteLine BOMs and
    combine the two BOMs (discard any known assembly part numbers).  Eliminate 
    duplicate part numbers, but keep track of the quantities of parts that came
    from SolidWorks and the quantities of parts that came from SyteLine.  If
    a part has a length valve, i.e. a pipe, then convert the length to feet
    and muliply that length by the quantity of that length of pipe.  Convert
    lengths to an int, but rounded up to the nearest whole value.
    
    Parameters
    ----------
    files_list : list
        list contains two itmes: first item is a dictionary containing 
        SolidWorks BOMs.  The second is a dictionary containing SyteLine BOMs. 
        Each dictionary has the form: {assemblyPN1: df1, assemblyPN2: df2,
        assemblyPN3: df3, ...}; where assemblyPN1 is a sting looking like 
        'ACV01536', 'DVD44467', etc.; and df1 is a dataframe object contains
        the BOM for assemblyPN1.

    Returns
    -------
    Pandas dataframe
        A Pandas dataframe of the combined SolidWorks and SyteLine BOMs.  
        Dataframe contains column headings PN, DESCRIPTION, and QTY SW / SL.
        If only SolidWorks BOMs are provided, only show quatities for those 
        parts, e.g. 1, 1, 4, 4, 1.  If both SW and SL BOMs are provided, show 
        quatities from both SolidWorks and SyteLine, e.g. 1/2, 1/0, 4/3, 4/0, 
        1/0.  If for a particular part both SW and SL quatities are the same,
        then show only one number, e.g. 1/2, 1/0, 4/3, 4/0, 1/0, 5, 7, 4/3.
    '''  
    if not files_list[0]:  # create and empty dataframe
        files_list[0] = {'assembly_sw1':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': []})}
    if not files_list[1]:  # create and empty dataframe
        files_list[0] = {'assembly_sl1':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': []})}
    
    dfsw = pd.DataFrame() # start with an empty DataFrame    
    if files_list[0]:
        for k, v in files_list[0].items():
            dfi = v.copy()
            values = dict.fromkeys(cfg['part_num'], 'PN') 
            values.update(dict.fromkeys(cfg['descrip'], 'DESCRIPTION'))  # make sure descrip headers all the same: descrip
            values.update(dict.fromkeys(cfg['qty'], 'Q\nsw'))
            dfi.rename(columns=values, inplace=True)   # rename appropriate column headers to "PN" and "descrip"
            #dfi = dfi[['PN', 'DESCRIPTION', 'Q\nsw']]
            if 'LENGTH' in dfi.columns:
                dfi['l2'] = dfi['LENGTH']/12.0    # convert inch lengths to feet
                dfi.loc[dfi['PN'].str.contains('3086-'), 'l2'] = 1  # if pn is 3086-, set l2 = 1
                dfi['l2'] = dfi['l2'].fillna(1)
                dfi['Q\nsw'] = dfi['Q\nsw'] * dfi['l2']   # it, qty to qty * l2 (where l2 is the number for feet)
                dfi['Q\nsw'] = (dfi['Q\nsw'] + .5).astype(float).round().astype(int) # round up to nearest foot and make value be an int
            dfi = dfi[['PN', 'DESCRIPTION', 'Q\nsw']]
            dfsw = pd.concat([dfsw, dfi])
            
        dfsw = dfsw.groupby(['PN', 'DESCRIPTION'], as_index=False)['Q\nsw'].sum()

    dfsl = pd.DataFrame() # start with an empty DataFrame        
    if files_list[1]:
        for k, v in files_list[1].items():
            dfi = v.copy()
            values = dict.fromkeys(cfg['part_num'], 'PN') 
            values.update(dict.fromkeys(cfg['descrip'], 'DESCRIPTION'))  # make sure descrip headers all the same: descrip
            values.update(dict.fromkeys(cfg['qty'], 'Q\nsl'))
            dfi.rename(columns=values, inplace=True)   # rename appropriate column headers to "PN" and "descrip"
            dfi = dfi[['PN', 'DESCRIPTION', 'Q\nsl']]
            dfsl = pd.concat([dfsl, dfi])
        dfsl = dfsl.groupby(['PN', 'DESCRIPTION'], as_index=False)['Q\nsl'].sum()
        
    df = dfsw.merge(dfsl, on='PN', how='outer')   
    
    df['DESCRIPTION'] = df['DESCRIPTION_x'].combine_first(df['DESCRIPTION_y'])
    df = df.fillna(0)
    df['Q\nsw'] = df['Q\nsw'].astype(int)
    df['Q\nsl'] = df['Q\nsl'].astype(int)
    
    df['Qty\nsw / sl'] = df['Q\nsw'].astype(str) + ' / ' +  df['Q\nsl'].astype(str)
    df.loc[df['Q\nsw'] == df['Q\nsl'], 'Qty\nsw / sl' ] = df['Q\nsw'].astype(str) + '  '
    
    if (df['Q\nsw'] == 0).all():
        df['Qty\nsw / sl'] = df['Q\nsl'].astype(str) + '  '
    elif (df['Q\nsl'] == 0).all():
        df['Qty\nsw / sl'] = df['Q\nsw'].astype(str) + '  '
                                             
    df = df.drop(columns=['DESCRIPTION_x', 'DESCRIPTION_y', 'Q\nsw', 'Q\nsl' ])
    
    return df


