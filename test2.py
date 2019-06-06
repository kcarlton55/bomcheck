#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 21:31:00 2019

@author: ken
"""

def bomcheck(fn, d=False, c=True):
    '''Do BOM checks on a group of Excel files containing BOMs.  Filenames must
    end with _sw.xlsx or _sl.xlsx.  Leading part of file names must match.  For
    example, leading parts of names 0300-2018-797_sw.xlsx and 0300-2018-797_sw.xlsx
    match and a BOM check will be done on them.

    Parmeters
    =========

    fn : string
        filename(s) of Excel files to do a BOM check on.

    v : bool
        verbose on or off (True or False).  Default: False
    
    d : bool
        If True, omit items from the droplist for BOM checking.  The drop list
        is a list of part nos. to disreguard for the bom check.  Default: False.
        See the function "getdroplist" for more info.

    Returns
    =======

    out : Excel file (saved to disk)
        The Excel file show the outputs from the lists title_dfsw and 
        title_dfmerged.  Each object is shown on its own individual Excel
        worksheet.

    Examples
    ========

    >>> bomcheck("078551*")

    >>> bomcheck("C:\\pathtomyfile\\6890-*")

    >>> bomcheck("*")
    
    Only a directory name specified.  Implies "*" for that directory:
    
    >>> bomcheck("C:\\pathtomyfile")  # only a directory name specified.  Implies '*" for that directory:

    \u2009
    '''
    if os.path.isdir(fn):
        fn = os.path.join(fn, '*')
        
    if fn.startswith('[') and fn.endswith(']'):
        fn = eval(fn)
        
    if d:
        print('drop =', drop)
        print('exceptions =', exceptions)
        
    dirname, swfiles, pairedfiles = gatherBOMs(fn)
    
    # lone_sw is a dic.  Keys are assy nos.  Values are DataFrame objects (BOMs)
    # merged_sw2sl is a dic.  Keys are assys nos.  Values are Dataframe objects
    # (merged SW and SL BOMs).    
    lone_sw, merged_sw2sl = combine_tables(swfiles, pairedfiles, d)
    
    title_dfsw = []
    for k, v in lone_sw.items():
        title_dfsw.append((k, v))  # Create a list of tuples: [(title, bom)... ]
        
    title_dfmerged = []
    for k, v in merged_sw2sl.items():
        title_dfmerged.append((k, v))  
        
#############################################
    if c==True:
    	title_dfsw, title_dfmerged = concat(title_dfsw, title_dfmerged) 
        
    print('aaa')
    print(title_dfmerged)    

#############################################  
   
    try:    
        export2excel(dirname, 'bomcheck', title_dfsw + title_dfmerged)
    except PermissionError:
        print('\nError: unable to write to bomcheck.xlsx')
        
        
# https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html

def concat(title_dfsw, title_dfmerged):
    ''' Concatenate all the SW BOMs into one long list, and concatenate all the
    merged BOMs into another long list.  Each BOM, before concatenation, has a
    new column added titled "assy".  Values of "assy" are strings and are the 
    same for a given BOM.  The string value is the assy no. for the BOM.  After
    concatenation, Pandas groupby function is employed on the long list 
    resulting in a nice looking output; the assy no. appears to the left of the 
    BOM.

    Parameters
    ==========

    title_dfsw : list
        A list of tuples, each tuple has two items: a string and a DataFrame.
        The string is the assy no. for the DataFrame.  The DataFrame is that
        derived from a SW BOM.

    title_dfmerged : list
        A list of tuples, each tuple has two items: a string and a DataFrame.
        The string is the assy no. for the DataFrame.  The DataFrame is that
        derived from merged SW and SL BOMs.  

    Returns
    =======

    out : tuple
        The tuple has two items and is of the form:
        
        (('SW BOMs', all-SW-BOMs), ('Merged BOMs', all-merged-BOMs)

        Where the all-SW-BOMs and the all-merged-BOMs are Pandas DataFrame
        objects.

    ''' 
    dfswGrpBy = False
    dfmergedGrpBy = False
    dfswDFrames = []
    dfmergedDFrames = []
    for t in title_dfsw:
        t[1]['assy'] = t[0]
        dfswDFrames.append(t[1])
    for t in title_dfmerged:
        t[1]['assy'] = t[0]
        dfmergedDFrames.append(t[1])
    if dfswDFrames:
        dfswConcatenated = pd.concat(dfswDFrames)
        dfswGrpBy = dfswConcatenated.groupby(['assy']).apply()
    if dfmergedDFrames:
        dfmergedConcatenated = pd.concat(dfmergedDFrames)  
        dfmergedGrpBy = dfmergedConcatenated.groupby(['assy']).apply()
    if dfswGrpBy and not dfmergedGrpBy:
        return [('SW BOMs', dfswGrpBy)], []
    elif dfswGrpBy and dfmergedGrpBy:
        return [('SW BOMs', dfswGrpBy)], [('Merged BOMs', dfmergedGrpBy)]
    elif dfmergedGrpBy:
        return [], [('Merged BOMs', dfmergedGrpBy)]
    else:
        return [], []
        

