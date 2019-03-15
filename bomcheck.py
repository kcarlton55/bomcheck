#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 20:39:10 2018

@author: ken
"""


__version__ = '0.1.18'
import glob, argparse, sys, warnings
import pandas as pd
import os.path
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)


def getdroplist():
    ''' Create two global python lists named drop and exceptions.  These lists
    are derived from the file named droplists.py.  This file is meant for 
    anyone in the Engineering department to be able to modify.  The lists are
    of pns, like those for bolts and nuts, that are to be excluded from the bom
    check.  These lists are called upon by the sw() function.
    '''
    global drop, exceptions
    pathDekker = os.path.normpath("I:/bomcheck/")
    pathDevelopment = os.path.normpath("/home/ken/projects/project1/")
    if os.path.exists(pathDekker) and not pathDekker in sys.path:
        sys.path.append(pathDekker)
    if os.path.exists(pathDevelopment) and not pathDevelopment in sys.path:
        sys.path.append(pathDevelopment)
    try:
        import droplist
        drop = droplist.drop
        exceptions = droplist.exceptions
    except ModuleNotFoundError:
        print('\nFile droplist.py not found or corrupt.  Put it in the')
        print('directory I:\\bomcheck\n')
        drop = ["3*-025", "3800-*"]
        exceptions= []
        
        
getdroplist()       


def main():
    '''bomcheck.py can be run from a command line.

    Examples
    ========

    >>> python bomcheck.py "078551*"

    >>> python bomcheck.py "C:\\pathtomyfile\\6890-*"

    >>> python bomcheck.py "*"

    >>> python bomcheck.py --help

    \u2009
    '''
    dropcontents = 'drop: ' + str(drop) + ', exceptions: ' + str(exceptions)
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                        description='Program to compare SolidWorks BOMs to SyteLine BOMs')
    parser.add_argument('filename', help='Name of file containing BOM.  Name ' +
                        'must end with _sw.xlsx, _sl.xlsx. _sw.csv, or ' +
                        '_sl.csv.  Enclose name in quotes.  An asterisk, *, ' +
                        'caputures multiple files.  Examples: "6890-*", "*".  ' +
                        'Optionally BOM can be entered via the clipboard: '  
                        ' Enter "1" to process only a SW BOM.  ' +
                        ' Enter "2" to process both a SW and SL BOM.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Show results on the computer monitor')
    parser.add_argument('-d', '--drop', action='version', version=dropcontents,
                        help='Show "drop" and "exceptions" lists and exit.  ' +
                        'The drop list contains pns that are dropped from the ' +
                        'the SW BOM and not included in the BOM check.  The ' +
                        'exeptions list contains exceptions to pns of the drop ' +
                        'list.  These lists are loaded from the file droplist.py')
    parser.add_argument('-a', '--all', action='store_true', default=False,
                        help='Include in the check pns of the drop list')
    parser.add_argument('--version', action='version', version=__version__,
                        help="Show program's version number and exit")
    args = parser.parse_args()
    bomcheck(args.filename, args.verbose, args.all)

    
def bomcheck(fn, v=False, a=False):
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
    
    a : bool
        use all; that is, disreguard using the drop list.  The drop list is
        a list of part nos. to disreguard for the bom check.  Default: False

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
        
    dirname, swfiles, pairedfiles = gatherfilenames(fn)
    
    if ((not swfiles and not pairedfiles) and fn not in ['1', '2']):
        print('\nNo sw or sl files found.  Check that you are working with the correct')
        print('directory.  Check that files are named correctly (e.g. XXXXXX_sw.xlsx).')
        print()
        sys.exit()
     
    title_dfsw = list(map(lambda x: (x[0], sw(x[1], a)), swfiles)) # [(title, dfsw), ...]
    title_dfmerged = list(map(lambda x: (x[0], sl(sw(x[1], a), x[2])), pairedfiles)) # [(title, dfmerged), ...]

    if fn in ['1', '2']:
        sw_df = sw('clipboard', a)
        title_dfsw.append(('clipboard', sw_df))
    if fn == '2': 
        title_dfsw = []
        title_dfmerged.append(('clipboard', sl(sw_df, filename='clipboard')))

    export2excel(dirname, 'bomcheck', title_dfsw + title_dfmerged)

    results = {}
    for s in (title_dfsw + title_dfmerged):
        results[s[0]] = s[1]

    if v:
        print()
        for pn, bom in results.items():  # cycle through each pn and bom in d
            print(pn + ":\n")      # print the pn.  \n prints a new line
            print(bom)             # print the bom
            print('\n\n')          # print two lines
    
    if sys.platform[:3] == 'win':  # Open bomcheck.xlsx in Excel
        try:
            os.startfile(os.path.join(dirname, 'bomcheck.xlsx'))
        except:
            print('Attempt to open bomcheck.xlsx in Excel failed.' )

    return results


def get_version():
    return __version__


def pause():
    programPause = input("Press the <ENTER> key to continue...")


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
        The Excel file shows on multiple sheets the results2export list.

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
        for r in results2export:
            sheetname = r[0]
            df = r[1]
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
        writer.save()
    abspath = os.path.abspath(fn)
    print("\ncreated file: " + abspath + '\n')


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

    out : tuple with tree elements: 1. name of working directory, 2. list of sw
        files and titles to assign to sw's boms, and 3. list of sl files and
        titles to assign to merged sw/sl boms.
    
        Tuple has the form:
            
        (dirname,
          [(titleforswbom1, swpathname1), ...],
          [(titleformergedbom2, swpathname2, slpathname2),...])
                    
        Where:
            dirname = the working driectory, i.e. where filename is located.
            swpathname = sw pathname, e.g., /dirpath/081233_sw.xlsx
            titleforbom = A name to attach to a bom for identification.  
                          Derived from the file name (that is, path and 
                          extension removed gives the name).
                         
        The 2nd item a list of tuples, each of length 2, containing only sw 
        files for which no matching sl bom was found.  The third item is a list
        of tuples, each of length 3, containing sw and sl boms that are apt for
        merging. 
        
     \u2009
    '''
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        print('directory not found: ', dirname)
        sys.exit()
    gatherednames = sorted(glob.glob(filename))
    swfilenames_tmp = []
    for f in gatherednames:  # Grab a list of all the SW files that glob grabbed.
        i = f.rfind('_')
        if f[i:i+4].lower()=='_sw.':
            swfilenames_tmp.append(f)  # [/pathname/file1_sw.xlxs, ...,/pathname/fileN_sw.xlx]
    swfilenames = []
    pairedfilenames = []
    # go through the sw files.  Find find the matching sl file for a given sw file
    for s in swfilenames_tmp:
        flag = True    # assume only a sw file exists...  no matching sl file.
        j = s.rfind('_')  # this to truncate the sw filename; i.e. to git rid of _sw.xlsx
        for f in gatherednames:
            i = f.rfind('_')
            if f[i:i+4].lower()=='_sl.' and s[:j].lower()==f[:i].lower():  # found sw/sl match
                dname, fname = os.path.split(s)
                k = fname.rfind('_')
                fntrunc = fname[:k]  # Name of the sw file, excluding path, and excluding _sw.xlsx
                pairedfilenames.append((fntrunc, s, f))  # (identifier, sw filename, sl filename)
                flag = False  # sw file is not alone!
        if flag==True:  # sw file is alone... no matching sl file found.
            dname, fname = os.path.split(s)
            fname, ext = os.path.splitext(fname)
            swfilenames.append((fname, s))  #  (identifier with _sw.xlsx ext, sw filename)
    return dirname, swfilenames, pairedfilenames


def test_columns(df, required_columns):
    '''The sw and sl functions call upon this function to try to ascertain
    whether or not the user has input proper BOM data.

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
        returned, e.g., 'U', then at least one column title is missing and
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


def sw(filename='clipboard', a=False):
    '''Take a SolidWorks BOM and restructure it to be like that of a SyteLine
    BOM.  That is, the following is done:

    - For parts with a length provided, the length is converted from inches
      to feet.
    - If the part is a pipe or beam, and it is shown multiple times in the bom,
      change the bom so that it is shown only once.  The length for that part
      in the new bom is the sum of the lengths of the multiple parts.  
      The program knows to execute this process by whether a Length is given
      for the part or not.
    - Any pipe fittings that start with "3" and end "025" (i.e., off-the-shelf
      pipe fittings) are removed from the BOM since these part nos. are not
      normally shown in SyteLine bomss.  This rule is goverened by the part nos.
      listed in the file named drop.py which may be updated by users.
    - Many times part nos. for pipe nipples show more than once in a sw bom.
      This function changes the occurance to one and sums the quatities.
    - Column titles are changed to match those of SyteLine.

    Parmeters
    =========

    filename : string
        Name of SolidWorks Excel file to process.  If filename = clipboard, the 
        sw bom is taken from the clipboard.

    a : bool
        use all; that is, disreguard using the drop list.  The drop list is
        a list of part nos. to disreguard for the bom check.  Default: False
    
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
        if filename.lower() in ['c', 'x', 'cb', 'clipboard']:
            print('\nCopy SolidWorks BOM to clipboard.  Include title.')
            pause()
            dfsw = pd.read_clipboard(engine='python', na_values=[' '], skiprows=1)
        elif str(type(filename))[-11:-2] == 'DataFrame':
            dfsw = filename
        elif ext=='.xlsx' or ext=='.xls':
            try:
                dfsw = pd.read_excel(filename, na_values=[' '], skiprows=1, engine='python')
            except:
                dfsw = pd.read_excel(filename, na_values=[' '], skiprows=1)
        elif ext=='.csv':
            dfsw = pd.read_csv(filename, na_values=[' '], skiprows=1,
                                encoding='iso8859_1', engine='python')
        else:
            print('non valid file name (', filename, ') (err 102)')
            sys.exit()

    except IOError:
        print('FILNAME NOT FOUND: ', filename)
        sys.exit()

    required_columns = [('QTY', 'QTY.'), 'DESCRIPTION', ('PART NUMBER', 'PARTNUMBER')]  # optional: LENGTH
    missing = test_columns(dfsw, required_columns)
    if missing:
        print('At least one column in your SW data (' + os.path.split(filename)[1] + ')  not found: ', missing)
        sys.exit()

    dfsw.fillna(0, inplace=True)  # fill NaN values with 0
    dfsw['DESCRIPTION'].replace(0, '!! No SW description provided !!', inplace=True)
    dfsw['DESCRIPTION'] = dfsw['DESCRIPTION'].apply(lambda x: x.replace('\n', ''))  # get rid of "new line" character
    dfsw.rename(columns={'PARTNUMBER':'Item', 'PART NUMBER':'Item',   # rename column titles
                          'DESCRIPTION': 'Material Description', 'QTY': 'Q', 'QTY.': 'Q'}, inplace=True)
    filtr1 = dfsw['Item'].str.startswith('3086')  # filter pipe nipples (i.e. pn starting with 3086)
    try:       # if no LENGTH in the table, an error occurs. "try" causes following lines to be passed over
        dfsw['LENGTH'] = round((dfsw['Q'] * dfsw['LENGTH'] * ~filtr1) /12.0, 4)  # covert lenghts to feet. ~ = NOT
        filtr2 = dfsw['LENGTH'] >= 0.00001  # a filter: only items where length greater than 0.0
        dfsw['Q'] = dfsw['Q']*(~filtr2) + dfsw['LENGTH']  # move lengths (in feet) to the Qty column
        dfsw['U'] = filtr2.apply(lambda x: 'FT' if x else 'EA')
    except:
        dfsw['U'] = 'EA'
    dfsw = dfsw.reindex(['Op', 'WC','Item', 'Q', 'Material Description', 'U'], axis=1)  # rename and/or remove columns
    d = {'Q': 'sum', 'Material Description': 'first', 'U': 'first'}   # funtions to apply to next line
    dfsw = dfsw.groupby('Item', as_index=False).aggregate(d).reindex(columns=dfsw.columns)
    
    if a==False:    
        drop2 = []
        for d in drop:  # drop is a global list of pns to exclude from the bom check
            d = '^' + d + '$'
            drop2.append(d.replace('*', '[A-Za-z0-9-]*'))    
            exceptions2 = []
        for e in exceptions:  # excpetion is also a globa list
            e = '^' + e + '$'
            exceptions2.append(e.replace('*', '[A-Za-z0-9-]*')) 
        filtr3 = dfsw['Item'].str.contains('|'.join(drop2)) & ~dfsw['Item'].str.contains('|'.join(exceptions2))
        dfsw.drop(dfsw[filtr3].index, inplace=True)  # drop frow SW BOM pns in "drop" list.
   
    dfsw['WC'] = 'PICK'
    dfsw['Op'] = str(10)
    dfsw.set_index('Op', inplace=True)

    return dfsw


def sl(df_solidworks, filename='clipboard'):
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
    dfsw = df_solidworks
    _, ext = os.path.splitext(filename)

    try:
        if filename.lower() in ['c', 'x', 'cb', 'clipboard']:
            print('\nCopy SyteLine BOM to clipboard.')
            pause()
            df_sl = pd.read_clipboard(engine='python', na_values=[' '])
        elif str(type(filename))[-11:-2] == 'DataFrame':
            df_sl = filename
        elif ext=='.xlsx' or ext=='.xls':
            df_sl = pd.read_excel(filename, na_values=[' '])
        elif ext=='.csv':
            df_sl = pd.read_csv(filename, na_values=[' '], engine='python',
                                encoding='utf-16', sep='\t')
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

    if not str(type(dfsw))[-11:-2] == 'DataFrame':
        print('Program halted.  A fault with SolidWorks DataFrame occurred.')
        sys.exit()

    # A BOM can be derived from different locations within SL.  From one location
    # the `Item` is the part number.  From another `Material` is the part number.
    # When `Material` is the part number, a useless 'Item' column is also present.
    # It causes the bomcheck program confusion and the program crashes.
    if 'Item' in df_sl.columns and 'Material' in df_sl.columns:
        df_sl.drop(['Item'], axis=1, inplace=True)
    df_sl.rename(columns={'Material':'Item', 'Quantity':'Q', 'Qty':'Q', 'U/M':'U'}, inplace=True)
    dfmerged = pd.merge(dfsw, df_sl, on='Item', how='outer', suffixes=('_sw', '_sl'), indicator=True)
    dfmerged.sort_values(by=['Item'], inplace=True)
    filtrI = dfmerged['_merge'].str.contains('both')  # this filter determines if pn in both SW and SL
    filtrQ = abs(dfmerged['Q_sw'] - dfmerged['Q_sl']) < .01  # a filter is a list of True/False values
    filtrM = dfmerged['Material Description_sw'].str.split()==dfmerged['Material Description_sl'].str.split()
    filtrU = dfmerged['U_sw']==dfmerged['U_sl']
    chkmark = '\u02DC' # The UTF-8 character code for a check mark character (was \u2713)
    err = 'X'     # X character (was \u2716)
    dfmerged['IQMU'] = (filtrI.apply(lambda x: chkmark if x else err)   # X = Item not in SW or SL
                       + filtrQ.apply(lambda x: chkmark if x else err)   # X = Qty differs btwn SW and SL
                       + filtrM.apply(lambda x: chkmark if x else err)   # X = Mtl differs btwn SW & SL
                       + filtrU.apply(lambda x: chkmark if x else err))  # X = U differs btwn SW & SL
    dfmerged['IQMU'] = ~dfmerged['Item'].duplicated(keep=False) * dfmerged['IQMU'] # duplicate in SL? IQMU-> blank
    dfmerged = dfmerged[['Item', 'IQMU', 'Q_sw', 'Q_sl', 'Material Description_sw',
                           'Material Description_sl', 'U_sw', 'U_sl']]
    dfmerged.fillna('', inplace=True)
    dfmerged.set_index('Item', inplace=True)
    #dfmerged.to_clipboard()
    return dfmerged


if __name__=='__main__':
    main()


