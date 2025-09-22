#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep  6 15:28:36 2025

@author: Ken Carlton

Allow a comparison of SW/SL parts to those in slow_moving inventory.
This allows possible substitution of slow_moving parts in systems
currently being built so that slow_moving parts can be used up.
"""

import pdb # use with pdb.set_trace()
import pandas as pd
from difflib import SequenceMatcher

def check_sm_parts(files_list, sm_files, cfg):
    ''' Collect part numbers and their descriptions that come from SolidWorks
    and SyteLine.  Compare the part numbers to those from a list of slow_moving
    parts to see if any of the slow_moving parts can be substituted.

    Parameters
    ----------
    files_list : list
        This list of two dictionaries that bomcheck.py supplies.
        It has the form:
        [{assembly_pn1: df1, assembly_pn2: df2, ..., assembly_pnN: dfN},
         {assembly_pn1: df1, assembly_pn2: df2, ..., assembly_pnN: dfN}]
        Where the first dictionary comes from SyteLine; the second from
        SolidWorks.  The df1, df2, etc. are the BOMs in DataFrame form
        that correspond to the assembly_pn.  The function discards the
        assembly part numbers.

    cfg : dictionary
        cfg is comes from bomcheck.py and is the exact same dictionary that
        is in bomcheck.py.  cfg provides alternative header names that the
        BOMs might have, such as "Material", "PARTNUMBER", "PART NUMBER",
        "Part Number", "Item"; and "DESCRIPTION", "Material Description", and
        "Description".  With these alternative names, this check_sm_parts
        function figures out what the correct headers should be for the part
        no. and descriptions fields.

    pn_fltr : string
        Part no. filter.  Normally will be assigned a value like '....-....-'.
        With this, part numbers 4610-2008-203, 5500-0025-001, and 6220-0055-004
        will be reduced to 4610-2008-, 5500-0025-, and 6220-0055-.  This
        reduction occurs in both the SW/SL BOMs and the slow_moving BOM.
        The shortened part nos. will be used for matching between BOM.  This
        will result in, for example 4610-2008-203 finding the closest matching
        parts from the slow_moving BOM to be 4610-2008-198, 4610-2008-199,
        4610-2008-200, etc..

        The string is a regex string
        (https://en.wikipedia.org/wiki/Regular_expression).  The dot, .,
        represents one character.  Other suitable values for pn_filtr could be
        '.{10}', '.+-.+-'.  (.{10} means ten characters.  The .+ means one or
        more characters)

    descrip_filter : string, optional
        This filters the 'Item Description' field of the slow moving BOM.
        Only parts who's descriptions that are able to pass through this filter
        will show up in the results of this check_sm_parts function.

        The string is a regex string.  Furthermore the string allows for "or"
        and "and" types of filtering.  For example if you want to reduce
        the parts shown to only stainless steel parts that are Nema 7, you
        could use the filter 'S/S| SS|316|304&N7|NEMA 7'  This means
        '(SS or 316 or 304) and (N7 or NEMA 7)'.  The bar, !, represents "or".
        The ampersand character, &, represents "and".  Note: spaces count.
        Thus 'SS|316|304&N7|NEMA 7' is different from 'SS|316|304& N7 | NEMA 7'

        The default is ''.

    Returns
    -------
    DataFrame

    Only the union of the SW/SL BOMs and the slow_moving BOM is output.  All
    other part nos. are discarded.  Only needed columns are output.  Needed
    colums are the part no. and descritpion fields of the SW/SL BOMs and the
    slow_moving BOM, and the Age field of the slow_moving use BOM.
    '''
    # extract from "cfg" args from the user.
    pn_fltr = cfg['filter_pn'].text()
    descrip_filter = cfg['filter_descrip'].text() if cfg['filter_descrip'] else ''

    ##### create df and populate it  df is a collection of BOMs from SW & SL
    df = pd.DataFrame() # start with an empty DataFrame
    for f in files_list:
        for k, v in f.items():
            dfi = v.copy()
            values = dict.fromkeys(cfg['part_num'], 'pn sw/sl')   # make sure pns headers are all the same: pn
            values.update(dict.fromkeys(cfg['descrip'], 'descrip sw/sl'))  # make sure descrip headers all the same: descrip
            dfi.rename(columns=values, inplace=True)   # rename appropriate column headers to "pn" and "descrip"
            if 'cost' in dfi.columns:
                dfi = dfi[['pn sw/sl', 'descrip sw/sl', 'cost']]   # delete all columns but "pn", "descrip"
            else:
                dfi = dfi[['pn sw/sl', 'descrip sw/sl']]
            df = pd.concat([df, dfi])
    df.sort_values(by='pn sw/sl', ascending=True, inplace=True)
    df.drop_duplicates(subset=['pn sw/sl'], keep='first')
    df['common_pn'] = df['pn sw/sl'].str.extract('(' + pn_fltr +')')  # apply the pn_fltr

    # dfinv is the dataframe derived from the excel sheet of slow_moving parts
    dfinv = pd.DataFrame()  # start with an empty DataFrame
    for k, v in sm_files.items():
        dfinv = pd.concat([dfinv, v])
    dfinv.sort_values(by='Description', ascending=True, inplace=True)
    dfinv['common_pn'] = dfinv['Item'].str.extract('(' + pn_fltr +')')
    dfinv = dfinv.drop(dfinv.index[-1])
    dfinv['Description'] = dfinv['Description'].fillna('')
    dfinv = dfinv.dropna(subset=['common_pn'])
    dfinv['Unit Cost'] = dfinv['Unit Cost'].astype(int)

    # apply the descrip_filter
    if descrip_filter:
        for f in descrip_filter.split('&'):
            dfinv = dfinv[dfinv['Description'].str.contains(f, case=False, regex=True)]
    if descrip_filter and cfg['repeat']:
        for f in descrip_filter.split('&'):
            df = df[df['descrip sw/sl'].str.contains(f, case=False, regex=True)]
            
    ##### merge df & dfinv
    df = df.merge(dfinv, on='common_pn', how=cfg['merge'])
    df = df.drop('common_pn', axis=1)
    
    if float(cfg['similarity'].text()) > .5:
        similarity_score = df.apply(lambda row: SequenceMatcher(None, row['descrip sw/sl'], row['Description']).ratio(), axis=1) 
        similarity_bool = similarity_score*100 > float(cfg['similarity'].text())
        df['similarity'] = (similarity_score*100).round().astype(int).astype('string') + '%'
        #df['similarity'] = (similarity_score*100).astype(int).to_string().str.cat('%')
        df = df[similarity_bool]



    # if leading or trailing spaces differ, for example, between a text
    # in one descrip and another, then the df.drop_duplicates() won't work
    # to catch the duplicate line.
    for col in ['pn sw/sl', 'descrip sw/sl', 'Item', 'Description']:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()
    df = df.drop_duplicates()

    df.reset_index(drop=True, inplace=True)

    return df


# =============================================================================
#     counts = df['pn'].value_counts()
#     lone_values = counts[counts==1]
#     lone_pns = lone_values.index.do_list()
#     print(lone_values['pn'])
# =============================================================================











