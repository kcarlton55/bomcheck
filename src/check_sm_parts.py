#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  6 15:28:36 2025

@author: Ken Carlton

Allow a comparison of SW/SL parts to those in slow_moving inventory.
This allows possible substitution of slow_moving parts in systems
currently being built so that slow_moving parts can be used up.
"""

#import pdb # use with pdb.set_trace()
import pandas as pd
from difflib import SequenceMatcher
import fnmatch
import re
#import numpy as np


def check_sm_parts(files_list, sm_files, cfg):
    ''' Collect part numbers and their descriptions that come from SolidWorks
    and SyteLine.  Compare the part numbers to those from a list of slow_moving
    parts to see if any of the slow_moving parts can be substituted.

    Parameters
    ----------
    files_list : list
        This list of two dictionaries that bomcheck.py supplies. It has the
        form:
        [{SWassembly_pn1: df1, SWassembly_pn2: df2, ..., SWassembly_pnN: dfN},
         {SLassembly_pn1: df1, SLassembly_pn2: df2, ..., SLassembly_pnN: dfN}]
        Where the first dictionary comes from SolidWorks; the second from
        SyteLine.  The df1, df2, etc. are the BOMs in DataFrame form
        that correspond to the assembly_pn.  This function, check_sm_parts,
        discards the assembly part numbers.

    cfg : dictionary
        cfg is comes from bomcheck.py and is the exact same dictionary that
        bomcheck.py uses.  cfg provides alternative header names that the BOMs
        might have, such as "Material", "PARTNUMBER", "PART NUMBER",
        "Part Number", "Item"; and "DESCRIPTION", "Material Description", and
        "Description".  With these alternative names, check_sm_parts figures 
        out what the correct headers should be for the part no. 
        and description fields.

    pn_fltr : string
        Part no. filter.  Normally will be assigned a value like '....-....-'.
        With this, part numbers 4610-2008-203, 5500-0025-001, and 6220-0055-004
        will be reduced to 4610-2008-, 5500-0025-, and 6220-0055-.  This
        reduction occurs in both the SW/SL BOMs and the slow_moving BOM.  The 
        shortened part nos. will be used for matching between BOMs.  This will
        result in, for example 4610-2008-203 finding the closest matching parts
        from the slow_moving BOM to be 4610-2008-198, 4610-2008-199,
        4610-2008-200, etc..

        The string is a regex string 
        (ref: https://en.wikipedia.org/wiki/Regular_expression).  The dot, .,
        represents one character.  Other suitable values for pn_filtr could be
        '.{10}', '.+-.+-'.  (.{10} means ten characters.  The .+ means one or
        more characters)

    Returns
    -------
    DataFrame

    Only the union of the SW/SL BOMs and the slow_moving BOM is output; 
    e.g. pt nos and desriptions, costs, usage, etc.
    '''
   
    # extract from "cfg" args from the user.
    try:
        pn_fltr = cfg['filter_pn'].text()
        descrip_filter = cfg['filter_descrip'].text() if cfg['filter_descrip'] else ''
    except:
        pn_fltr = cfg['filter_pn']
        descrip_filter = cfg['filter_descrip'] if cfg['filter_descrip'] else ''

    ####################################################################################
    ##### create df and populate it.  df is a collection of BOMs from SW & SL      #####
    ####################################################################################
    

    qty_col_name ='QTY\nSW/SL' 
    df = convert_files_list(files_list, cfg)
    df['common_pn'] = df['PN'].str.extract('(' + pn_fltr +')')  # apply the pn_fltr
              
    if cfg['drop_bool']==True and cfg['drop']:
        filtr3 = is_in(cfg['drop'], df['PN'], cfg['exceptions'])
        df.drop(df[filtr3].index, inplace=True) 
      
    ####################################################################################
    ##### dfinv is the dataframe derived from the excel sheet of slow_moving parts #####
    ####################################################################################
    dfinv = pd.DataFrame()  # start with an empty DataFrame
    for k, v in sm_files.items():
        dfinv = pd.concat([dfinv, v])

    df = df.dropna(subset=['common_pn'])  # drop rows that have NaN in column 'common_pn'
    df.reset_index(drop=True, inplace=True)

    # df doesn't haves cost of parts.  Get them from dfinv and put them into df.  
    df2 = df.merge(dfinv, left_on='PN', right_on='Item', how='left')
    df['COST'] = df2['Unit Cost'].fillna(0)
    df['COST'] = '$' + df['COST'].round(2).astype('string')  # Now a COST column is in df
        
    dfinv['De-\nmand?']= dfinv['De-\nmand?'].replace('No Demand', 'No')
    dfinv['De-\nmand?']= dfinv['De-\nmand?'].replace('Demand', 'Yes')
    
    if not cfg.get('show_demand', False):    
        dfinv = dfinv[dfinv['De-\nmand?'] == 'No']
        dfinv = dfinv.drop('De-\nmand?', axis=1)
    if not cfg.get('on_hand', False):    
        dfinv = dfinv[dfinv['On\nHand'] != 0.0]
        
    # match sure only number, e.g. "100, extracted from 'Last Used\n(Days)' 
    # and not "100 days", that a user could enter. 
    try:
        match = re.search(r'\d+', cfg['filter_age'].text())
    except:
        match = re.search(r'\d+', cfg.get('filter_age', '0'))
    if match:
        min_age = float(match.group())
    else:
        min_age = 0  
        
    dfinv = dfinv[dfinv['on\nshelf\n(days)'] > min_age]  
    dfinv['common_pn'] = dfinv['Item'].str.extract('(' + pn_fltr +')')
    if len(dfinv.index) > 0:
        dfinv = dfinv.drop(dfinv.index[-1])
    dfinv['Description'] = dfinv['Description'].fillna('')
    dfinv = dfinv.dropna(subset=['common_pn'])
    dfinv['Unit Cost'] = '$' + dfinv['Unit Cost'].round(2).astype('string')
    # dfinv = dfinv[dfinv['Movement?'] == 'No Demand']
    
    # apply the descrip_filter
    if descrip_filter:
        for f in descrip_filter.split('&'):
            dfinv = dfinv[dfinv['Description'].str.contains(f, case=False, regex=True)]
    if descrip_filter and cfg['repeat']:
        for f in descrip_filter.split('&'):
            df = df[df['DESCRIPTION'].str.contains(f, case=False, regex=True)]   
    ####################################################################################
    ##### merge df & dfinv                                                         #####
    ####################################################################################    
    df = df.merge(dfinv, on='common_pn', how='inner')
    df = df.drop('common_pn', axis=1)
    
    alter_score = [(r'S/S|[^A-Z]SS[^A-Z]|304|316|STAINLESS|LSS|SST', .2),
                              (r'NEMA 7|N7', .2), (r'24V', .2), (r'125V|120V|115V|110V|100V', .2)]
      
    ####################################################################################
    ##### Finish up                                                                #####
    ####################################################################################
    
    # similarity_score is based on what the module SequenceMatcher produces.  However
    # I want the score reduced more if, for example, the "description" is SS and
    # "Description" is not SS.  In this case, reduce similarity_score by %20.
    # The variable 'alter_score' looks for these adjustments.    
    alter_score = [(r'S/S|[^A-Z]SS[^A-Z]|304|316|STAINLESS|LSS|SST|[^A-Z]SS$', .2),
                              (r'NEMA 7|N7', .2), (r'24\s*V', .2), (r'1[0-2][0-5]\s*V', .2),
                              (r'230/460\s*V|230\s*V|460\s*V', .2), (r'575\s*V', .2), (r'200\s*V', .2)] 
    
    df['DESCRIPTION'] = df['DESCRIPTION'].replace(0, 'missing description')
    
    similarity_score = df.apply(lambda row: SequenceMatcher(None, row['DESCRIPTION'], row['Description']).ratio(), axis=1) 

    if len(similarity_score.index) > 0:
        for alter in alter_score:
            similarity_score = similarity_score.where(~(df['DESCRIPTION'].str.contains(alter[0],case=False, regex=True) &
                                          ~df['Description'].str.contains(alter[0], case=False, regex=True)),
    										  similarity_score*alter[1])
    # If someone enters a percent character, %, when indicating the min similarity he wishes
    # to see, for example 86%, the % chacter will crash the program.  So this program will
    # fix the problem by extracting the number, i.e. 86, from the text, i.e. 86%

    try:
        match = re.search(r'\d+', cfg['similar'].text())
    except:
        match = re.search(r'\d+', cfg['similar'])
    if match:
        min_similarity = float(match.group())
    else:
        min_similarity = 0    
        
    if len(similarity_score.index) > 0:
        similarity_bool = similarity_score*100 > min_similarity
        df['descr\nsimi-\nlarity'] = (similarity_score*100).round().astype(int)
        df = df[similarity_bool]
    else:
        df['descr\nsimi-\nlarity'] = 0
        
    # if leading or trailing spaces differ, for example, between a text
    # in one descrip and another, then the df.drop_duplicates() won't work
    # to catch the duplicate line.
    for col in ['PN', 'DESCRIPTION', 'Item', 'Description']:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()
    
    df = df.drop_duplicates()
    df.sort_values(by=['PN', 'descr\nsimi-\nlarity'], ascending=[True, False], kind='mergesort', inplace=True)
    df['descr\nsimi-\nlarity'] = df['descr\nsimi-\nlarity'].astype('string') + '%'
      
    df = df.rename(columns={'Item': 'alt pn'})
    
    
    df.rename(columns={'QTYnSW/SL' : qty_col_name}, inplace=True)
    df = df.set_index(['PN', 'DESCRIPTION', qty_col_name,  'COST', 'alt pn']) #.sort_index(axis=0)

    df['alt\nqty\nused'] = '' 
       
    if 'De-\nmand?' in df.columns:
        new_column_order = ['Description',
                            'descr\nsimi-\nlarity', 'On\nHand', 'Unit Cost', 'Yr n-1\nUsage', 'Yr n-2\nUsage', 
                            'Last Used\n(Days)', 'on\nshelf\n(days)', 'De-\nmand?', 'alt\nqty\nused']                                
    else:
        new_column_order = ['Description',
                            'descr\nsimi-\nlarity', 'On\nHand', 'Unit Cost', 'Yr n-1\nUsage', 'Yr n-2\nUsage',
                            'Last Used\n(Days)', 'on\nshelf\n(days)', 'alt\nqty\nused']     
    df = df[new_column_order]
    df = df.rename(columns={'Description': 'alt description', 'Unit Cost':'cost', 'On\nHand': 'on\nhand',
                            'Yr n-1\nUsage': 'yr\nn-1\nusage', 'Yr n-2\nUsage': 'yr\nn-2\nusage',
                            'Last Used\n(Days)' : 'last\nused\n(days)'})   
    
    return df
    

def is_in(find, series, xcept):
    '''Argument "find" is a list of strings that are glob
    expressions.  The Pandas Series "series" will be
    evaluated to see if any members of find exists as
    substrings within each member of series.  Glob
    expressions are strings like '3086-*-025' or *2020*.
    '3086-*-025' for example will match'3086-0050-025'
    and '3086-0215-025'.

    The output of the is_in function is a Pandas Series.
    Each member of the Series is True or False depending on
    whether a substring has been found or not.

    xcept is a list of exceptions to those in the find list.
    For example, if '3086-*-025' is in the find list and
    '3086-3*-025' is in the xcept list, then series members
    like '3086-0515-025' or '3086-0560-025' will return a
    True, and '3086-3050-025' or '3086-3060-025' will
    return a False.

    For reference, glob expressions are explained at:
    https://en.wikipedia.org/wiki/Glob_(programming)

    Parmeters
    =========

    find: string or list of strings
        Items to search for

    series:  Pandas Series
        Series to search

    xcept: string or list of strings
        Exceptions to items to search for

    Returns
    =======

    out: Pandas Series, dtype: bool
        Each item is True or False depending on whether a
        match was found or not
    '''
    if not isinstance(find, list):
        find = [find]
    if not isinstance(xcept, list) and xcept:
        xcept = [xcept]
    elif isinstance(xcept, list):
        pass
    else:
        xcept = []
    series = series.astype(str).str.strip()  # ensure that all elements are strings & strip whitespace from ends
    find2 = []
    for f in find:
        find2.append('^' + fnmatch.translate(str(f)) + '$')  # reinterpret user input with a regex expression
    xcept2 = []
    for x in xcept:  # exceptions is also a global variable
        xcept2.append('^' +  fnmatch.translate(str(x))  + '$')
    if find2 and xcept2:
        filtr = (series.str.contains('|'.join(find2)) &  ~series.str.contains('|'.join(xcept2)))
    elif find2:
        filtr = series.str.contains('|'.join(find2))
    else:
        filtr = pd.Series([False]*series.size)
    return filtr


def convert_file_list(fl, Qcolname,  cfg):
        '''
        convert files_list[0] (from SW) or files_list[1] (from SL) to a single
        dataframe containing (hopefully) only part numbers and not assembly
        numbers.  files_list is a list with the structure looking like:
            
        files_list = [   
           [{'assembly_sw1':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': [], 'Length' : []})},
            {'assembly_sw2':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': [], 'Length' : []})},
             ...
            {'assembly_swN':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': [], 'Length' : []})}],
            
            [{'assembly_sl1':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': [], 'Length' : []})},
             {'assembly_sl2':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': [], 'Length' : []})},
              ...
             {'assembly_slN':  pd.DataFrame({'Part Number': [], 'QTY': [], 'Description': [], 'Length' : []})}]
            ]
        
        So, fl = files_list[0] or fl = files_list[1]
        (The empty lists, [], shown above will be filled with data.)
        
        Parameters
        ----------
        fl : list
            Either files_list[0] (from SW) or files_list[1] (from SL)
        Qcolname : string
            Name to be assigned to the column that shows part quantities
        cfg : dictionary
            cfg is a dictionary generated by bomcheck.py's set_globals function.
            It defines optional column names in case other names exists in the boms
            that are submitted.  

        Returns
        -------
        Pandas dataframe
            Dataframe will have column names 'PN', 'DESCRIPTION', and Qcolname.
            Quanties of parts that have the same part number are summed. If a 
            length column exists (SW may have this column), the length is 
            multiplied by the quantity and then devided by 12 (12 to convert 
            inches to feet).
            
        '''
        df = pd.DataFrame({'PN': [], 'DESCRIPTION':[], 'QTY\nSW/SL':[]})
        #df = pd.DataFrame()
        assynos = []
        for k, v in fl.items():
           dfi = v.copy()
           values = dict.fromkeys(cfg['part_num'], 'PN')                # make sure pns headers are all "PN"
           values.update(dict.fromkeys(cfg['descrip'], 'DESCRIPTION'))  #           descrip             "DESCRIPTION"
           values.update(dict.fromkeys(cfg['length_sw'], 'LENGTH'))     #           length              "LENGTH"
           values.update(dict.fromkeys(cfg['qty'], Qcolname))           #           qty                 Qcolname
           dfi.rename(columns=values, inplace=True)                     # now rename column headers
           if 'LENGTH' in dfi.columns:
               #dfi['LENGTH'] = dfi['LENGTH'].fillna('0.0')
               dfi['LENGTH'] = dfi['LENGTH'].astype(str)  # the line just below needs a string to work with.
               dfi_extract = dfi['LENGTH'].str.extract(r'(\W*)([\d.]*)\s*([\w\^]*)') # e.g. '34.4 ft^2' > '' '34.4' 'ft^2', or '$34.4' > '$' '34.4' ''    
               dfi['LENGTH'] = pd.to_numeric(dfi_extract[1], errors='coerce').fillna(0.0) # set the no. to a strings
               dfi.loc[dfi['PN'].str.contains('3086-'), 'LENGTH'] = 0.0 # nipple pn's sometimes show a length in the length column.  Ignore it.
               dfi['LENGTH'] = dfi['LENGTH'] /12    # 0.0 / 12 = 0.0
               dfi['LENGTH'] = dfi['LENGTH'].replace(0.0, 1.0)  # df[Qcolname] = df[Qcolname] x 1.0 (needed for next line below)
               dfi[Qcolname] = pd.to_numeric(dfi[Qcolname], errors='coerce').fillna(0.0)
               dfi[Qcolname] = dfi[Qcolname].astype(float) * dfi['LENGTH']
           dfi = dfi[['PN', 'DESCRIPTION', Qcolname]]
           try:
               dfi = dfi.loc[:, ~dfi.columns.duplicated(keep='first')]
               df = pd.concat([df, dfi]) 
           except:
               pass
           assynos.append(k)
        try:
            df[Qcolname] = df[Qcolname].astype(float)
            df = df.groupby(['PN', 'DESCRIPTION'], as_index=False).sum()  # sum quantities of parts with the same part no.
            exclude_series = pd.Series(assynos)
            df = df[~df['PN'].isin(exclude_series)]  # exclude any found assembly pns
        except:
            pass #df[Qcolname] = 0.0
        
        
        return df   
    

def convert_files_list(files_list, cfg):
    '''
    Employ the convert_file_list function to pull out part quantities from
    files_list, and then manipulate that data to create a new column in the 
    dataframe that this function outputs.  It shows quantities: 'QTY\nSW/SL'

    Parameters
    ----------
    files_list : list
        See the docstring in the convert_file_list function. 
    cfg : dictionary
        cfg is a dictionary generated by bomcheck.py's set_globals function.
        It defines optional column names in case other names exists in the boms
        that are submitted.  

    Returns
    -------
    Dataframe
        Dataframe has columns 'PN', 'DESCRIPTION', and 'QTY\nSW/SL',  
    '''
    if files_list[0] and files_list[1]:
        df_sw = convert_file_list(files_list[0], 'QTY_SW', cfg)
        df_sl = convert_file_list(files_list[1], 'QTY_SL', cfg)
        df_sw = df_sw.loc[:, ~df_sw.columns.duplicated(keep='first')]
        df_sl = df_sl.loc[:, ~df_sl.columns.duplicated(keep='first')]
        
        df = df_sw.merge(df_sl, on='PN', how='outer')
        df['DESCRIPTION_x'] = df['DESCRIPTION_x'].fillna(df['DESCRIPTION_y'])
        df = df.drop(columns=['DESCRIPTION_y'])
        df = df.rename(columns={'DESCRIPTION_x': 'DESCRIPTION'})
        df = df.fillna(0.0)
        df['QTY\nSW/SL'] = (df['QTY_SW'].round(0).astype(int).astype(str) + ' / ' + 
                            df['QTY_SL'].round(0).astype(int).astype(str))
        df = df.drop(columns=['QTY_SW', 'QTY_SL'])   
    elif files_list[0]:
        df = convert_file_list(files_list[0], 'QTY\nSW/SL', cfg)
        df['QTY\nSW/SL'] = df['QTY\nSW/SL'].round(0).astype(int).astype(str) + ' \ 0'
    else:
        try:
            df = convert_file_list(files_list[1], 'QTY\nSW/SL', cfg)
            df['QTY\nSW/SL'] = '0 \ ' + df['QTY\nSW/SL'].round(0).astype(int).astype(str)
        except:
            df = pd.DataFrame({'PN': ['0000-0000-000'], 'DESCRIPTION':['NA'], 'QTY\nSW/SL':['0.0']})
    df = df.sort_values(by='PN') 
    df = df[df['QTY\nSW/SL']!='0 / 0']  # don't show data if values < .5, e.g. short pipe lengths, small paint qtys, etc.
    return  df









