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

This program was designed with the intent that the program "pyinstaller" be
able to create a self executing program from bomcheck.py.  In this case, the
python modules listed in the file "requirements.txt" must be present in the
environment in which self executing program is created.

Also, the file droplist.py should be present in a location that the bomcheck
program can find it.  Within the code of the function "getdroplist" is shown
the location where the file is looked for.
"""


__version__ = '1.0.4'
__author__ = 'Kenneth Carlton'
import glob, argparse, sys, warnings
import pandas as pd
import os.path
import os
import tempfile
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)


def get_version():
    return __version__


def main():
    '''This fuction allows this bomcheck.py program to be run from the command
    line.  It is started automatically (via the "if __name__=='__main__'"
    command at the bottom of this file) when bomecheck.py is run from the
    command line.

    Examples
    ========

    $ python bomcheck.py "078551*"

    $ python bomcheck.py "C:\\pathtomyfile\\6890-*"

    $ python bomcheck.py "*"

    $ python bomcheck.py --help

    \u2009
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                        description='Program to compare SolidWorks BOMs to SyteLine BOMs')
    parser.add_argument('filename', help='Name of file containing a BOM.  Name ' +
                        'must end with _sw.xlsx, _sl.xlsx. _sw.csv, or ' +
                        '_sl.csv.  Enclose filename in quotes!  An asterisk, *, ' +
                        'caputures multiple files.  Examples: "6890-*", "*".  ' +
                        'Or if filename is a directory path, all _sw and _sl files ' +
                        'will be gathered from that directory.  ' +
                        '_sl files without a corresponding _sw file are ignored.')
    parser.add_argument('-d', '--drop', action='store_true', default=False,
                        help='Ignore pns listed in the file droplist.py')
    parser.add_argument('--version', action='version', version=__version__,
                        help="Show program's version number and exit")        
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()  
    bomcheck(args.filename, args.drop) 

    
def bomcheck(fn, d=False):
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
        
    dirname, swfiles, pairedfiles = gatherBOMs(fn)
    
    lone_sw, merged_sw2sl = combine_tables(swfiles, pairedfiles, d) # lone_sw & merged_sw2sl are dics
    
    title_dfsw = []
    for k, v in lone_sw.items():
        title_dfsw.append((k, v))
        
    title_dfmerged = []
    for k, v in merged_sw2sl.items():
        title_dfmerged.append((k, v))        
   
    try:    
        export2excel(dirname, 'bomcheck', title_dfsw + title_dfmerged)
    except PermissionError:
        print('\nError: unable to write to bomcheck.xlsx')
    
    if sys.platform[:3] == 'win':  # Open bomcheck.xlsx in Excel
        try:
            os.startfile(os.path.join(dirname, 'bomcheck.xlsx'))
        except:
            print('Attempt to open bomcheck.xlsx in Excel failed.' )


def export2excel(dirname, filename, results2export):
    '''Export to an Excel file the results of all the bom checks that have
    been done.

    Parmeters
    =========

    dirname : string
        The directory to which the Excel file that this function generates
        will be sent.

    filename : string
        The name of the Excel file.

    results2export : list
        List of pandas DataFrame objects.   Results are either: 1. Only
        SolidWorks BOMs, that have been converted to SyteLine format, if no
        corresponding SyteLine BOM was found to compare it to.  2.  A list
        showing a comparison between a SolidWorks BOM and a SyteLine BOM.

    Returns
    =======

    out : Excel file (saved to disk)
        The Excel file shows on multiple sheets the "results2export" list.

     \u2009
    '''
    d, f = os.path.split(filename)
    f, e = os.path.splitext(f)
    if d:
        dirname = d   # if user specified a directory, use it instead
    if e and not e[4].lower()=='.xls':
        print('Output filename extension needs to be .xlsx')
        print('Program aborted.')
        sys.exit(0)
    else:
        e = '.xlsx'
    fn = os.path.join(dirname, f+e)

    with pd.ExcelWriter(fn) as writer:
        for r in results2export:
            sheetname = r[0]
            df = r[1]
            df.to_excel(writer, sheet_name=sheetname)
            worksheet = writer.sheets[sheetname]  # pull worksheet object
            # adjust widths of columns in Excel worksheet to fit data's width: 
            mwic = df.index.astype(str).map(len).max() # max width of index column
            worksheet.set_column(0, 0, mwic + 1)  # set width of index column, i.e. col 0/col A
            worksheet.hide_gridlines(2)  # see: https://xlsxwriter.readthedocs.io/page_setup.html
            j = 0
            k = 0
            for idx, col in enumerate(df):  # set width of rest of columns  
                series = df[col]
                max_len = max((
                    series.astype(str).map(len).max(),  # len of largest item
                    len(str(series.name))  # len of the column's title
                    )) + k  # adding a little extra space
                j += 1
                if j >= 4:
                    k = 1
                worksheet.set_column(idx+1, idx+1, max_len)  # set column width
        writer.save()
    abspath = os.path.abspath(fn)
    print("\nCreated file: " + abspath + '\n')
    

def fixcsv(filename):
    '''fixcsv if called when a sw csv file is used.  Commas are on rare 
    occasions used within a part's description.  This comma causes the program 
    to crash.  (See the testcsv() function).  
    
    Parmeters
    =========

    filename : string
        Name of SolidWorks csv file to process.
        
    Returns
    =======
    
    out : list
        A list of all the lines in filename, except that the commas (,) in each
        line, except those that are within of the pn descriptions, are
        converted to semicolons (;).
    '''
    with open(filename, encoding="ISO-8859-1") as f:
        data1 = f.readlines()
    num = data1[0].count(',')  # no. of commas in first line of filename      
    data2 = list(map(lambda x: x.replace(',', ';') , data1)) # replace all commas with semicolons
    # The last two columns in a SW BOM are always "Descrition" and "Part Number".
    # Reverse each item (each string) of data2 and "replace" (which works from 
    # the start of a string to the end) the semicolons with commas up to 
    # postion i. Then replace the comma between pn and descrip back to a 
    # semicolon.  Finally reverse the string and append to the list named data.
    reverse = lambda s: s[::-1]    # reverse string s... Hello -> olleH
    data = []
    for d in data2:
        if d.count(';') != num:
            i = d.count(';') - num + 1
            reversed_str = reverse(d).replace(';', ',', i)
            reversed_str = reversed_str.replace(',', ';', 1)
            data.append(reverse(reversed_str))
        else:
            data.append(d)
    return data  # a list of lines from filename with semicolons as separators
         

def getdroplist():
    ''' Create two global python lists named drop and exceptions.  Make these
    lists global thus allowing easy access to other functions (speciffically to
    sw).  These lists are derived from the file named droplists.py.  This file
    is meant for anyone with proper authority to be able to modify.  The drop 
    list contains pns of off-the-shelf parts, like bolts and pipe nipples, that
    are to be excluded from the bom check.
    
    Returns
    =======
    
    out : None
    '''
    global drop, exceptions
    usrPrf = os.getenv('USERPROFILE', 'C:/nonexistent')  # on my win computer, USERPROFILE = C:\Users\k_carlton
    userDocDir = os.path.join(usrPrf, 'Documents')
    paths = [userDocDir, "I:/DVT-BOMCHECK/settings", "/home/ken/projects/project1/", "I:/bomcheck/"]
    for p in paths:
        if os.path.exists(p) and not p in sys.path:
            sys.path.append(p)
            print('\ndroplist loaded from ' + p + '\n')
            break
    try:
        import droplist
        drop = droplist.drop
        exceptions = droplist.exceptions
    except ModuleNotFoundError:
        drop = ['3*-025']   # If droplist.py not found, use this
        exceptions= []
        
        
getdroplist()       # create global variables named drop and exceptions


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
                                   encoding='iso8859_1', engine='python',
                                   dtype = {'ITEM NO.': 'str'})
            temp.close()
        elif file_extension == '.xlsx' or file_extension == '.xls':
            df = pd.read_excel(v, na_values=[' '], skiprows=1)
        if not missing_columns('sw', df, k):
            swdfsdic.update(multilevelbom(df, k))
    sldfsdic = {}
    for k, v in slfilesdic.items(): 
        _, file_extension = os.path.splitext(v)
        if file_extension == '.csv':
            df = pd.read_csv(v, na_values=[' '], engine='python',
                             encoding='utf-16', sep='\t')
        elif file_extension == '.xlsx' or file_extension == '.xls':
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


def missing_columns(bomtype, df, pn, printerror=True):
    ''' SolidWorks and SyteLine BOMs require certain essential columns to be
    present.  This function looks at those BOMs that are within dfdic to see if
    any required columns are missing.  If found, print to screen.  Finally, 
    return a dictionary like that input less the faulty BOMs.

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
    else: # 'sl bom'
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


def combine_tables(swdic, sldic, d=False):
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
        
    d : bool
        A boolean to pass along to the sw function.

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

    - For parts with a length provided, the length is converted from inches
      to feet.
    - If the part is a pipe or beam and it is listed multiple times in the bom,
      the bom is updated so that the part is shown only once.  The length is 
      converted to the sum of the lengths of the multiple parts.
    - Any pipe fittings that start with "3" and end with "025" are 
      off-the-shelf parts.  They are removed from the SolidWorks bom.  (As a
      rule, off-the-shelf parts are not shown on SyteLine boms.)  The list
      that governs this rule is in a file named drop.py.  This file may be
      updated by authorized users.  Therefore other part nos. may be added to 
      this list if required.
    - Many times part nos. for pipe nipples show more than once in a sw bom.
      If this occurs the bom is updated so that the nipple part no. shows only 
      once.  The quantity is updated accordingly for this nipple.
    - Column titles are changed to match those of SyteLine.

    Parmeters
    =========

    df : Pandas DataFrame
        Name of SolidWorks Excel file to process.  If filename = clipboard, the 
        sw bom is taken from the clipboard.

    d : bool
        If d True, ignore items from droplist.  (See getdroplist()).
        Default: False
    
    Returns
    =======

    out : pandas DataFrame
        A SolidWorks BOM with a structure like that of SyteLine.

    Examples
    ========

    >>> sw()   # Get the BOM from the clipboard

    >>> sw(r"C:\\dirpath\\name.xlsx")

    \u2009
    '''  
    values = {'QTY':0, 'QTY.':0, 'LENGTH':0, 'DESCRIPTION': 'description missing',
              'PART NUMBER': 'pn missing', 'PARTNUMBER': 'pn missing'} 
    df.fillna(value=values, inplace=True)
    # obsolete: df['DESCRIPTION'].replace(0, '!! No SW description provided !!', inplace=True)
    df['DESCRIPTION'] = df['DESCRIPTION'].apply(lambda x: x.replace('\n', ''))  # get rid of "new line" character
    df.rename(columns={'PARTNUMBER':'Item', 'PART NUMBER':'Item', 'L': 'LENGTH',
                       'DESCRIPTION': 'Description', 'QTY': 'Q', 'QTY.': 'Q',}, inplace=True)
    filtr1 = df['Item'].str.startswith('3086')  # filter pipe nipples (i.e. pn starting with 3086)
    try:       # if no LENGTH in the table, an error occurs. "try" causes following lines to be passed over
        df['LENGTH'] = round((df['Q'] * df['LENGTH'] * ~filtr1) /12.0, 2)  # covert lenghts to feet. ~ = NOT
        filtr2 = df['LENGTH'] >= 0.00001  # a filter: only items where length greater than 0.0
        df['Q'] = df['Q']*(~filtr2) + df['LENGTH']  # move lengths (in feet) to the Qty column
        df['U'] = filtr2.apply(lambda x: 'FT' if x else 'EA')
    except:
        df['U'] = 'EA'
    df = df.reindex(['Op', 'WC','Item', 'Q', 'Description', 'U'], axis=1)  # rename and/or remove columns
    dd = {'Q': 'sum', 'Description': 'first', 'U': 'first'}   # funtions to apply to next line
    df = df.groupby('Item', as_index=False).aggregate(dd).reindex(columns=df.columns)
    
    if d==True:
        drop2 = []
        for d in drop:  # drop is a global list of pns to exclude from the bom check
            d = '^' + d + '$'
            drop2.append(d.replace('*', '[A-Za-z0-9-]*'))    
        exceptions2 = []
        for e in exceptions:  # excpetion is also a globa list
            e = '^' + e + '$'
            exceptions2.append(e.replace('*', '[A-Za-z0-9-]*'))
        if drop2:
            filtr3 = df['Item'].str.contains('|'.join(drop2)) & ~df['Item'].str.contains('|'.join(exceptions2))
            df.drop(df[filtr3].index, inplace=True)  # drop frow SW BOM pns in "drop" list.
    
    df['WC'] = 'PICK'
    df['Op'] = str(10)
    df.set_index('Op', inplace=True)

    return df


def sl(dfsw, dfsl):
    '''This function reads in a bom derived from StyeLine and then merges it
    with the bom from SolidWorks.  The merged boms allow differences to
    easily seen.

    The first column in the output is labeled `IQMU`.  Check marks and Xs will
    be under this column header.  `I` means that the item (part number) matches
    in SolidWorks and SyteLine, Q for quatities matching, M for Material
    Description matching, and U for unit of measure matching.

    Parmeters
    =========

    df_solidworks : pandas DataFrame
        A DataFrame produced by the function `sw()`

    filename : string
        Name of SyteLine Excel file to process.  If filename = clipboard, the 
        sl bom is taken from the clipboard.

    Returns
    =======

    df_merged : Pandas DataFrame
        df_merged it a DataFrame that shows a side-by-side comparison of a
        SolidWorks bom to a SyteLine bom.

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
    dfsl.rename(columns={'Material':'Item', 'Quantity':'Q', 'Material Description':'Description',
                         'Qty':'Q', 'Qty Per': 'Q', 'U/M':'U', 'UM':'U'}, inplace=True)
    dfmerged = pd.merge(dfsw, dfsl, on='Item', how='outer', suffixes=('_sw', '_sl'), indicator=True)
    dfmerged.sort_values(by=['Item'], inplace=True)
    filtrI = dfmerged['_merge'].str.contains('both')  # this filter determines if pn in both SW and SL
    filtrQ = abs(dfmerged['Q_sw'] - dfmerged['Q_sl']) < .005  # a filter is a list of True/False values
    filtrM = dfmerged['Description_sw'].str.split()==dfmerged['Description_sl'].str.split()
    filtrU = dfmerged['U_sw']==dfmerged['U_sl']
    chkmark = '-' # '\u02DC' # The UTF-8 character code for a check mark character (was \u2713)
    err = 'X'     # X character (was \u2716)
    
    dfmerged['i'] = filtrI.apply(lambda x: chkmark if x else err)     # X = Item not in SW or SL
    dfmerged['q'] = filtrQ.apply(lambda x: chkmark if x else err)     # X = Qty differs btwn SW and SL
    dfmerged['d'] = filtrM.apply(lambda x: chkmark if x else err)     # X = Mtl differs btwn SW & SL
    dfmerged['u'] = filtrU.apply(lambda x: chkmark if x else err)     # X = U differs btwn SW & SL
    dfmerged['i'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['i'] # duplicate in SL? IQMU-> blank
    dfmerged['q'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['q'] # duplicate in SL? IQMU-> blank
    dfmerged['d'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['d'] # duplicate in SL? IQMU-> blank
    dfmerged['u'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['u'] # duplicate in SL? IQMU-> blank
    
    dfmerged = dfmerged[['Item', 'i', 'q', 'd', 'u', 'Q_sw', 'Q_sl', 'Description_sw',
                           'Description_sl', 'U_sw', 'U_sl']]
    dfmerged.fillna('', inplace=True)
    dfmerged.set_index('Item', inplace=True)
    #dfmerged.to_clipboard()
    return dfmerged


if __name__=='__main__':
    main()                   # comment out this line for testing
    #bomcheck('*')   # use for testing #







        

    