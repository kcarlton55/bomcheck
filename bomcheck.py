#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File initial creation on Sun Nov 18 2018

@author: Ken Carlton

This program compares two BOMs: one originating from SolidWorks (sw) and the 
other from SyteLine (sl).  The structure of the BOMs (headings, structure, 
etc.) are very unique to our company.  Therefore this program, unaltered, will
fail to function at another company. 

Run from the command line like this: python bomcheck.py -v '*'

Run without any arguments shows help info about the program: python bomcheck.py

Run from a python console terminal like this: bomcheck('*', v=True)

This program was designed with the intent that the program "pyinstaller" be
able to create a self executing program from bomcheck.py.  In this case, the
python modules listed in the file "requirements.txt" must be present in the
environment in which self executing program is created.

Also, the file droplist.py should be present in a location that the bomcheck
program can find it.  Within the code of the function "getdroplist" is shown
the location where the file is looked for.
"""


__version__ = '1.0.1'
import glob, argparse, sys, warnings
import pandas as pd
import os.path
import tempfile
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)


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
    paths = ["I:/bomcheck/", "C:/tmp/", "I:/DVT-BOMCHECK/", "/home/ken/projects/project1/"]
    for p in paths:
        if os.path.exists(p) and not p in sys.path:
            sys.path.append(p)
            break
    try:
        import droplist
        drop = droplist.drop
        exceptions = droplist.exceptions
    except ModuleNotFoundError:
        print('\nFile droplist.py not found or corrupt.  Put it in the')
        print('directory I:\\bomcheck\n')
        drop = []   # If droplist.py not found, use this
        exceptions= []
        
        
getdroplist()       # create global variables named drop and exceptions


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
    dropcontents = 'drop: ' + str(drop) + ', exceptions: ' + str(exceptions)
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                        description='Program to compare SolidWorks BOMs to SyteLine BOMs')
    parser.add_argument('filename', help='Name of file containing a BOM.  Name ' +
                        'must end with _sw.xlsx, _sl.xlsx. _sw.csv, or ' +
                        '_sl.csv.  Enclose filename in quotes!  An asterisk, *, ' +
                        'caputures multiple files.  Examples: "6890-*", "*".  ' +
                        'Or if filename is a directory path, all _sw and _sl files ' +
                        'will be gathered from that directory.  ' +
                        '_sl files without a corresponding _sw file are ignored.  ' +
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
#    parser.add_argument('-1', --clipboard1, action='store_true', default=False,
#                        help='Allow import of a SolidWorks BOM from clipboard')
#    parser.add_argument('-2', --clipboard2, action='store_true', default=False,
#                        help='Allow import of a SyteLine BOM from clipboard')  
    parser.add_argument('-a', '--all', action='store_true', default=False,
                        help='Include in the check pns of the drop list')
    parser.add_argument('--version', action='version', version=__version__,
                        help="Show program's version number and exit")        
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
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
        print('\nNo sw or sl files found.  Check that you are working from the correct')
        print('directory.  Also check that files are named correctly (e.g. XXXXXX_sw.xlsx).\n')
        sys.exit()
     
    title_dfsw = list(map(lambda x: (x[0], sw(x[1], a)), swfiles)) # [(title, dfsw), ...]
    title_dfmerged = list(map(lambda x: (x[0], sl(sw(x[1], a), x[2])), pairedfiles)) # [(title, dfmerged), ...]

    if fn in ['1', '2']:
        sw_df = sw('clipboard', a)
        title_dfsw.append(('clipboard', sw_df))
    if fn == '2': 
        title_dfsw = []
        title_dfmerged.append(('clipboard', sl(sw_df, filename='clipboard')))
        
    try:    
        export2excel(dirname, 'bomcheck', title_dfsw + title_dfmerged)
    except PermissionError:
        print('\nError: unable to write to bomcheck.xlsx')
        
    results = {}
    for s in (title_dfsw + title_dfmerged):
        results[s[0]] = s[1]

    if v:
        print()
        for pn, bom in results.items():  # cycle through each pn and bom
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
            for idx, col in enumerate(df):  # set width of rest of columns  
                series = df[col]
                max_len = max((
                    series.astype(str).map(len).max(),  # len of largest item
                    len(str(series.name))  # len of the column's title
                    )) + 1  # adding a little extra space
                worksheet.set_column(idx+1, idx+1, max_len)  # set column width
        writer.save()
    abspath = os.path.abspath(fn)
    print("\nCreated file: " + abspath + '\n')


def gatherfilenames(filename):
    '''Gather names of excel files to be processed and return them in organized
    lists.  Names must end with `_sw.xlsx`, `_sl.xlsx`, `_sw.csv`, or `_sl.csv`

    Parmeters
    =========

    filename : string
        For example "C:/filepath/*".  The `*` means that from this directory 
        all Excel files ending with _sw.xlsx or _sl.xlsx will be gathered.

    Returns
    =======

    out : tuple with three elements
    
        - Tuple element 1: Name of working directory; that is, the dircectory
          containing _sw and _sl files, and where the bomcheck.xlsx file will
          be placed.  
        - Tuple element 2: A list of tuples, each tuple containing a title to 
          assign to result data, and also a name of a sw Excel or sw csv file 
          to which the title will apply.  (Only contains sw file names for
          which no corresonding sl file was found.)
        - Tuple element 3: A list of tuples, each containing three elements:
          1.  title to assign to data, 2. name of sw Excel or sw csv file,
          3. name of sl Excel or sl csv file.  (The sw file name corresponds
          to the sl file name.)
          
        If a sl (SyteLine) file exists, and if no correspoinding sw file
        was found to exist, then the sl file is ignored.
    
        The tuple has the form:
            
        (dirname, [(title1, swpathname1), ...], [(title2, swpathname2, slpathname2),...])
        
     \u2009
    '''
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        print('directory not found: ', dirname)
        sys.exit(0)
    gatherednames = sorted(glob.glob(filename))
    swfilenames_tmp = []
    for f in gatherednames:  # Grab a list of all the SW files that glob grabbed.
        i = f.rfind('_')
        if f[i:i+4].lower()=='_sw.':
            swfilenames_tmp.append(f)  # [/pathname/file1_sw.xlxs, ...,/pathname/fileN_sw.xlx]
    swfilenames = []
    pairedfilenames = []
    # go through the sw files.  Find the matching sl file for a given sw file
    for s in swfilenames_tmp:
        flag = True    # assume only a sw file exists...  that is, no matching sl file.
        j = s.rfind('_')  # this to truncate the sw filename; i.e. to git rid of _sw.xlsx
        for f in gatherednames:
            i = f.rfind('_')
            if f[i:i+4].lower()=='_sl.' and s[:j].lower()==f[:i].lower():  # found sw/sl match
                dname, fname = os.path.split(s)
                k = fname.rfind('_')
                fntrunc = fname[:k]  # Name of the sw file, excluding path, and excluding _sw.xlsx
                pairedfilenames.append((fntrunc, s, f))  # (title, sw pathname, sl pathname)
                flag = False  # sw file is not alone!
        if flag==True:  # sw file is alone... no matching sl file found.
            dname, fname = os.path.split(s)
            fname, ext = os.path.splitext(fname)
            swfilenames.append((fname, s))  #  (title, sw pathname)
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


def reverse(s):
   ''' Reverse a string.  For example, "abcde" to "edcba".
    
   Parameters
   ==========
   
   s : string
       String to be reversed:
           
   Returns
   =======
   
   out : string
       String s but with characters in reverse order.    
   '''
   str = "" 
   for i in s: 
       str = i + str
   return str


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
    data2 = list(map(lambda x: x.replace(',', ';') , data1)) # replace commas with semicolons
    # The last two columns in a SW BOM are always "Descrition" and "Part Number".
    # Reverse each line of data2 and "replace" (which works from the start
    # of a string to the end) the semicolons with commas up to postion i.
    # Then replace the comma between pn and descrip back to a semicolon.  
    # Finally reverse the string and append to the list named data.
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
         

def testcsv(filename):
    ''' Test so see if the number of commas in each row is the same or not.  
    For a comma delimited csv file the no. of commas in each row should be the
    same.  If not, a program crash occurs with an error message that can be 
    confusing to the user.  This function on the other hand gives a user
    friendly error message.  This type of failure typically occurs in a SW csv
    file since SL csv files do not use commas as a delimiter.”
    '''
    with open(filename, encoding="ISO-8859-1") as f:
        num = f.readline().count(',')  # get number of commas in 1st line of f
        failed_lines = [x for x in f if x.count(',') != num]
    if failed_lines:
        print('\nParsing Error.  Program halted.')
        print('File causing problem: ' + filename)
        print('Reason for failure: number of commas in each row of the file is not the same.')
        print('(Commas separate fields in the row.  Unequal commas represent unequal number')
        print('of fields.)  Most likely culprit: a comma within the part description,')
        print('e.g. “KIT, VMX0153 MECH SEAL”\n')
        print('Offendig line(s):')
        for j in failed_lines:
            print('  ', j)
    return failed_lines  # if list empty, equivalent to False, else True


def sw(filename='clipboard', a=False):
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

    filename : string
        Name of SolidWorks Excel file to process.  If filename = clipboard, the 
        sw bom is taken from the clipboard.

    a : bool
        use all; that is, disreguard using the drop list.  (See getdroplist()).
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
    _, ext = os.path.splitext(filename)
    try:
        if filename.lower() in ['c', 'x', 'cb', 'clipboard']:
            print('\nCopy SolidWorks BOM to clipboard (from xlxs file only) including the BOM header')
            input("Press the <ENTER> key to continue...")
            dfsw = pd.read_clipboard(engine='python', na_values=[' '], skiprows=1)
        elif str(type(filename))[-11:-2] == 'DataFrame':
            dfsw = filename
        elif ext=='.xlsx' or ext=='.xls':
            try:
                dfsw = pd.read_excel(filename, na_values=[' '], skiprows=1, engine='python')
            except:
                dfsw = pd.read_excel(filename, na_values=[' '], skiprows=1)
        elif False: #ext=='.csv':
            if testcsv(filename):
                sys.exit(1)
            else:
                dfsw = pd.read_csv(filename, na_values=[' '], skiprows=1,
                                   encoding='iso8859_1', engine='python')
        elif ext=='.csv':
            data = fixcsv(filename)
            temp = tempfile.TemporaryFile(mode='w+t')
            for d in data:
                temp.write(d)
            temp.seek(0)
            dfsw = pd.read_csv(temp, na_values=[' '], skiprows=1, sep=';',
                                   encoding='iso8859_1', engine='python')
            temp.close()
        else:
            print('non valid file name (', filename, ') (err 102)')
            sys.exit(0)

    except IOError:
        print('FILNAME NOT FOUND: ', filename)
        sys.exit(0)

    required_columns = [('QTY', 'QTY.'), 'DESCRIPTION', ('PART NUMBER', 'PARTNUMBER')]  # optional: LENGTH
    missing = test_columns(dfsw, required_columns)
    if missing:
        print('At least one column in your SW data (' + os.path.split(filename)[1] + ')  not found: ', missing)
        sys.exit()

    values = {'QTY':0, 'QTY.':0, 'LENGTH':0, 'DESCRIPTION': 'description missing', 'PART NUMBER': 'pn missing', 'PARTNUMBER': 'pn missing'} 
    dfsw.fillna(value=values, inplace=True)
    # obsolete: dfsw['DESCRIPTION'].replace(0, '!! No SW description provided !!', inplace=True)
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
            input("Press the <ENTER> key to continue...")
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
    main()                   # comment out this line for testing
    # bomcheck('*', v=True)   # use for testing


