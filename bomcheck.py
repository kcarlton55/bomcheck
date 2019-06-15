#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File initial creation on Sun Nov 18 2018

@author: Kenneth Carlton

This program compares two BOMs: one originating from SolidWorks (SW) and the 
other from SyteLine (SL).  The structure of the BOMs (headings, structure, 
etc.) are very unique to our company.  Therefore this program, unaltered, will
fail to function at another company. 

Run from the command line like this: python bomcheck.py '*'

Run without any arguments shows help info about the program: python bomcheck.py

Run from a python console terminal like this: bomcheck('*')

To see how to create an EXE file from this program, see the file named
howtocompile.md. 
"""


__version__ = '1.0.6'
__author__ = 'Kenneth Carlton'
import glob, argparse, sys, warnings
import pandas as pd
import os.path
import os
import tempfile
import re
import datetime
import itertools
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)


def get_version():
    return __version__


def getdroplist():
    ''' Create two global python lists named drop and exceptions.  Make these
    lists global thus allowing easy access to other functions (specifically to
    sw).  These lists are derived from the file named droplists.py.  The drop 
    list contains pns of off-the-shelf parts, like bolts and pipe nipples, that
    are to be excluded from the bom check.
    
    Returns
    =======
    
    out : None
        If droplists.py not found set drop=['3*-025'] and exceptions=[]
    '''
    global drop, exceptions
    usrPrf = os.getenv('USERPROFILE')  # on my win computer, USERPROFILE = C:\Users\k_carlton
    if usrPrf:    
        userDocDir = os.path.join(usrPrf, 'Documents')
    else:
        userDocDir = "C:/"
    paths = [userDocDir, "/home/ken/projects/project1/"]
    for p in paths:
        if os.path.exists(p) and not p in sys.path:
            sys.path.append(p)
            break
    else:
        print('At function "getdroplist", a suitable path was not found to\n'
              'load droplist.py from.')
    try:
        import droplist
        drop = droplist.drop
        exceptions = droplist.exceptions
    except ModuleNotFoundError:
        drop = ['3*-025']   # If droplist.py not found, use this
        exceptions= []
        
        
getdroplist()       # create global variables named drop and exceptions


def main():
    '''This fuction allows this bomcheck.py program to be run from the command
    line.  It is started automatically (via the "if __name__=='__main__'"
    command at the bottom of this file) when bomecheck.py is run from the
    command line.
    
    calls: bomcheck

    Examples
    ========

    $ python bomcheck.py "078551*"

    $ python bomcheck.py "C:\\pathtomyfile\\6890-*"

    $ python bomcheck.py "*"

    $ python bomcheck.py --help

    \u2009
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                        description='Program compares SolidWorks BOMs to SyteLine BOMs.  ' +
                        'Output is sent to a Microsoft Excel spreadsheet.')
    parser.add_argument('filename', help='Name of file containing a BOM.  Name ' +
                        'must end with _sw.xlsx, _sl.xlsx. _sw.csv, or ' +
                        '_sl.csv.  Enclose filename in quotes!  An asterisk, *, ' +
                        'caputures multiple files.  Examples: "6890-*", "*".  ' +
                        'Or if filename is a directory path, all _sw and _sl files ' +
                        'will be gathered from that directory.  ' +
                        '_sl files without a corresponding _sw file are ignored.')
    parser.add_argument('-d', '--drop', action='store_true', default=False,
                        help='Ignore 3*-025 pns, i.e. do not use in the bom check')
    parser.add_argument('-c', '--concatenate', action='store_true', default=False,
                        help='Concatenate the output into one long list of BOMs ')
    parser.add_argument('-v', '--version', action='version', version=__version__,
                        help="Show program's version number and exit")            
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()  
    bomcheck(args.filename, args.drop, args.concatenate) 


def bomcheck(fn, d=False, c=False):
    ''' This function is the hub of the bomcheck program.  It calls upon other
    fuctions that act to open Excel files or csv files containing containing 
    BOMs.  Filenames must end with _sw.xlsx, _sl.xlsx, sw.csv, or sl.csv.  
    Leading part of file names must match.  For example, leading parts of names
    0300-2018-797_sw.xlsx and 0300-2018-797_sw.xlsx match and a BOM check will
    be done on them.  If a _sw file found for which not _sl file file found, 
    transform the _sw file to a SyteLine like format.  If a _sl file found with
    no matching _sw file found, the _sl file is ignoreed; that is, it is not 
    used an any computation.  SW and SL BOMs are then merged thus showing a
    checked BOM.  Finally results are exported to an MS Excel file.
    
    calls: gatherBOMs, combine_tables, concat, export2excel

    Parmeters
    =========

    fn : string
        filename(s) of Excel files to do a BOM check on.

    c : bool
        concatenate data that is sent to the ouput Excel file.  Default: False
    
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

    >>> bomcheck("*")   # all files in the current working directory are evaluated
    
    Only a directory name specified.  Implies "*" for that directory:
    
    >>> bomcheck("C:\\pathtomyfile")  # only a directory name specified.  Implies "*" for that directory:

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
        title_dfsw.append((k, v))  # Create a list of tuples: [(title, swbom)... ]
        
    title_dfmerged = []
    for k, v in merged_sw2sl.items():
        title_dfmerged.append((k, v))  # Create a list of tuples: [(title, mergedbom)... ]
        
    if c==True:
    	title_dfsw, title_dfmerged = concat(title_dfsw, title_dfmerged) 
   
    try:    
        export2excel(dirname, 'bomcheck', title_dfsw + title_dfmerged)
    except PermissionError:
        print('\nError: unable to write to bomcheck.xlsx')
        
        
def gatherBOMs(filename):
    ''' Gather all SolidWorks and SyteLine BOMs derived from "filename".
    "filename" can be a string containing wildcards, e.g. 6890-085555-*, which
    allows the capture of multiple files; or "filename" can be a list of such 
    strings.  These files (BOMs) will be converted to Pandas DataFrame objects.
    
    Only files prefixed with _sw.xlsx, _sw.csv, _sl.xlsx, or _sl.csv will be
    chosen.  These files will then be converted to two python dictionaries.  
    One dictionary will contain SolidWorks BOMs only.  The other will contain
    only SyteLine BOMs.  The dictionary keys (i.e., "handles" allowing access
    to each BOM) will be the part numbers of the BOMs.
    
    If a filename corresponds to a BOM containing a multiple level BOM, then
    that BOM will be broken down to subassemblies and will be added to the
    dictionaries.
    
    calls: fixcsv, multilevelbom, missing_columns 
    
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
        if file_extension.lower() == '.csv':
            data = fixcsv(v)
            temp = tempfile.TemporaryFile(mode='w+t')
            for d in data:
                temp.write(d)
            temp.seek(0)
            df = pd.read_csv(temp, na_values=[' '], skiprows=1, sep='$',
                                   encoding='iso8859_1', engine='python',
                                   dtype = {'ITEM NO.': 'str'})
            temp.close()
        elif file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
            df = pd.read_excel(v, na_values=[' '], skiprows=1)
        if not missing_columns('sw', df, k):
            swdfsdic.update(multilevelbom(df, k))
    sldfsdic = {}
    for k, v in slfilesdic.items(): 
        _, file_extension = os.path.splitext(v)
        if file_extension.lower() == '.csv':
            df = pd.read_csv(v, na_values=[' '], engine='python',
                             encoding='utf-16', sep='\t')
        elif file_extension.lower() == '.xlsx' or file_extension.lower == '.xls':
            df = pd.read_excel(v, na_values=[' '])
        if not missing_columns('sl', df, k):
            sldfsdic.update(multilevelbom(df, k))
    try:     
        df = pd.read_clipboard(engine='python', na_values=[' '])
        if not missing_columns('sl', df, 'BOMfromClipboard', printerror=False):
            sldfsdic.update(multilevelbom(df, 'TOPLEVEL')) 
    except:
        pass
    dirname = os.path.dirname(filename[0])
    if dirname and not os.path.exists(dirname):
        print('directory not found: ', dirname)
        sys.exit(0)
    return dirname, swdfsdic, sldfsdic


def fixcsv(filename):
    '''fixcsv is called upon when a SW csv file is employed.  Why?  SW csv
    files use a comma (,) as a delimiter.  Commas, on rare  occasions, are used
    within a part's description.  This extra comma(s) causes the program to 
    crash. To alleviate the problem, this function switches the comma (,) 
    delimited format to a dollar sign ($) as a delimiter, but leaves any commas
    in place within the part's DESCRIPTION field.  A $ character is used
    because it is nowhere used in a part's description.
    
    Parmeters
    =========

    filename : string
        Name of SolidWorks csv file to process.
        
    Returns
    =======
    
    out : list
        A list of all the lines (rows) in filename.  Commas in each line are 
        changed to semicolons.  However any commas in the DESCRIPTION field
        stay commas.
    '''
    with open(filename, encoding="ISO-8859-1") as f:
        data1 = f.readlines()
    # n1 = number of commas in 2nd line of filename (i.e. where column header
    #      names located).  This is the no. of commas that should be in each row.
    n1 = data1[1].count(',')
    n2 = data1[1].upper().find('DESCRIPTION')  # locaton of the word DESCRIPTION within the row.
    n3 = data1[1][:n2].count(',')  # number of commas before the word DESCRIPTION 
    data2 = list(map(lambda x: x.replace(',', '$') , data1)) # replace ALL commas with $
    data = []
    for row in data2:
        n4 = row.count('$')
        if n4 != n1:
            # n5 = location of 1st ; character within the DESCRIPTION field 
            #      that should be a , character
            n5 = row.replace('$', '?', n3).find('$')
            # replace those ; chars that should be , chars in the DESCRIPTION field:
            data.append(row[:n5] + row[n5:].replace('$', ',', (n4-n1))) # n4-n1: no. commas needed
        else:
            data.append(row)
    return data


def missing_columns(bomtype, df, pn, printerror=True):
    ''' SolidWorks and SyteLine BOMs require certain essential columns to be
    present.  This function looks at those BOMs that are within df to see if
    any required columns are missing.  If found, print to screen.  Finally, 
    return a dictionary like that input less the faulty BOMs.
    
    calls: missing_tuple

    Parameters
    ==========

    bomtype : string
        "sw" or "sl"

    df : Pandas DataFRame
        A SW or SL BOM

    pn : string
        Part number of the BOM   

    Returns
    =======

    out : bool
        True if BOM afoul.  Otherwise False.
    '''
    if bomtype == 'sw':
        required_columns = [('QTY', 'QTY.'), 'DESCRIPTION',
                            ('PART NUMBER', 'PARTNUMBER')]
    else: # 'for sl bom'
        required_columns = [('Qty', 'Quantity', 'Qty Per'), 
                            ('Material Description', 'Description'), 
                            ('U/M', 'UM'), ('Item', 'Material')]
    missing = []
    for r in required_columns:
        if isinstance(r, str) and r not in df.columns:
            missing.append(r)
        elif isinstance(r, tuple) and missing_tuple(r, df.columns):
            missing.append(' or '.join(missing_tuple(r, df.columns)))
    if missing and bomtype=='sw' and printerror:
        print('\nEssential BOM columns missing.  SolidWorks requires a BOM header\n' +
              'to be in place.  Is this missing?  This BOM will not be processed.\n\n' +
              '    missing: ' + ' ,'.join(missing) +  '\n' +    
              '    missing in: ' + pn)
        return True
    elif missing and printerror:
        print('\nEssential BOM columns missing.  This BOM will not be processed.\n' +
             '    missing: ' + ' ,'.join(missing) +  '\n\n' +    
             '    missing in: ' + pn)
        return True
    elif missing:
        return True
    else:
        return False


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
    

def multilevelbom(df, top='TOPLEVEL'):
    ''' If the BOM is a multilevel BOM, pull out the components thereof; that
    is, pull out the main assembly and the subassemblies thereof.  These 
    assys/subassys are  placed in a python dictionary and returned.

    Parmeters
    =========

    df : Pandas DataFrame
        The DataFrame is that of a SolidWorks or SyteLine BOM.
        
    top : string
        If df is derived from a file such as 082009_sw.xlsx, "top" should be
        assigned for "082009" since the top level part number is not given in 
        the Excel file and therefore can't be derived from the file.  This is
        also true for a single level Syteline BOM.  On the other hand a 
        mulilevel SyteLine BOM, which has a column named "Level", has the top
        level pn contained within (assigned at "Level" 0).  In this case use 
        the default "TOPLEVEL".
        
    Returns
    =======
    
    out : python dictionary
        The dictionary has the form {assypn1: BOM1, assypn2: BOM2, ...}.
        Where assypn is a string object and is the part number of a BOM.
        All BOMs are pandas DataFrame objects.
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
    if 'Level' in df.columns:  # if present, is a SL BOM.  Make sure top='TOPLEVEL'
        top = 'TOPLEVEL'
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


def combine_tables(swdic, sldic, d=False):
    ''' Match SolidWorks assembly nos. to those from SyteLine and then merge
    their BOMs to create a BOM check.  For any SolidWorks BOMs for which no
    SyteLine BOM was found, put those in a separate dictionary for output.
    
    calls: sw, sl

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
        
    d : bool
        A boolean to pass along to the sw function.  If true, employ the
        drop list.

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
    for key, dfsw in swdic.items():
        if key in sldic:
            combined_dic[key] = sl(sw(dfsw, d), sldic[key])
        else:
            lone_sw_dic[key + '_sw'] = sw(dfsw, d)
    return lone_sw_dic, combined_dic
        
        
def sw(df, d=False):
    '''Take a SolidWorks BOM and restructure it to be like that of a SyteLine
    BOM.  That is, the following is done:

    - For parts with a length provided (a LENGTH column), the length is 
      converted from inches to feet.  (SyteLine BOMs have lengths in feet)
    - If the part is a pipe or beam and it is listed multiple times in the BOM,
      the BOM is updated so that the part is shown only once.  The length is 
      converted to the sum of the lengths of the multiple parts.
    - (If d=True) Any pipe fittings that start with "3" and end with "025" are 
      off-the-shelf parts.  They are removed from the SolidWorks bom.  (As a
      general rule, off-the-shelf parts are not shown on SyteLine BOMs.)  The
      list that governs this rule is in a file named drop.py.  Therefore other
      part nos. may be added to this list if required.  (see getdroplist)
    - Many times part nos. for pipe nipples show more than once in a SW BOM.
      If this occurs the BOM is updated so that the nipple part no. shows only 
      once.  The quantity is updated accordingly for this nipple.
    - Column titles are changed to match those of SyteLine, thus allowing
      merging to a SyteLing BOM.

    Parmeters
    =========

    df : Pandas DataFrame
        SolidWorks DataFrame object to process.

    d : bool
        If d True, ignore items from droplist.  (See getdroplist).
        Default: False
    
    Returns
    =======

    out : pandas DataFrame
        A SolidWorks BOM with a structure like that of SyteLine.

    \u2009
    '''
    # if LENGTH value a string, e.g., 32.5" instead of 32.5, convert to a float: 32.5
    # the 'extract(r"([-+]?\d*\.\d+|\d+)")' pulls out a number from a string
    if 'LENGTH' in df.columns and df['LENGTH'].dtype == object:
        df['LENGTH'] = df['LENGTH'].str.extract(r"([-+]?\d*\.\d+|\d+)")
        df['LENGTH'] = df['LENGTH'].astype(float)
    values = {'QTY':0, 'QTY.':0, 'LENGTH':0, 'DESCRIPTION': 'description missing',
              'PART NUMBER': 'pn missing', 'PARTNUMBER': 'pn missing'} 
    df.fillna(value=values, inplace=True)
    # obsolete: df['DESCRIPTION'].replace(0, '!! No SW description provided !!', inplace=True)
    df['DESCRIPTION'] = df['DESCRIPTION'].apply(lambda x: x.replace('\n', ''))  # get rid of "new line" character
    df.rename(columns={'PARTNUMBER':'Item', 'PART NUMBER':'Item', 'L': 'LENGTH',
                       'DESCRIPTION': 'Description', 'QTY': 'Q', 'QTY.': 'Q',}, inplace=True)
    filtr1 = df['Item'].str.startswith('3086')  # filter pipe nipples (i.e. pn starting with 3086)
    try:       # if no LENGTH in the table, an error occurs. "try" causes following lines to be passed over
        df['LENGTH'] = (df['Q'] * df['LENGTH'] * ~filtr1) /12.0  # covert lenghts to feet. ~ = NOT
        filtr2 = df['LENGTH'] >= 0.00001  # a filter: only items where length greater than 0.0
        df['Q'] = df['Q']*(~filtr2) + df['LENGTH']  # move lengths (in feet) to the Qty column
        df['U'] = filtr2.apply(lambda x: 'FT' if x else 'EA')
    except:
        df['U'] = 'EA'
    df = df.reindex(['Op', 'WC','Item', 'Q', 'Description', 'U'], axis=1)  # rename and/or remove columns
    dd = {'Q': 'sum', 'Description': 'first', 'U': 'first'}   # funtions to apply to next line
    df = df.groupby('Item', as_index=False).aggregate(dd).reindex(columns=df.columns)
    df['Q'] = round(df['Q'], 2)
    
    if d==True:
        drop2 = []
        for d in drop:  # drop is a global varialbe: pns to exclude from the bom check
            d = '^' + d + '$'
            drop2.append(d.replace('*', '[A-Za-z0-9-]*'))    
        exceptions2 = []
        for e in exceptions:  # exceptions is also a global variable
            e = '^' + e + '$'
            exceptions2.append(e.replace('*', '[A-Za-z0-9-]*'))
        if drop2 and exceptions2:
            filtr3 = df['Item'].str.contains('|'.join(drop2)) & ~df['Item'].str.contains('|'.join(exceptions2))
            df.drop(df[filtr3].index, inplace=True)  # drop frow SW BOM pns in "drop" list.
        elif drop2:
            filtr3 = df['Item'].str.contains('|'.join(drop2))
            df.drop(df[filtr3].index, inplace=True)  # drop frow SW BOM pns in "drop" list.
    
    df['WC'] = 'PICK'
    df['Op'] = str(10)
    df.set_index('Op', inplace=True)

    return df


def sl(dfsw, dfsl):
    '''This function reads in a BOM derived from StyeWorks and then merges it
    with the BOM from SiteLine.  The merged BOMs allow differences to be
    easily seen.

    The first set of columns in the output is labeled i, q, d, and u.  Xs at a
    row in any of these colums indicate something didn't match up between the SW
    and SL BOMs.  An X in the i column means the SW and SL Items (i.e. pns) didn't
    match.  q means quantity, d means description, u means unit of measure.

    Parmeters
    =========

    dfsw: : Pandas DataFrame
        A DataFrame of a SolidWorks BOM
        
    dfsl: : Pandas DataFrame
        A DataFrame of a SyteLine BOM
        
    Returns
    =======

    df_merged : Pandas DataFrame
        df_merged is a DataFrame that shows a side-by-side comparison of a
        SolidWorks BOM to a SyteLine BOM.

    \u2009
    '''
    if not str(type(dfsw))[-11:-2] == 'DataFrame':
        print('Program halted.  A fault with SolidWorks DataFrame occurred.')
        sys.exit()

    # A BOM can be derived from different locations within SL.  From one location
    # the `Item` is the part number.  From another `Material` is the part number.
    # When `Material` is the part number, a useless 'Item' column is also present.
    # It causes the bomcheck program confusion and the program crashes.
    if 'Item' in dfsl.columns and 'Material' in dfsl.columns:
        dfsl.drop(['Item'], axis=1, inplace=True)
    if 'Description' in dfsl.columns and 'Material Description' in dfsl.columns:
        dfsl.drop(['Description'], axis=1, inplace=True)
    dfsl.rename(columns={'Material':'Item', 'Quantity':'Q', 
                         'Material Description':'Description', 'Qty':'Q', 'Qty Per': 'Q',
                         'U/M':'U', 'UM':'U', 'Obsolete Date': 'Obsolete'}, inplace=True)

    if 'Obsolete' in dfsl.columns:
        filtr4 = dfsl['Obsolete'].notnull()
        dfsl.drop(dfsl[filtr4].index, inplace=True)    # https://stackoverflow.com/questions/13851535/how-to-delete-rows-from-a-pandas-dataframe-based-on-a-conditional-expression
        
    dfmerged = pd.merge(dfsw, dfsl, on='Item', how='outer', suffixes=('_sw', '_sl'), indicator=True)
    dfmerged.sort_values(by=['Item'], inplace=True)
    filtrI = dfmerged['_merge'].str.contains('both')  # this filter determines if pn in both SW and SL
    filtrQ = abs(dfmerged['Q_sw'] - dfmerged['Q_sl']) < .0051  # If diff in qty greater than this value, show X
    filtrM = dfmerged['Description_sw'].str.split() == dfmerged['Description_sl'].str.split()
    filtrU = dfmerged['U_sw'].str.strip() == dfmerged['U_sl'].str.strip()
    chkmark = '-'
    err = 'X'
    
    dfmerged['i'] = filtrI.apply(lambda x: chkmark if x else err)     # X = Item not in SW or SL
    dfmerged['q'] = filtrQ.apply(lambda x: chkmark if x else err)     # X = Qty differs btwn SW and SL
    dfmerged['d'] = filtrM.apply(lambda x: chkmark if x else err)     # X = Mtl differs btwn SW & SL
    dfmerged['u'] = filtrU.apply(lambda x: chkmark if x else err)     # X = U differs btwn SW & SL
    dfmerged['i'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['i'] # duplicate in SL? i-> blank
    dfmerged['q'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['q'] # duplicate in SL? q-> blank
    dfmerged['d'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['d'] # duplicate in SL? d-> blank
    dfmerged['u'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['u'] # duplicate in SL? u-> blank
    
    dfmerged = dfmerged[['Item', 'i', 'q', 'd', 'u', 'Q_sw', 'Q_sl', 'Description_sw',
                           'Description_sl', 'U_sw', 'U_sl']]
    dfmerged.fillna('', inplace=True)
    dfmerged.set_index('Item', inplace=True)
    return dfmerged


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
    dfswDFrames = []
    dfmergedDFrames = []
    swresults = []
    mrgresults = []
    for t in title_dfsw:
        t[1]['assy'] = t[0]
        dfswDFrames.append(t[1])
    for t in title_dfmerged:
        t[1]['assy'] = t[0]
        dfmergedDFrames.append(t[1])
    if dfswDFrames:
        dfswCCat = pd.concat(dfswDFrames).reset_index()
        swresults.append(('SW BOMs', dfswCCat.set_index(['assy', 'Op'])))
    if dfmergedDFrames:
        dfmergedCCat = pd.concat(dfmergedDFrames).reset_index() 
        mrgresults.append(('BOM Check', dfmergedCCat.set_index(['assy', 'Item'])))
    return swresults, mrgresults


def export2excel(dirname, filename, results2export):
    '''Export to an Excel file the results of all the bom checks that have
    been done.
    
    calls: len2, autosize_excel_columns, autosize_excel_column_df, definefn
    (these functions defined internally within the export2exel function)

    Parmeters
    =========

    dirname : string
        The directory to which the Excel file that this function generates
        will be sent.

    filename : string
        The name of the Excel file.

    results2export : list
        List of tuples.  Each tuple has two items.  The first item is a string
        and is the title, usually an assembly part number, given to the second
        item.  The second item is a DataFrame object for a BOM.  The list of 
        tuples are:
        
        1. Only SolidWorks BOMs, that have been converted to SyteLine format, 
        if no corresponding SyteLine BOM was found to compare it to; and/or
        
        2.  A list showing a comparison between a SolidWorks BOM and a SyteLine
        BOM.  (i.e., a merged SW/SL BOM)

    Returns
    =======

    out : Excel file (saved to disk)
        The Excel file shows on multiple sheets the "results2export" list.

     \u2009
    '''
    def len2(s):
        ''' Extract from within a string either a decimal number truncated to two
        decimal places, or an int value; then return the length of that substring.
        Why used?  Q_sw, Q_sl, Q, converted to string, are on ocasion something 
        like 3.1799999999999997.  This leads to wrong length calc using len.'''
        match = re.search(r"\d*\.\d\d|\d+", s)
        if match:
            return len(match.group())
        else:
            return 0
    
    def autosize_excel_columns(worksheet, df):
        ''' Adjust column width of an Excel worksheet (ref.: https://stackoverflow.com/questions/
            17326973/is-there-a-way-to-auto-adjust-excel-column-widths-with-pandas-excelwriter)'''
        autosize_excel_columns_df(worksheet, df.index.to_frame())
        autosize_excel_columns_df(worksheet, df, offset=df.index.nlevels)
    
    def autosize_excel_columns_df(worksheet, df, offset=0):
        for idx, col in enumerate(df):
            x = 1 # add a little extra width to the Excel column
            if df.columns[idx] in ['i', 'q', 'd', 'u']:
                x = 0
            series = df[col]
            if df.columns[idx][0] == 'Q':
                max_len = max((  
                    series.astype(str).map(len2).max(),
                    len(str(series.name))
                )) + x
            else:                
                max_len = max((
                    series.astype(str).map(len).max(),
                    len(str(series.name))
                )) + x
            worksheet.set_column(idx+offset, idx+offset, max_len)
            
    def definefn(dirname, filename, i=0):
        '''If bomcheck.xlsx exists, return bomcheck(1).xlsx.  If that exists,
        return bomcheck(2).xlsx.  And so forth.'''
        d, f = os.path.split(filename)
        f, e = os.path.splitext(f)
        if d:
            dirname = d   # if user specified a directory, use it instead
        if e and not e.lower()=='.xlsx':
            print('Output filename extension needs to be .xlsx')
            print('Program aborted.')
            sys.exit(0)
        else:
            e = '.xlsx'        
        if i == 0:
            fn = os.path.join(dirname, f+e)
        else:
            fn = os.path.join(dirname, f+ '(' + str(i) + ')'+e)         
        if os.path.exists(fn):
            return definefn(dirname, filename, i+1)
        else:
            return fn

    fn = definefn(dirname, filename)
    
    if os.getenv('USERNAME'):
        username = os.getenv('USERNAME')  # Works on MS Windows
    else:
        username = 'unknown'  
    now = datetime.datetime.now()
    time = now.strftime("%m-%d-%Y %I:%M %p")
    
    bomheader = '&C&A'        
    if drop:   # add a tab to Excel called droplist; and show drop & exceptions
        bomfooter = '&LCreated ' + time + ' by ' + username + '&CPage &P of &N&Rdrop: yes'
        dfvalues = list(itertools.zip_longest(drop, exceptions, fillvalue=''))
        df = pd.DataFrame(dfvalues, columns =['drop', 'exceptions'])
        df['index'] = list(range(len(df.index)))
        df.set_index('index', inplace=True)
        results2export.append(('droplist', df))
    else:
        bomfooter = '&LCreated ' + time + ' by ' + username + '&CPage &P of &N'
        
    with pd.ExcelWriter(fn) as writer:
        for r in results2export:
            sheetname = r[0]
            df = r[1]
            df.to_excel(writer, sheet_name=sheetname)
            worksheet = writer.sheets[sheetname]  # pull worksheet object
            autosize_excel_columns(worksheet, df)
            worksheet.set_header(bomheader)  # see: https://xlsxwriter.readthedocs.io/page_setup.html
            worksheet.set_footer(bomfooter)
            worksheet.set_landscape()
            worksheet.fit_to_pages(1, 0) 
            worksheet.hide_gridlines(2)                
        writer.save()
    abspath = os.path.abspath(fn)
    print("\nCreated file: " + abspath + '\n')
    
    if sys.platform[:3] == 'win':  # Open bomcheck.xlsx in Excel when on Windows platform
        try:
            os.startfile(abspath)
        except:
            print('Attempt to open bomcheck.xlsx in Excel failed.' )            


if __name__=='__main__':
    main()                   # comment out this line for testing
    #bomcheck('*')   # use for testing #







        

    