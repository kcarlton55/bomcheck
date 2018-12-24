#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 20:39:10 2018

@author: ken
"""


__version__ = '0.1.6'
import glob, argparse, sys, warnings
import pandas as pd
import os.path
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', None)

def main():
    '''bomcheck.py can be run from a command line.
    
    Examples
    ========
    
    >>> python bomcheck.py "078551*"   
    
    >>> python bomcheck.py "C:\\\\pathtomyfile\\\\6890-*"  # must use double (\\\\) backslash
    
    >>> python bomcheck.py "*"
    
    >>> python bomcheck.py --help
    
    \u2009  
    '''
    dir_bc = os.path.dirname(os.path.realpath(__file__))  # direcory where bomcheck.py is at
    exceptions_default = os.path.join(dir_bc, 'exceptions.txt')
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Program to compare SolidWorks BOMs to SyteLine BOMs')
    #parser = argparse.ArgumentParser(description='Compare SolidWorks BOMs to a SyteLine BOMs')
    parser.add_argument('filename', help='Excel files containing BOMs to compare. ' +
                        'Filenames must end with _sw.xlsx or _sl.xlsx.  ' +
                        'Examples: "078551*", "6890-*", "*"')
    parser.add_argument('-e', '--exceptions',  # default: where bomcheck.py is located 
                        default=exceptions_default,
                        help='text file containing excecptions to pns (off-the-shelf items) omited from SW BOMs',
                        metavar='')
    parser.add_argument('-v', '--version', action='version',
                    version=__version__, help="Show program's version number and exit.")
    parser.add_argument('-o', '--out', default='bomcheck', metavar='', 
                        help="Name of excel file to create and then output results to.")
    parser.add_argument('--operation', default=10, help='Operation no. that shows in output from the `sw` function')
    args = parser.parse_args()
    dirname, swfiles, pairedfiles = gatherfilenames(args.filename)
    op = args.operation
           
    swlist = []
    mergedlist = []
    
    for _sw in swfiles:
        swlist.append((_sw[0], sw(_sw[1], args.exceptions, op)))
        
    for pf in pairedfiles:
        mergedlist.append((pf[0], sl(sw(pf[1], args.exceptions), pf[2])))
    
    export2excel(dirname, args.out, swlist, mergedlist)
        

def bomcheck(fn, exceptions='<dir of bomcheck.py file>/exceptions.txt', operation=10):
    '''Do BOM checks on a group of Excel files containing BOMs.  Filenames must
    end with _sw.xlsx or _sl.xlsx.  Leading part of file names must match.  For
    example, leading parts of names 0300-2018-797_sw.xlsx and 0300-2018-797_sw.xlsx
    match and a BOM check will be done on them.
    
    Parmeters
    =========
    
    fn : string
        filename(s) of Excel files to do a BOM check on.
        
    exceptions : string
        Name of text file containing excecptions to pns (off-the-shelf items)
        that are omited from SW BOMs (carried out by the `sw` function)
        
    Returns
    =======

    out : Excel file (saved to disk)
        The Excel file show the outputs from the swlist and the mergedlist.
        Each object is shown on its own individual Excel worksheet. 
        
    Examples
    ========
    
    >>> bomcheck("078551*")   
    
    >>> bomcheck("C:\\\\pathtomyfile\\\\6890-*")   # must use double (\\\\) backslash
    
    >>> bomcheck("*")
    
    \u2009        
    '''
    dirname, swfiles, pairedfiles = gatherfilenames(fn)
    op = operation
    dir_bc = os.path.dirname(os.path.realpath(__file__))  # direcory where bomcheck.py is at
    excepts_default_file = os.path.join(dir_bc, 'exceptions.txt')
    
    if not exceptions=='<dir of bomcheck.py file>/exceptions.txt' and os.path.isfile(exceptions):
        exceptsfile = exceptions
    else:
        exceptsfile = excepts_default_file
   
    swlist = []
    mergedlist = []
    
    for _sw in swfiles:
        swlist.append((_sw[0], sw(_sw[1], exceptsfile, op)))
              
    for pf in pairedfiles:
        mergedlist.append((pf[0], sl(sw(pf[1], exceptsfile), pf[2])))
        
    export2excel(dirname, 'bomcheck', swlist, mergedlist)
    
    results = {}
    for s in swlist:
        results[s[0]] = s[1]
    for m in mergedlist:
        results[m[0]] = m[1]
    return results
        

def get_version():
    return __version__


def export2excel(dirname, filename, swlist, mergedlist):
    '''Export to an Excel file the results of all the bom checks that have
    been done.
    
    Parmeters
    =========
    
    dirname : string
        The directory to which the Excel file that this function generates
        will be sent.
        
    filename : string
        The name of the Excel file.
        
    swlist : list
        List of pandas DataFrame objects.  This list is a result of the output
        from the function "sw".  These are SolidWorks BOMs for which no
        matching SyteLine BOM was found.
        
    mergedlist : list
        List of DataFrame objects.  Each of these DataFrame objects is the
        output of the "sl" function.  That is, each object is a bom check
        showing the comparison of a SolidWorks BOM and a SyteLine BOM.
        
    Returns
    =======

    out : Excel file (saved to disk)
        The Excel file show the outputs from the swlist and the mergedlist.
        Each object is shown on its own individual Excel worksheet. 
        
     \u2009 
    '''
    d, f = os.path.split(filename)
    f, e = os.path.splitext(f)
    if d:
        dirname = d   # if user specified a directory, use it instead
    if e and not e[4].lower()=='.xls':
        print('output filename extension needs to be .xlsx')
        print('Program aborted.')
        sys.exit()
    else:
        e = '.xlsx'
    fn = os.path.join(dirname, f+e)
    
    with pd.ExcelWriter(fn) as writer:
        for s in swlist:
            sheetname = s[0]
            df = s[1]
            df.to_excel(writer, sheet_name=sheetname)
            worksheet = writer.sheets[sheetname]  # pull worksheet object
            # adjust widths of columns in Excel worksheet to fit data's width:
            for idx, col in enumerate(df):  # loop through all columns
                series = df[col]
                max_len = max((
                    series.astype(str).map(len).max(),  # len of largest item
                    len(str(series.name))  # len of column name/header
                    )) + 1  # adding a little extra space
                worksheet.set_column(idx+1, idx+1, max_len)  # set column width

        for m in mergedlist:
            sheetname = m[0]
            df = m[1]
            df.to_excel(writer, sheet_name=sheetname)
            worksheet = writer.sheets[sheetname]  # pull worksheet object
            for idx, col in enumerate(df):  # loop through all columns
                series = df[col]
                max_len = max((
                    series.astype(str).map(len).max(),  # len of largest item
                    len(str(series.name))  # len of column name/header
                    )) + 1  # adding a little extra space
                worksheet.set_column(idx+1, idx+1, max_len)  # set column width
        writer.save()
            

def gatherfilenames(filename):
    '''Gather names of excel files to be processed and return them in organized
    lists.  Names must end with `_sw.xlsx`, `_sl.xlsx`, `_sw.csv`, or `_sl.csv`
    
    Parmeters
    =========
    
    filename : string
        e.g., r"C:/filepath/*".  The `*` means that all excel files ending with
        `_sw.xlsx` or `_sl.xlsx` will be gathered.
   
    Returns
    =======

    out : tuple with two items
        The second tuple item is a list of tuples, each with two file names:
        the first is the name of excel file containing a SolidWorks bom, and 
        the second is the matching SyteLine file name, e.g., 
        (073166_sw.xlsx, 073166_sl.xlsx)
        .
        The first tuple item is a list of SolidWorks boms for which no matching
        Syteline bom was found.  
        
     \u2009 
    '''
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        print('directory not found: ', dirname)
        sys.exit()
    gatherednames = sorted(glob.glob(filename))
    swfilenames_tmp = []
    for f in gatherednames:
        i = f.rfind('_')
        if f[i:i+4].lower()=='_sw.':
            swfilenames_tmp.append(f)
    swfilenames = []
    pairedfilenames = []
    for s in swfilenames_tmp:
        flag = True
        j = s.rfind('_')
        for f in gatherednames:
            i = f.rfind('_')
            if f[i:i+4].lower()=='_sl.' and s[:j].lower()==f[:i].lower():
                dname, fname = os.path.split(s)
                fname = fname[:i]
                pairedfilenames.append((fname, s, f))
                flag = False
        if flag==True:
            dname, fname = os.path.split(s)
            fname, ext = os.path.splitext(fname)
            swfilenames.append((fname, s))
    return dirname, swfilenames, pairedfilenames
                
        
def test_columns(df, required_columns):
    '''The sw and sl functions call upon this function to ascertain whether
    or not the user has input proper BOM data.  
    
    Parmeters
    =========

    df : pandas DataFrame
        A Dataframe from which column titles are extracted to see if they match
        columns that should be in a SolidWorks or SyteLine BOM.
        
    required_columns : list
        A list of column titles, each a string object, that should be present
        in a BOM that tells the program that all is OK.  If the list item is a
        tuple, for example ('PARTNUMBER', 'PART NUMBER'), then either of 
        tuple items are acceptable.

    Returns
    =======

    out : string
        if the string is a null string, i.e. '', then the test has been passed
        and all column titles are present.  However if a non null string is
        returned, e.g., 'U/M', then at least one column title is missing and
        the test fails.
        
    \u2009 
    '''
    not_found = ''  # not_found is a column title that is not found
    c = df.columns
    for r in required_columns:
        if type(r) == tuple:
            for r0 in r:
                if r0 in c:
                    not_found = ''
                    break
                not_found = r    
        else:
            if r not in c:
                not_found = r
                break
    return not_found
                
            
def sw(filename='clipboard', exceptions='./exceptions.txt', operation=10):   
    '''Take a SolidWorks BOM and restructure it to be like that of a SyteLine 
    BOM.  That is, the following is done:
        
    - If a part no. is shown multiple times in a BOM, change the BOM so that
      the part no. is only shown once.  The quatity for that part is the sum
      of the quantites for the multiple items.
    - If the part is a pipe or beam, and it is shown multiple times in the BOM,
      change the BOM so that it is shown only once.  The length for that part
      is the sum of the lengths of the multiple parts.
    - For parts that have a length associated with it, the lenghts are
      converted from inches to feet.
    - Any pipe fittings that start with "3" and end "025" (i.e., off-the-shelf
      pipe fittings) are removed from the BOM since these part nos. are not
      shown on a SyteLine BOM.  Place exceptions to this rule in the file
      `exceptions.txt`
    - Column titles are changed to match those of SyteLine.
    
    Parmeters
    =========
    
    filename : string
        Name of Excel file(s) to process.
        
    excpetions : string
        Name of the text file containing a list part number exceptions.
        (part numbers staring with `3` and ending with `025`, i.e. 
        off-the-shelf pipe fittings, are removed from SolidWorks boms.  
        Exceptions to this rule are listed in the text file.)
        
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
    _, ext = os.path.splitext(filename)
    try:
        if filename=='clipboard' or filename=='cb':
            df_sw = pd.read_clipboard(engine='python', na_values=[' '], skiprows=1)
        elif str(type(filename))[-11:-2] == 'DataFrame':
            df_sw = filename
        elif ext=='.xlsx' or ext=='.xls': 
            df_sw = pd.read_excel(filename, na_values=[' '], skiprows=1)
        elif ext=='.csv':
            df_sw = pd.read_csv(filename, na_values=[' '], skiprows=1, engine='python', encoding='windows-1252')
        else:
            print('non valid file name (', filename, ') (err 102)')
            sys.exit()
            
    except IOError:
        print('FILNAME NOT FOUND: ', filename)
        sys.exit()
    #except:
    #    print('unknown error in function sw')
    #    sys.exit()
        
    exlist = []  # Exceptions to part nos. removed for SW BOM.    
    try:    
        with open(exceptions,'r') as fh:
            exceps = fh.read().splitlines()
    except FileNotFoundError:
        print('File not found: exceptions.txt')
        exceps=[]
    for e in exceps:
        if e and e[0]!='#':
             exlist.append(e.strip()) 
        
    required_columns = [('QTY', 'QTY.'), 'DESCRIPTION', ('PART NUMBER', 'PARTNUMBER')]  # optional: LENGTH
    missing = test_columns(df_sw, required_columns)
    if missing:
        print('At least one column in your SW data (' + os.path.split(filename)[1] + ')  not found: ', missing)
        sys.exit()   

    df_sw.fillna(0, inplace=True)  # fill NaN values with 0
    df_sw['DECRIPTION'] = df_sw['DESCRIPTION'].apply(lambda x: x.replace('\n', ''))  # get rid of "new line" character
    df_sw.rename(columns={'PARTNUMBER':'Item', 'PART NUMBER':'Item',   # rename column titles
                          'DESCRIPTION': 'Material Description', 'QTY': 'Qty', 'QTY.': 'Qty'}, inplace=True)
    filtr1 = df_sw['Item'].str.startswith('3086')  # filter pipe nipples (i.e. pn starting with 3086)
    try:       # if no LENGTH in the table, an error occurs. "try" causes following lines to be passed over 
        df_sw['LENGTH'] = round((df_sw['Qty'] * df_sw['LENGTH'] * ~filtr1) /12.0, 4)  # covert lenghts to feet. ~ = NOT 
        filtr2 = df_sw['LENGTH'] >= 0.00001  # a filter: only items where length greater than 0.0
        df_sw['Qty'] = df_sw['Qty']*(~filtr2) + df_sw['LENGTH']  # move lengths (in feet) to the Qty column
        df_sw['U/M'] = filtr2.apply(lambda x: 'FT' if x else 'EA')
    except:
        df_sw['U/M'] = 'EA'

    df_sw = df_sw.reindex(['Op', 'WC','Item', 'Qty', 'Material Description', 'U/M'], axis=1)  # rename and/or remove columns
    d = {'Qty': 'sum', 'Material Description': 'first', 'U/M': 'first'}   # funtions to apply to next line
    df_sw = df_sw.groupby('Item', as_index=False).aggregate(d).reindex(columns=df_sw.columns)
    filtr3 = df_sw['Item'].str.startswith('3') & df_sw['Item'].str.endswith('025') & ~df_sw['Item'].isin(exlist)
    df_sw.drop(df_sw[filtr3].index, inplace=True)  # delete nipples & fittings who's pn ends with "025"
    df_sw['WC'] = 'PICK'
    df_sw['Op'] = str(operation)  
    df_sw.set_index('Op', inplace=True)
    
    return df_sw


def sl(df_solidworks, filename='clipboard'): 
    '''This function reads in a BOM derived from StyeLine and then merges it 
    with the BOM from SolidWorks.  The merged BOMs allow differences to
    easily seen between the two BOMs.
    
    The first column in the output is labeled `IQMU`.  Check marks and Xs will
    be under this column header.  `I` means that the item (part number) matches
    in SolidWorks and SyteLine, Q for quatities matching, M for Material 
    Description matching, and U for unit of measure matching.
            
    Parmeters
    =========
  
    filename : string
        Name of Excel file(s) to process
    
    df_solidworks : pandas.DataFrame
        A DataFrame produced by the function `sw`
        
    Returns
    =======    
        
        
    Examples
    ========
    
    >>> sl()
    
    >>> sl(r"C:\\dirpath\\name2.xlsx", sw(filename))
    
    \u2009 
    '''
    df_sw = df_solidworks
    _, ext = os.path.splitext(filename)
    
    try:
        if filename=='clipboard' or filename=='cb':
            df_sl = pd.read_clipboard(engine='python', na_values=[' '])
        elif str(type(filename))[-11:-2] == 'DataFrame':
            df_sl = filename
        elif ext=='.xlsx' or ext=='.xls': 
            df_sl = pd.read_excel(filename, na_values=[' '])
        elif ext=='.csv':
            df_sl = pd.read_csv(filename, na_values=[' '], engine='python', encoding='windows-1252')
        else:
            print('non valid file name (', filename, ') (err 101)')
            sys.exit()
        
    except IOError:
        print('FILNAME NOT FOUND: ', filename)
        sys.exit()
    #except:
    #    print('unknown error in function sl')
    #    sys.exit()
    
    sl_required_columns = [('Qty', 'Quantity'), 'Material Description', 'U/M', ('Item', 'Material')]
    missing = test_columns(df_sl, sl_required_columns)
    if missing:
        print('At least one column in your SL data (' + os.path.split(filename)[1] + ') not found: ', missing)
        sys.exit()    
    
    if not str(type(df_sw))[-11:-2] == 'DataFrame':
        print('Program halted.  A fault with SolidWorks DataFrame occurred.')
        sys.exit()
    
    # A BOM can be derived from different locations within SL.  From one location
    # the `Item` is the part number.  From another `Material` is the part number.
    # When `Material` is the part number, a useless 'Item' column is also present.
    # It causes the bomcheck program confusion and the program crashes.
    if 'Item' in df_sl.columns and 'Material' in df_sl.columns:
        df_sl.drop(['Item'], axis=1, inplace=True)       
    df_sl.rename(columns={'Material':'Item', 'Quantity':'Qty'}, inplace=True)
    df_merged = pd.merge(df_sw, df_sl, on='Item', how='outer', suffixes=('_sw', '_sl'), indicator=True)
    df_merged.sort_values(by=['Item'], inplace=True)
    filtrI = df_merged['_merge'].str.contains('both')  # this filter determines if pn in both SW and SL
    filtrQ = abs(df_merged['Qty_sw'] - df_merged['Qty_sl']) < .01  # a filter is a list of True/False values
    filtrM = df_merged['Material Description_sw'].str.split()==df_merged['Material Description_sl'].str.split()
    filtrU = df_merged['U/M_sw']==df_merged['U/M_sl']
    chkmark = '\u2713' # The UTF-8 character code for a check mark character
    err = '\u2716'     # X character
    ws = '\u2009'      # ws = white space character, ref: https://en.wikipedia.org/wiki/Whitespace_character
    IQMU = 'I' + ws + 'Q' + ws + 'M' + ws + 'U'  # i.e., U Q M U... ctc = "Column Title for Checks"
    df_merged[IQMU] = (filtrI.apply(lambda x: chkmark if x else err)     # X = Item not in SW or SL
                       + filtrQ.apply(lambda x: chkmark if x else err)   # X = Qty differs btwn SW and SL
                       + filtrM.apply(lambda x: chkmark if x else err)   # X = Mtl differs btwn SW & SL
                       + filtrU.apply(lambda x: chkmark if x else err))  # X = U/M differs btwn SW & SL
    df_merged[IQMU] = ~df_merged['Item'].duplicated(keep=False) * df_merged[IQMU] # duplicate in SL? IQMU-> blank
    df_merged = df_merged[['Item', IQMU, 'Qty_sw', 'Qty_sl', 'Material Description_sw',
                           'Material Description_sl', 'U/M_sw', 'U/M_sl']]
    df_merged.fillna('', inplace=True)
    df_merged.set_index(IQMU, inplace=True)
    #df_merged.to_clipboard()
    return df_merged


if __name__=='__main__':
    main()


    