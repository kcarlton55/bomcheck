#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 21:31:00 2019

@author: ken
"""

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
    parser.add_argument('-c', '--concatenate', action='store_false', default=True,
                        help='Ignore pns listed in the file droplist.py')
    parser.add_argument('-v', '--version', action='version', version=__version__,
                        help="Show program's version number and exit")      
    parser.add_argument('-a', '--about', action='version', version=about,
                        help="Show info about the program.")           
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()  
    bomcheck(args.filename, args.drop, args.concatenate) 


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
        
    if c==True:
    	title_dfsw, title_dfmerged = concat(title_dfsw, title_dfmerged) 
   
    try:    
        export2excel(dirname, 'bomcheck', title_dfsw + title_dfmerged)
    except PermissionError:
        print('\nError: unable to write to bomcheck.xlsx')
        
        
def about():
    print('This program was written by Ken Carlton, 2019')
    print('kencarlton55@gmail.com')
    print('Program written for: ')
    print('    Dekker Vacuum Technologies, Inc.')
    print('    935 S Woodland Ave')
    print('    Michigan City, IN 46360')
    print('Program compares two Bills of Material.  One is from a Microsoft Excel')
    print('sheet in which is a BOM from SolidWorks.  The other is from a')
    print('Microsoft Excel sheet in which is a BOM from SyteLine.')
       

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
        swresults.append(('SW BOM', dfswCCat.set_index(['assy', 'Op'])))
    if dfmergedDFrames:
        dfmergedCCat = pd.concat(dfmergedDFrames).reset_index() 
        mrgresults.append(('Merged BOMs', dfmergedCCat.set_index(['assy', 'Item'])))
    return swresults, mrgresults


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
        List of tuples.  Each tuple has two items.  The first item is a string
        and is the title, usually an assembly part number, given to the second
        item.  The second item is a DataFrame object for a BOM.  The list of 
        tuples are:
        
        1. Only SolidWorks BOMs, that have been converted to SyteLine format, 
        if no corresponding SyteLine BOM was found to compare it to; and/or
        
        2.  A list showing a comparison between a SolidWorks BOM and a SyteLine
        BOM.

    Returns
    =======

    out : Excel file (saved to disk)
        The Excel file shows on multiple sheets the "results2export" list.

     \u2009
    '''
    def autosize_excel_columns(worksheet, df):
        ''' Adjust column widith of an Excel worksheet
        (ref.: # https://stackoverflow.com/questions/17326973/
            is-there-a-way-to-auto-adjust-excel-column-widths-with-pandas-excelwriter)'''
        autosize_excel_columns_df(worksheet, df.index.to_frame())
        autosize_excel_columns_df(worksheet, df, offset=df.index.nlevels)
    
    def autosize_excel_columns_df(worksheet, df, offset=0):
        for idx, col in enumerate(df):
            x = 1  # add a little extra space if not column i, q, d, or u
            if len(df.columns[idx]) == 1:
                x = 0
            series = df[col]
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

    with pd.ExcelWriter(fn) as writer:
        for r in results2export:
            sheetname = r[0]
            df = r[1]
            df.to_excel(writer, sheet_name=sheetname)
            worksheet = writer.sheets[sheetname]  # pull worksheet object
            worksheet.hide_gridlines(2)  # see: https://xlsxwriter.readthedocs.io/page_setup.html
            autosize_excel_columns(worksheet, df)
        writer.save()
    abspath = os.path.abspath(fn)
    print("\nCreated file: " + abspath + '\n')
    
    if sys.platform[:3] == 'win':  # Open bomcheck.xlsx in Excel when on Windows platform
        try:
            os.startfile(abspath)
        except:
            print('Attempt to open bomcheck.xlsx in Excel failed.' )

        
