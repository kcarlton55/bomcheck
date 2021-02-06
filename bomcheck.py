#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File initial creation on Sun Nov 18 2018

@author: Kenneth E. Carlton

This program compares two BOMs: one originating from SolidWorks (SW) and the
other from SyteLine (SL).  The structure of the BOMs (headings, structure,
etc.) are very unique to my company.  Therefore this program, unaltered, will
fail to function at another company.  

Run this program from the command line like this: python bomcheck.py '*'

Without any arguments help info is shown: python bomcheck.py

Run from a python console terminal like this: bomcheck('*')

To see how to create an EXE file from this program, see the file named
howtocompile.md.
"""


__version__ = '1.7.5'
__author__ = 'Kenneth E. Carlton'
import glob, argparse, sys, warnings
import pandas as pd
import os.path
import os
import tempfile
import re
import datetime
import pytz
import fnmatch
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)


def get_version():
    return __version__


def set_globals():
    ''' Create a global variables including the primary one named cfg.
    cfg is a dictionary containing settings used by this program.
    
    set_globals() is ran when bomcheck first starts up.
    
    set_globals() tries to derive settings from the file named bc_bomcheck.py
    if it can be located and if values have been established there.
    Otherwise set_globals() creates its on settings for cfg.
    
    (see the function named create_bc_config to find where the file bc_check.py
     is located on you disk drive.)
    '''
    global cfg, printStrs, excelTitle
    try:
        create_bc_config()  # if bc_config.py file doen't exist, create a starter file
    except:
        pass
    cfg = {}
    printStrs = []
    excelTitle = []
    # try to import the file named bc_config.py.
    
    try:
        if sys.platform[:3] == 'win':
            datadir = os.getenv('"LOCALAPPDATA"')
            dirname = os.path.join(datadir, 'bomcheck')
            if os.path.exists(dirname) and not dirname in sys.path:
                sys.path.append(dirname)
        elif sys.platform[:3] == 'lin' or sys.platform[:3] == 'dar':
            homedir = os.path.expanduser('~')
            dirname = os.path.join(homedir, '.bomcheck')
            if os.path.exists(dirname) and not dirname in sys.path:
                sys.path.append(dirname)
        else:
            printStr = ('At function "set_globals", a suitable path was not found to\n'
                        'load bc_config.py from.  Notify the programmer of this error.')
            #printStrs.append(printStr)
            print(printStr) 
    except:
        pass
           
    try:
        import bc_config
    except ModuleNotFoundError:
        def bc_config():  # do this so that doing "dir(bc_config)" below doesn't fail
            pass

    cfg = {}
    cfg['col'] = {}
    def insert_into_cfg(var, default, col=False):
        ''' Function to insert key/value pairs into the dictionary named cfg.
        Use values set in the file named bc_config.py when available.'''
        global cfg
        if col: 
            value = bc_config.__dict__[var] if (var in dir(bc_config)) else default
            cfg['col'].update({var:value})
        else:                
            cfg[var] = bc_config.__dict__[var] if (var in dir(bc_config)) else default
           
    # default settings for bomcheck
    list1 = [('accuracy', 2),       ('discard_length', ['3086-*']), 
             ('drop', ['3*-025']),  ('exceptions', []), 
             ('from_um', 'inch'),   ('timezone', 'local'), # or 'US/Central', etc.),
             ('to_um', 'feet'),     ('skiprows_sw', 1), 
             ('skiprows_sl', 0)]
    # Give to bomcheck names of columns that it can expect to see in BOMs.  If
    # one of the names, except length names, in each group shown in brackets
    # below is not found, then bomcheck will fail.
    list2 = [('part_num',  ["PARTNUMBER", "PART NUMBER", "Part Number", "Item", "Material"]),
             ('qty',       ["QTY", "QTY.", "Qty", "Quantity", "Qty Per"]),
             ('descrip',   ["DESCRIPTION", "Material Description", "Description"]),
             ('um_sl',     ["UM", "U/M"]),     # not required in a SW BOM
             ('level_sl',  ["Level"]),         # not required in a SW BOM
             ('itm_sw',    ["ITEM NO."]),      # not required in a SL BOM
             ('length_sw', ["LENGTH", "Length", "L"])]  # not required in a SL or SW BOM
    
    # OK... Default values have just been set above, but look in the bc_confg.py 
    # file and use any values from there and override the values set above.
    for k, v in list1:
        insert_into_cfg(k, v)
    cfg['accuracy'] = int(cfg['accuracy'])     # make sure is an int and not a float
    cfg['skiprows_sw'] = int(cfg['skiprows_sw'])
    cfg['skiprows_sl'] = int(cfg['skiprows_sl'])
    for k, v in list2:
        insert_into_cfg(k, v, col=True)
                             
    
def showSettings():
    return cfg


def main():
    '''This fuction allows this bomcheck.py program to be run from the command
    line.  It is started automatically (via the "if __name__=='__main__'"
    command at the bottom of this file) when bomecheck.py is run.

    calls: bomcheck

    Examples
    ========

    $ python bomcheck.py "078551*"

    $ python bomcheck.py "C:/pathtomyfile/6890-*"

    $ python bomcheck.py "*"

    $ python bomcheck.py --help

    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                        description='Program compares SolidWorks BOMs to SyteLine BOMs.  ' +
                        'Output is sent to a Microsoft Excel spreadsheet.')
    parser.add_argument('filename', help='Name of file containing a BOM.  Name ' +
                        'must end with _sw.xlsx, _sl.xlsx. _sw.csv, or ' +
                        '_sl.csv.  Enclose filename in quotes!  An asterisk, *, ' +
                        'caputures multiple files.  Examples: "6890-*", "*".  ' +
                        'Or if filename is instead a directory, all _sw and _sl files ' +
                        'in that directory and subdirectories thereof will be ' +
                        'gathered.  BOMs gathered from _sl files without ' +
                        'corresponding SolidWorks BOMs found are ignored.')
    parser.add_argument('-d', '--drop_bool', action='store_true', default=False,
                        help='Ignore 3*-025 pns, i.e. do not use in the bom check')
    parser.add_argument('-c', '--sheets', action='store_true', default=False,
                        help='Break up results across multiple sheets in the ' +
                        'Excel file that is output.')
    parser.add_argument('-v', '--version', action='version', version=__version__,
                        help="Show program's version number and exit")
    parser.add_argument('-f', '--followlinks', action='store_false', default=True,
                        help='Follow symbolic links when searching for files to process.  ' +
                        "  (MS Windows doesn't honor this option.)")
    parser.add_argument('--from_um',  default=cfg['from_um'], help='The unit of measure ' +
                        'to apply to lengths in a SolidWorks BOM unless otherwise ' +
                        'specified', metavar='value')
    parser.add_argument('--to_um', default=cfg['to_um'], help='The unit of measure ' +
                        'to convert SolidWorks lengths to', metavar='value')
    parser.add_argument('-a', '--accuracy', help='Decimal place accuracy applied ' +
                        'to lengths in a SolidWorks BOM', default=cfg['accuracy'], 
                        metavar='value')
    parser.add_argument('-sr_sw', '--skiprows_sw', help='Number of rows to skip when ' +
                        'reading data from the Excel/csv files that contain SolidWorks BOMs.  ' +
                        'The first row to read from BOMs is meant to be the row containing ' +
                        ' column headings such as ITEM NO., QTY, PART NUMBER, etc.',
                        default=cfg['skiprows_sw'], metavar='value')
    parser.add_argument('-sr_sl', '--skiprows_sl', help='Number of rows to skip when ' +
                        'reading data from the Excel/csv files that contain SyteLine BOMs.  ' +
                        'The first row to read from BOMs is meant to be the row containing ' +
                        'column headings such as Item, Description, Qty Per, etc.', 
                        default=cfg['skiprows_sl'], metavar='value')
    parser.add_argument('-p', '--pause', help='Pause the program just before the program ' +
                        'the program would normally close after completing its work.',
                        default=False, action='store_true')
    
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    
    bomcheck(args.filename, vars(args))


def bomcheck(fn, dic={}, **kwargs):
    '''  
    This is the primary function of the bomcheck program and acts as a hub
    for other functions within the bomcheck program.  First to occur: Excel 
    and/or csv files that contain BOMs are opened.  Filenames containing BOMs 
    must end with _sw.xlsx,_sl.xlsx, _sw.csv, or _sl.csv; otherwise the files
    are ignored.  For a comparison between a SolidWorks (SW) BOM and a 
    SyteLine (SL) BOM to occur, filenames must be the same up until the 
    underscore (_) character of the filename.  E.g., 086677_sw.xlsx and 
    086677_sl.xlsx match.  By the way, an _sw.csv file will compare with a
    _sl.xlsx file, and vice versa.
    
    This function will also handle multilevel BOMs from SW and/or SL.  In which
    case subassembly BOMs will automatically be extracted to allow the BOM 
    check to occur.

    Any _sw files found for which no matching _sl file is found will be
    converted into a SyteLine like BOM format and output to an Excel file.
    If a _sl file is present for which no corresponding _sw file is found, 
    the _sl file is ignored; that is, no output... output is silent.

    After BOM merges occur, an Excel file is output containing the results. 
    The name of the Excel file is bomcheck.xlsx.  The results are the SW files
    for which no matching SL file was found, and also for the merged SW/SL 
    BOMs.  Finally this function will also return DataFrame objects of the 
    results.

    calls: gatherBOMs_from_fnames, collect_checked_boms, concat_boms, 
    export2excel, get_fnames

    Parmeters
    =========

    fn: string or list
        1.  Filename of Excel or csv files to do a BOM check on.  Default: "*"
            (i.e. all _sw & _sl files in the current working directory).
        2.  fn can be a directory name in which case all _sw and _sl files
            in that directory and subdirectories thereof are analyzed.
        3.  If a list is given, then it is a list of filenames and/or 
            directories.
        4.  An asterisk, *, matches any characters.  E.g. 6890-083544-* will
            match 6890-083544-1_sw.xlsx, 6890-083544-2_sw.xlsx, etc.
        
    dic: dictionary
        default: {}, i.e. an empty dictionary.  This variable is only used if
        the function "main" is used to run the bomcheck program; that is,
        the bomcheck program was inititiated from the command line.  If so,
        keys named "drop", "sheets", "from_um", and "to_um" and corresponding
        values thereof will have been put into dic.
        
    kwargs: dictionary
        Unlike dic, no values in kwargs are derived from the main function.
        This variable is used when bomcheck is run from a python console.  The
        dictionary key/value items that this function looks for are:

        c:  bool
            Break up results across multiple sheets within the bomcheck.xlsx
            file.  Default: False
    
        d: bool
            If True, employ the list named drop which will have been created by
            the function named "set_globals".  Default: False
            
        x: bool
            Export results to an Excel file named bomcheck.xlsx.  Default: True
    
        u: string
            Username.  This will be fed to the export2exel function so that a
            username will be placed into the footer of the bomcheck.xlsx file.
            Default: 'unknown'
            
        f: bool
            If True, follow symbolic links when searching for files to process.
            Default: False
    
    Returns
    =======

    out: tuple and an Excel file
        An Excel file is automatically created showing results of the bom 
        check.
    
        When c=False, returns a tuple containing two items:

            1.  One DataFrame object comprised of SW BOMs for which no
                matching SL BOMs were found.

            2.  One DataFrame object comprised of merged BOMs

        When c=True, no tuple is returned and the Excel file takes on a 
        different format as described above.

    Examples
    ========

    >>> bomcheck("078551*") # all file names beginning with characters: 078551

    >>> bomcheck("C:/folder/6890*")  # files names starting with 6890

    >>> bomcheck("*", d=True)   # all files in the current working directory

    >>> bomcheck("C:/folder") # all files in 'folder' and in subdirectories of
    
    >>> bomcheck("C:/folder/*") # all files, one level deep
    
    >>> bomcheck(["C:/folder1/*", "C:/folder2/*"], d=True, u="John Doe") 
    
    '''
    global printStrs, cfg
    printStrs = []
    # Set settings depending on 1. if input was derived from running this 
    # program from the command line (i.e. values from dic), 2. if from 
    # excecuting the bomcheck() function within a python console or called by
    # some other python function (i.e. from kwargs), or 3. if the settings were
    # imported from bc_config.py.  Many default values (e.g. cfg['from_um'])
    # were initially establisd by the set_globals() function.
    cfg['from_um'] = (dic.get('from_um') if dic.get('from_um')
                      else kwargs.get('from_um', cfg['from_um']))  
    cfg['to_um'] = (dic.get('to_um') if dic.get('to_um')
                    else kwargs.get('to_um', cfg['to_um']))
    cfg['accuracy'] = (dic.get('accuracy') if dic.get('accuracy')
                       else kwargs.get('a', cfg['accuracy']))
    cfg['drop_bool'] = (dic.get('drop_bool') if dic.get('drop_bool') 
                   else kwargs.get('d', False))
    cfg['skiprows_sw'] = (dic.get('skiprows_sw') if dic.get('skiprows_sw') 
                   else kwargs.get('sr_sw', cfg['skiprows_sw']))
    cfg['skiprows_sl'] = (dic.get('skiprows_sl') if dic.get('skiprows_sl') 
                   else kwargs.get('sr_sl', cfg['skiprows_sl']))
    c = (dic.get('sheets') if dic.get('sheets') else kwargs.get('c', False))
    u =  kwargs.get('u', 'unknown')  
    x = kwargs.get('x', True)
    f = kwargs.get('f', False)
    p = dic.get('pause', False)
    
    if isinstance(fn, str) and fn.startswith('[') and fn.endswith(']'):
        fn = eval(fn)  # change a string to a list
    elif isinstance(fn, str):
        fn = [fn]

    fn = get_fnames(fn, followlinks=f)  # get filenames with any extension.   
        
    #if cfg['drop']:
    #    printStr = '\ndrop = ' + str(cfg['drop']) + '\nexceptions = ' + str(cfg['exceptions']) + '\n'
    #    printStrs.append(printStr)
    #    print(printStr)

    dirname, swfiles, slfiles = gatherBOMs_from_fnames(fn)

    # lone_sw is a dic; Keys are assy nos; Values are DataFrame objects (SW 
    # BOMs only).  merged_sw2sl is a dic; Keys are assys nos; Values are 
    # Dataframe objects (merged SW and SL BOMs).
    lone_sw, merged_sw2sl = collect_checked_boms(swfiles, slfiles)

    title_dfsw = []                # Create a list of tuples: [(title, swbom)... ]
    for k, v in lone_sw.items():   # where "title" is is the title of the BOM,
        title_dfsw.append((k, v))  # usually the part no. of the BOM.

    title_dfmerged = []            # Create a list of tuples: [(title, mergedbom)... ]
    for k, v in merged_sw2sl.items():
        title_dfmerged.append((k, v)) 

    if title_dfsw:
        printStr = '\nNo matching SyteLine BOMs found for these SolidWorks files:\n'
        printStr += '\n'.join(list(map(lambda x: '    ' + x[0], title_dfsw))) + '\n'
        printStrs.append(printStr)
        print(printStr)

    if c == False:                 # concat_boms is a bomcheck function
    	title_dfsw, title_dfmerged = concat_boms(title_dfsw, title_dfmerged)

    if x:
        try:
            if title_dfsw or title_dfmerged:
                export2excel(dirname, 'bomcheck', title_dfsw + title_dfmerged, u)
            else:
                printStr = ('\nNo SolidWorks files found to process.  (Lone SyteLine\n' +
                            'BOMs will be ignored.)  Make sure file names end with\n' +
                            '_sw.xlsx, _sw.csv, _sl.xlsx, or _sl.csv.\n')
                printStrs.append(printStr)
                print(printStr)
        except PermissionError:
            printStr = '\nError: unable to write to bomcheck.xlsx\n'
            printStrs.append(printStr)
            print(printStr)
      
    if p == True:        
            input("Press enter to exit")
            
    return printStrs
            
# =============================================================================
#     if c == False:
#         if title_dfsw and title_dfmerged:
#             return title_dfsw[0][1], title_dfmerged[0][1]
#         elif title_dfsw:
#             return title_dfsw[0][1], None
#         elif title_dfmerged:
#             return None, title_dfmerged[0][1]
#         else:
#             return None, None
# =============================================================================
        


def get_fnames(fn, followlinks=False):
    ''' Interpret fn to get a list of filenames based on fn's value.  
    
    Parameters
    ----------
    fn: str or list
        fn is a filename or a list of filenames.  A filename can also be a
        directory name.  Example 1, strings: "C:/myfile_.xlsx", "C:/dirname", 
        "['filename1', 'filename2', 'dirname1' ...]". Example 2, list:
        ["filename1", "filename2", "dirname1", "dirname2"].  When a a directory
        name is given, filenames are gathered from that directory and from 
        subdirectories thereof.
    followlinks: Boolean, optional
        If True, follow symbolic links. If a link is to a direcory, then
        filenames are gathered from that directory and from subdirectories
        thereof.  The default is False.  

    Returns
    -------
    _fn: list
        A list of filenames, e.g. ["filename1", "filename2", ...].  Each value
        in the list is a string.  Each string is the name of a file.  The
        filename can be a pathname, e.g. "C:/dir1/dir2/filename".  The
        filenames can have any type of extension.
    '''
    if isinstance(fn, str) and fn.startswith('[') and fn.endswith(']'):
            fn = eval(fn)  # if fn a string like "['fname1', 'fname2', ...]", convert to a list
    elif isinstance(fn, str):
        fn = [fn]   # fn a string like "fname1", convert to a list like [fname1]
        
    _fn1 = [] 
    for f in fn:
        _fn1 += glob.glob(f)
        
    _fn2 = []    # temporary holder
    for f in _fn1:
        if followlinks==True and os.path.islink(f) and os.path.exists(f):
            _fn2 += get_fnames(os.readlink(f))              
        elif os.path.isdir(f):  # if a dir, gather all filenames in dirs and subdirs thereof
            for root, dirs, files in os.walk(f, followlinks=followlinks):
                for filename in files:
                  _fn2.append(os.path.join(root, filename))  
        else:
            _fn2.append(f) 
            
    return _fn2


def make_csv_file_stable(filename):
    ''' Except for any commas in a parts DESCRIPTION, replace all commas
    in a csv file with a $ character.  Commas will sometimes exist in a
    DESCRIPTION field, e.g, "TANK, 60GAL".  But commas are intended to be field
    delimeters; commas in a DESCRIPTION field are not.  Excess commas in
    a line from a csv file will cause a program crash.  Remedy: change those 
    commas meant to be delimiters to a dollor sign character, $.
        
    Parmeters
    =========

    filename: string
        Name of SolidWorks csv file to process.

    Returns
    =======

    out: list
        A list of all the lines (rows) in filename is returned.  Commas in each
        line are changed to dollar signs except for any commas in the
        DESCRIPTION field.
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


def gatherBOMs_from_fnames(filename):
    ''' Gather all SolidWorks and SyteLine BOMs derived from "filename".
    "filename" can be a string containing wildcards, e.g. 6890-085555-*, which
    allows the capture of multiple files; or "filename" can be a list of such
    strings.  These files (BOMs) will be converted to Pandas DataFrame objects.

    Only files prefixed with _sw.xlsx, _sw.csv, _sl.xlsx, or _sl.csv will be
    chosen; others are discarded.  These files will then be converted into two
    python dictionaries.  One dictionary will contain SolidWorks BOMs only, and
    the other will contain only SyteLine BOMs.

    If a filename has a BOM containing a multiple level BOM, then the 
    subassembly BOMs will be extracted from that BOM and be added to the 
    dictionaries.

    calls: make_csv_file_stable, deconstructMultilevelBOM, test_for_missing_columns

    Parmeters
    =========

    filename: list
        List of filenames to be analyzed.

    Returns
    =======

    out: tuple
        The output tuple contains three items.  The first is the directory
        corresponding to the first file in the filename list.  If this
        directory is an empty string, then it refers to the current working
        directory.  The remainder of the tuple items are two python 
        dictionaries. The first dictionary contains SolidWorks BOMs, and the 
        second contains SyteLine BOMs.  The keys for these two dictionaries 
        are part nos. of assemblies derived from the filenames (e.g. 085952 
        from 085953_sw.xlsx), or derived from subassembly part numbers of a
        file containing multilevel BOM.
    '''
    dirname = '.'  # to this will assign the name of 1st directory a _sw is found in 
    global printStrs
    swfilesdic = {}
    slfilesdic = {}
    for f in filename:  # from filename extract all _sw & _sl files and put into swfilesdic & slfilesdic
        i = f.rfind('_')
        if f[i:i+4].lower() == '_sw.' or f[i:i+4].lower() == '_sl.':
            dname, fname = os.path.split(f)
            k = fname.rfind('_')
            fntrunc = fname[:k]  # Name of the sw file, excluding path, and excluding _sw.xlsx
            if f[i:i+4].lower() == '_sw.' and '~' not in fname: # Ignore names like ~$085637_sw.xlsx
                swfilesdic.update({fntrunc: f})
                if dirname == '.':
                    dirname = os.path.dirname(os.path.abspath(f)) # use 1st dir where a _sw file is found to put bomcheck.xlsx
            elif f[i:i+4].lower() == '_sl.' and '~' not in fname:
                slfilesdic.update({fntrunc: f})    
    swdfsdic = {}  # for collecting SW BOMs to a dic
    for k, v in swfilesdic.items():
        try:
            _, file_extension = os.path.splitext(v)
            if file_extension.lower() == '.csv' or file_extension.lower() == '.txt':
                data = make_csv_file_stable(v)
                temp = tempfile.TemporaryFile(mode='w+t')
                for d in data:
                    temp.write(d)
                temp.seek(0)
                df = pd.read_csv(temp, na_values=[' '], skiprows=cfg['skiprows_sw'], sep='$',
                                 encoding='iso8859_1', engine='python',
                                 dtype = dict.fromkeys(cfg['col']['itm_sw'], 'str'))
                temp.close()
            elif file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
                df = pd.read_excel(v, na_values=[' '], skiprows=cfg['skiprows_sw'])
                colnames = []
                for colname in df.columns:  # rid colname of '\n' char if exists
                    colnames.append(colname.replace('\n', ''))
                df.columns = colnames
            if not test_for_missing_columns('sw', df, k):
                swdfsdic.update(deconstructMultilevelBOM(df, 'sw', k))
        except:
            printStr = '\nError processing file: ' + v + '\nIt has been excluded from the BOM check.\n'
            printStrs.append(printStr)
            print(printStr)
    sldfsdic = {}  # for collecting SL BOMs to a dic
    for k, v in slfilesdic.items():
        try:
            _, file_extension = os.path.splitext(v)
            if file_extension.lower() == '.csv' or file_extension.lower() == '.txt':
                try:
                    df = pd.read_csv(v, na_values=[' '], engine='python', 
                                     skiprows=cfg['skiprows_sl'],
                                     encoding='utf-16', sep='\t')
                except UnicodeError:
                    printStr = ("\nError. Probable cause: This program expects Unicode text encoding from\n"
                                "a csv file.  The file " + v + " does not have this.  The\n"
                                "correct way to achieve a functional csv file is:\n\n"
                                '    From Excel, save the file as type “Unicode Text (*.txt)”, and then\n'
                                '    change the file extension from txt to csv.\n\n'
                                "On the other hand you can use an Excel file (.xlsx) instead of a csv file.\n")
                    printStrs.append(printStr)
                    print(printStr)
                    sys.exit(1)
            elif file_extension.lower() == '.xlsx' or file_extension.lower == '.xls':
                df = pd.read_excel(v, na_values=[' '], skiprows=cfg['skiprows_sl'])
                
            if not (test_for_missing_columns('sl', df, k) and 
                    cfg['col']['level_sl'] in df.columns):
                sldfsdic.update(deconstructMultilevelBOM(df, 'sl', 'TOPLEVEL'))
            elif not test_for_missing_columns('sl', df, k):
                sldfsdic.update(deconstructMultilevelBOM(df, 'sl', k))
        except:
            printStr = '\nError processing file: ' + v + '\nIt has been excluded from the BOM check.\n'
            printStrs.append(printStr)
            print(printStr)
    try:
        df = pd.read_clipboard(engine='python', na_values=[' '])
        if not test_for_missing_columns('sl', df, 'BOMfromClipboard', printerror=False):
            sldfsdic.update(deconstructMultilevelBOM(df, 'sl', 'TOPLEVEL'))
    except:
        pass
    if os.path.islink(dirname):
        dirname = os.readlink(dirname)
    return dirname, swdfsdic, sldfsdic


def test_for_missing_columns(bomtype, df, pn, printerror=True):
    ''' SolidWorks and SyteLine BOMs require certain essential columns to be
    present.  This function looks at those BOMs that are within df to see if
    any required columns are missing.  If found, print to screen.

    calls: test_alternative_column_names

    Parameters
    ==========

    bomtype: string
        "sw" or "sl"

    df: Pandas DataFRame
        A SW or SL BOM

    pn: string
        Part number of the BOM

    Returns
    =======

    out: bool
        True if BOM afoul.  Otherwise False.
    '''
    global printStrs
    if bomtype == 'sw':
        required_columns = [cfg['col']['qty'], cfg['col']['descrip'],
                            cfg['col']['part_num'], cfg['col']['itm_sw']]
    else: # 'for sl bom'
        required_columns = [cfg['col']['qty'], cfg['col']['descrip'],
                            cfg['col']['part_num'], cfg['col']['um_sl']]
            
    missing = []
    for r in required_columns:
        if isinstance(r, str) and r not in df.columns:
            missing.append(r)
        elif isinstance(r, list) and test_alternative_column_names(r, df.columns):
            missing.append(' or '.join(test_alternative_column_names(r, df.columns)))
    if missing and bomtype=='sw' and printerror:
        printStr = ('\nEssential BOM columns missing.  SolidWorks requires a BOM header\n' +
              'to be in place.  This BOM will not be processed:\n\n' +
              '    missing: ' + ' ,'.join(missing) +  '\n' +
              '    missing in: ' + pn + '\n') 
        printStrs.append(printStr)
        print(printStr)
        return True
    elif missing and printerror:
        printStr = ('\nEssential BOM columns missing.  This BOM will not be processed:\n' +
                    '    missing: ' + ' ,'.join(missing) +  '\n\n' +
                    '    missing in: ' + pn + '\n')
        printStrs.append(printStr)
        print(printStr)
        return True
    elif missing:
        return True
    else:
        return False


def test_alternative_column_names(tpl, lst):
    ''' tpl contains alternative names for a required column in a bom.  If 
    none of the names in tpl match a name in lst, return tpl so that the
    user can be notified that one of those alternative names should have been
    present.  On the other hand, if a match was found, return None.
    
    Parameters
    ==========
    tpl: tuple or list
        Each item of tpl is a string.  Each item is an alternative column name,
        e.g. ("Qty", "Quantity")
       
    lst: list
        A list of the required columns that a bom must have in order for a bom
        check to be correctly completed.
        
    Returns
    =======
    out: tpl|None
        If no match found, return the same tuple, tpl, that was an input
        parameter.  Else return None
    '''
    flag = True
    for t in tpl:
        if t in lst:
            flag = False  # A required column name was found in the tuple, so good to proceed with bom check
    if flag:
        return tpl  # one of the tuple items is a required column.  Report that one or the other is missing


def col_name(df, col):
    '''
    Parameters
    ----------
    df: Pandas DataFrame
        
    col: list
        List of column names that will be compared to the list of column
        names from df (i.e. from df.columns)

    Returns
    -------
    out: string
        Name of column that is common to both df.columns and col
    '''
    try:
        df_cols_as_set = set(list(df.columns))
        intersect = df_cols_as_set.intersection(col)
        return list(intersect)[0]
    except IndexError:
        return ""


def deconstructMultilevelBOM(df, source, top='TOPLEVEL'):
    ''' If the BOM is a multilevel BOM, pull out the BOMs thereof; that is,
    pull out the main assembly and the subassemblies thereof.  These
    assys/subassys are placed in a python dictionary and returned.  If df is
    a single level BOM, a dictionary with one item is returned.

    For this function to pull out subassembly BOMs from a SyteLine BOM, the
    column named Level must exist in the SyteLine BOM.  It contains integers
    indicating the level of a subassemby within the BOM; e.g. 1, 2, 3, 2, 3,
    3, 3, 4, 4, 2.  Only multilevel SyteLine BOMs contain this column.
    On the other hand for this function to  pull out subassemblies from a
    SolidWorks BOM, the column ITEM NO. (see set_globals() for other optional
    names) must exist and contain values that indicate which values are 
    subassemblies; e.g, with item numbers like "1, 2, 2.1, 2.2, 3, 4, etc.,
    items 2.1 and 2.2 are members of the item number 2 subassembly.

    Parmeters
    =========

    df: Pandas DataFrame
        The DataFrame is that of a SolidWorks or SyteLine BOM.
        
    source: string
        Choices for source are "sw" or "sl".  That is, is the BOM being
        deconstructed from SolidWorks or SyteLine.

    top: string
        Top level part number.  This number is automatically generated by the
        bomcheck program in two ways:  1. If df originated from a SolidWorks 
        BOM or from a single level SyteLine  BOM, then “top” is derived from 
        the filename; e.g. 091828 from the filename 091828_sw.xlsx.  2. If df
        originated from a multilevel BOM, then it has a column named “Level”
        (i.e. the level of subassemblies and parts within subassemblies
        relative to the main, top, assembly part number).  In this case the
        part number associated with level "0" is assigned to "top".

    Returns
    =======

    out: python dictionary
        The dictionary has the form {assypn1: BOM1, assypn2: BOM2, ...},
        where assypn1, assypn2, etc. are string objects and are the part
        numbers for BOMs; and BOM1, BOM2, etc. are pandas DataFrame objects
        that pertain to those part numbers.
    '''
    __lvl = col_name(df, cfg['col']['level_sl'])
    __itm = col_name(df, cfg['col']['itm_sw'])
    __pn = col_name(df, cfg['col']['part_num'])  # get the column name for pns
    
    p = None 
    df[__pn] = df[__pn].astype('str').str.strip() # make sure pt nos. are "clean"
    df[__pn].replace('', 'no pn from BOM!', inplace=True)
          
    # https://stackoverflow.com/questions/2974022/is-it-possible-to-assign-the-same-value-to-multiple-keys-in-a-dict-object-at-onc
    values = dict.fromkeys((cfg['col']['qty'] + cfg['col']['length_sw']), 0)
    values.update(dict.fromkeys(cfg['col']['descrip'], 'no descrip from BOM!'))
    values.update(dict.fromkeys(cfg['col']['part_num'], 'no pn from BOM!'))
    df.fillna(value=values, inplace=True)
   
    # Generate a column named __Level which contains integers based based upon
    # the level of a part within within an assembly or within subassembly of
    # an assembly. 0 is the top level assembly, 1 is a part or subassembly one 
    # level deep, and 2, 3, etc. are levels within subassemblies. 
    if source=='sw' and __itm and __itm in df.columns:
        __itm = df[__itm].astype('str')
        __itm = __itm.str.replace('.0', '') # stop something like 5.0 from slipping through
        df['__Level'] = __itm.str.count('\.') # level is the number of periods (.) in the string
    elif source=='sl' and __lvl and __lvl in df.columns:
        df['__Level'] = df[__lvl]
    else:
        df['__Level'] = 0 
          
    # Take the the column named "__Level" and create a new column: "Level_pn".
    # Instead of the level at which a part exists within an assembly, like
    # "__Level" which contains integers like [0, 1, 2, 2, 1], "Level_pn" contains
    # the parent part no. of the part at a particular level, e.g.
    # ['TOPLEVEL', '068278', '2648-0300-001', '2648-0300-001', '068278']
    lvl = 0
    level_pn = []  # storage of pns of parent assy/subassy of the part at rows 0, 1, 2, 3, ...
    assys = []  # storage of all assys/subassys found (stand alone parts ignored)
    for item, row in df.iterrows():
        if row['__Level'] == 0:
            poplist = []
            level_pn.append(top)
            if top != "TOPLEVEL":
                assys.append(top)
            elif 'Description' in df.columns and lvl == 0:
                excelTitle.append((row[__pn], row['Description'])) # info for a global variable
        elif row['__Level'] > lvl:
            if p in assys:
                poplist.append('repeat')
            else:
                assys.append(p)
                poplist.append(p)
            level_pn.append(poplist[-1])
        elif row['__Level'] == lvl:
            level_pn.append(poplist[-1])
        elif row['__Level'] < lvl:
            i = row['__Level'] - lvl  # how much to pop.  i is a negative number.
            poplist = poplist[:i]   # remove, i.e. pop, i items from end of list
            level_pn.append(poplist[-1])
        p = row[__pn]
        lvl = row['__Level']
    df['Level_pn'] = level_pn
    # collect all assys/subassys within df and return a dictionary.  keys
    # of the dictionary are pt. numbers of assys/subassys.  
    dic_assys = {}
    for k in assys:
        dic_assys[k.upper()] = df[df['Level_pn'] == k]
    return dic_assys


def create_um_factors(ser, from_um='inch', to_um='feet'):
    ''' From ser derive multiplication factors that will convert length values
    with a particular unit of measure (um) to to_um.  Some items of ser have a
    um values appended to it; for example 1105mm.  In this case the factor will
    be based on that um.  If no um is specified, it's derived from from_um. 

    Parmeters
    =========
    
    ser:  Pandas Series
        The data from the column that contains lengths from a SolidWorks BOM.

    from_um: str
        Use this unit of measure to convert from unless otherwised specified.  
        Valid units of measure: "inch", "feet", "yard", "millimeter", 
        "centimeter", "meter" (or abreviations thereof, e.g. mm).
        Default: "inch".

    to_um: str
        Convert to this unit of measure.  The same valid units of measure
        listed above apply.  Default: "feet"
    
    Returns
    =======

    out: list   
        multiplcation factors (list of floats)          
    '''
    factorpool = (('in', 1/12),      ('ft', 1.0),      ('mm', 1/(25.4*12)),
                  ('"', 1/12),       ("'", 1.0),       ('milli', 1/(25.4*12)),
                  (chr(8221), 1/12), (chr(8217), 1.0), ('cm', 10/(25.4*12)),
                  ('yard', 3.0),     ('foot', 1.0),    ('centi', 10/(25.4*12)),
                  ('yd', 3.0),       ('feet', 1.0),    ('m', 1000/(25.4*12)))
 
    # determine from_um_factor
    for k, v in factorpool:
        if k in from_um.lower():
            from_um_factor = v
            break
    else:
        from_um_factor = 1/12

    # determine to_um_factor
    for k, v in factorpool:
        if k in to_um.lower():
            to_um_factor = 1/v
            break
    else:
        to_um_factor = 1.0

    lengths = ser.fillna(0).tolist()
    factors = []
    for length in lengths:
        if isinstance(length, str):  # if UM explicitly stated, e.g. "34.3 MM"
           for k, v in factorpool:
                if k in length.lower():
                    from_factor = v
                    break
           else:
               from_factor = from_um_factor
        elif isinstance(length, float) or isinstance(length, int):
            from_factor = from_um_factor
        else:
            from_factor = 0
        factors.append(from_factor * to_um_factor)
        
    return factors


def is_in(find, xcept, series):
    '''Argument "find" is a list of strings that are glob expressions.  The 
    Pandas Series "series" will be evaluated to see if any members of find
    exists as substrings within each member of series.  Glob expressions are
    strings like '3086-*-025' or *2020*.  '3086-*-025' for example will match 
    '3086-0050-025' and '3086-0215-025'.
    
    The output of the is_in function is a Pandas Series.  Each member of the
    Series is True or False depending on whether a substring has been found
    or not.
        
    xcept is a list of exceptions to those in the find list.  For example, if
    '3086-*-025' is in the find list and '3086-3*-025' is in the xcept list,
    then series members like '3086-0515-025' or '3086-0560-025' will return
    a True, and '3086-3050-025' or '3086-3060-025' will return a False.
    
    For reference, glob expressions are explained at:
    https://en.wikipedia.org/wiki/Glob_(programming)
    
    Parmeters
    =========
    
    find: string or list of strings
        Items to search for
        
    xcept: string or list of strings
        Exceptions to items to search for

    series:  Pandas Series
       Series to search

    Returns
    =======

    out: Pandas Series, dtype: bool
        Each item is True or False depending on whether a match was found or not
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


def convert_sw_bom_to_sl_format(df):
    '''Take a SolidWorks BOM and restructure it to be like that of a SyteLine
    BOM.  That is, the following is done:

    - For parts with a length provided, the length is converted from from_um to 
      to_um (see the function main for a definition of these variables).
      Typically the unit of measure in a SolidWorks BOM is inches, and in 
      SyteLine, feet.
    - If the part is a pipe or beam and it is listed multiple times in the BOM,
      the BOM is updated so that only one listing is shown and the lengths
      of the removed listings are added to the remaining listing.
    - Similar to above, parts such as pipe nipples will show up more that
      once on a BOM.  Remove the excess listings and add the quantities of
      the removed listings to the remaining listing.
    - If global variable cfg['drop'] is set to True, off the shelf parts, which 
      are usually pipe fittings, are removed from the SolidWorks BOM.  (As a
      general rule, off-the-shelf parts are not shown on SyteLine BOMs.)  The 
      list that  governs this rule is in a file named drop.py.  Other part nos.
      may be added to this list as required.  (see the function set_globals
      for more information)
    - Column titles are changed to match those of SyteLine and thus will allow
      merging to a SyteLine BOM.
      
    calls: create_um_factors

    Parmeters
    =========

    df: Pandas DataFrame
        SolidWorks DataFrame object to process.

    Returns
    =======

    out: pandas DataFrame
        A SolidWorks BOM with a structure like that of SyteLine.

    \u2009
    '''
    
    values = dict.fromkeys(cfg['col']['part_num'], 'Item')
    values.update(dict.fromkeys(cfg['col']['length_sw'], 'LENGTH'))
    values.update(dict.fromkeys(cfg['col']['descrip'], 'Description'))
    values.update(dict.fromkeys(cfg['col']['qty'], 'Q'))
    df.rename(columns=values, inplace=True)        
    
    if 'LENGTH' in df.columns:  # convert lengths to other unit of measure, i.e. to_um
        factors = create_um_factors(df['LENGTH'], from_um=cfg['from_um'], to_um=cfg['to_um'])
        qtys = df['Q']
        lengths = df['LENGTH'].replace('[^\d.]', '', regex=True).astype(float)               
        discard_length_filter = ~is_in(cfg['discard_length'], [], df['Item'])
        df['LENGTH'] = lengths * qtys * factors * discard_length_filter
        filtr2 = df['LENGTH'] >= 0.00001
        df['Q'] = df['Q']*(~filtr2) + df['LENGTH']  # move lengths to the Qty column
        df['U'] = filtr2.apply(lambda x: 'FT' if x else 'EA')  # set the unit of measure
    else:
        df['U'] = 'EA'  # if no length colunm exists then set all units of measure to EA
    
    df = df.reindex(['Op', 'WC','Item', 'Q', 'Description', 'U'], axis=1)  # rename and/or remove columns
    dd = {'Q': 'sum', 'Description': 'first', 'U': 'first'}   # funtions to apply to next line
    df = df.groupby('Item', as_index=False).aggregate(dd).reindex(columns=df.columns)
    df['Q'] = round(df['Q'], cfg['accuracy'])

    if cfg['drop_bool']==True:
        filtr3 = is_in(cfg['drop'], cfg['exceptions'], df['Item'])
        df.drop(df[filtr3].index, inplace=True)

    df['WC'] = 'PICK'    # WC is a standard column shown in a SL BOM.
    df['Op'] = 10   # Op is a standard column shown in a SL BOM, usually set to 10  
    df.set_index('Op', inplace=True)
    
    return df


def check_a_sw_bom_to_a_sl_bom(dfsw, dfsl):
    '''This function takes in one SW BOM and one SL BOM and then merges them.
    This merged BOM shows the BOM check allowing differences between the
    SW and SL BOMs to be easily seen.

    A set of columns in the output are labeled i, q, d, and u.  Xs at a row in
    any of these columns indicate something didn't match up between the SW
    and SL BOMs.  An X in the i column means the SW and SL Items (i.e. pns)
    don't match.  q means quantity, d means description, u means unit of
    measure.

    Parmeters
    =========

    dfsw: Pandas DataFrame
        A DataFrame of a SolidWorks BOM

    dfsl: Pandas DataFrame
        A DataFrame of a SyteLine BOM

    Returns
    =======

    df_merged: Pandas DataFrame
        df_merged is a DataFrame that shows a side-by-side comparison of a
        SolidWorks BOM to a SyteLine BOM.

    \u2009
    '''
    global printStrs
    if not str(type(dfsw))[-11:-2] == 'DataFrame':
        printStr = '\nProgram halted.  A fault with SolidWorks DataFrame occurred.\n'
        printStrs.append(printStr)
        print(printStr)
        sys.exit()

    # A BOM can be derived from different locations within SL.  From one location
    # the `Item` is the part number.  From another `Material` is the part number.
    # When `Material` is the part number, a useless 'Item' column is also present.
    # It causes the bomcheck program confusion and the program crashes.  Thus a fix:
    if 'Item' in dfsl.columns and 'Material' in dfsl.columns:
        dfsl.drop(['Item'], axis=1, inplace=True)  # the "drop" here is not that in the cfg dictionary
    if 'Description' in dfsl.columns and 'Material Description' in dfsl.columns:
        dfsl.drop(['Description'], axis=1, inplace=True)
            
    values = dict.fromkeys(cfg['col']['part_num'], 'Item')
    values.update(dict.fromkeys(cfg['col']['um_sl'], 'U'))
    values.update(dict.fromkeys(cfg['col']['descrip'], 'Description'))
    values.update(dict.fromkeys(cfg['col']['qty'], 'Q'))
    values.update({'Obsolete Date': 'Obsolete'})
    dfsl.rename(columns=values, inplace=True)       
    
    if 'Obsolete' in dfsl.columns:  # Don't use any obsolete pns (even though shown in the SL BOM)
        filtr4 = dfsl['Obsolete'].notnull()
        dfsl.drop(dfsl[filtr4].index, inplace=True)    # https://stackoverflow.com/questions/13851535/how-to-delete-rows-from-a-pandas-dataframe-based-on-a-conditional-expression

    # When pns are input into SyteLine, all the characters of pns should
    # be upper case.  But on occasion people have mistakently used lower case.
    # Correct this and report what pns have been in error.
    x = dfsl['Item'].copy()
    dfsl['Item'] = dfsl['Item'].str.upper()  # make characters upper case
    x_bool =  x != dfsl['Item']
    x_lst = [i for i in list(x*x_bool) if i]
    if x_lst:
        printStr = ("\nLower case part nos. in SyteLine's BOM have been converted " +
                    "to upper case for \nthis BOM check:\n")
        printStrs.append(printStr)
        print(printStr)
        for y in x_lst:
            printStr = '    ' + y + '  changed to  ' + y.upper() + '\n'
            printStrs.append(printStr)
            print(printStr)

    dfmerged = pd.merge(dfsw, dfsl, on='Item', how='outer', suffixes=('_sw', '_sl') ,indicator=True)
    dfmerged.sort_values(by=['Item'], inplace=True)
    filtrI = dfmerged['_merge'].str.contains('both')  # this filter determines if pn in both SW and SL
    filtrQ = abs(dfmerged['Q_sw'] - dfmerged['Q_sl']) < .0051  # If diff in qty greater than this value, show X
    filtrM = dfmerged['Description_sw'].str.split() == dfmerged['Description_sl'].str.split()
    filtrU = dfmerged['U_sw'].astype('str').str.strip() == dfmerged['U_sl'].astype('str').str.strip()
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

    dfmerged = dfmerged[['Item', 'i', 'q', 'd', 'u', 'Q_sw', 'Q_sl',
                         'Description_sw', 'Description_sl', 'U_sw', 'U_sl']]
    dfmerged.fillna('', inplace=True)
    dfmerged.set_index('Item', inplace=True)
    return dfmerged


def collect_checked_boms(swdic, sldic):
    ''' Match SolidWorks assembly nos. to those from SyteLine and then merge
    their BOMs to create a BOM check.  For any SolidWorks BOMs for which no
    SyteLine BOM was found, put those in a separate dictionary for output.

    calls: convert_sw_bom_to_sl_format, check_a_sw_bom_to_a_sl_bom

    Parameters
    ==========

    swdic: dictionary
        Dictinary of SolidWorks BOMs.  Dictionary keys are strings and they
        are of assembly part numbers.  Dictionary values are pandas DataFrame
        objects which are BOMs for those assembly pns.

    sldic: dictionary
        Dictinary of SyteLine BOMs.  Dictionary keys are strings and they
        are of assembly part numbers.  Dictionary values are pandas DataFrame
        objects which are BOMs for those assembly pns.

    Returns
    =======

    out: tuple
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
            combined_dic[key] = check_a_sw_bom_to_a_sl_bom(convert_sw_bom_to_sl_format(dfsw), sldic[key])
        else:
            lone_sw_dic[key + '_sw'] = convert_sw_bom_to_sl_format(dfsw)
    return lone_sw_dic, combined_dic


def concat_boms(title_dfsw, title_dfmerged):
    ''' Concatenate all the SW BOMs into one long list (if there are any SW
    BOMs without a matching SL BOM being found), and concatenate all the merged
    SW/SL BOMs into another long list.

    Each BOM, before concatenation, will get a new column added: assy.  Values
    for assy will all be the same for a given BOM: the pn (a string) of the BOM.
    BOMs are then concatenated.  Finally Pandas set_index function will applied
    to the assy column resulting in the ouput being categorized by the assy pn.


    Parameters
    ==========

    title_dfsw: list
        A list of tuples, each tuple has two items: a string and a DataFrame.
        The string is the assy pn for the DataFrame.  The DataFrame is that
        derived from a SW BOM.

    title_dfmerged: list
        A list of tuples, each tuple has two items: a string and a DataFrame.
        The string is the assy pn for the DataFrame.  The DataFrame is that
        derived from a merged SW/SL BOM.

    Returns
    =======

    out: tuple
        The output is a tuple comprised of two items.  Each item is a list.
        Each list contains one item: a tuple.  The structure has the form:

            ``out = ([("SW BOMS", DataFrame1)], [("BOM Check", DataFrame2)])``

    Where...    
        "SW BOMS" is the title. (when c=True in the bomcheck function, the
        title will be an assembly part no.).  
        DataFrame1 = SW BOMs that have been concatenated together.

        "BOM Check" is another title.  
        DataFrame2 = Merged SW/SL BOMs that have been concatenated together.
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
        swresults.append(('SW BOMs', dfswCCat.set_index(['assy', 'Op']).sort_index(axis=0)))
    if dfmergedDFrames:
        dfmergedCCat = pd.concat(dfmergedDFrames).reset_index()
        mrgresults.append(('BOM Check', dfmergedCCat.set_index(['assy', 'Item']).sort_index(axis=0)))
    return swresults, mrgresults


def export2excel(dirname, filename, results2export, uname):
    '''Export to an Excel file the results of all the BOM checks.

    calls: len2, autosize_excel_columns, autosize_excel_column_df, definefn...
    (these functions are defined internally within the export2exel function)

    Parmeters
    =========

    dirname: string
        The directory to which the Excel file that this function generates
        will be sent.

    filename: string
        The name of the Excel file.

    results2export: list
        List of tuples.  The number of tuples in the list varies according to
        the number of BOMs analyzed, and if bomcheck's c (sheets) option was
        invoked or not.  Each tuple has two items.  The  first item of a tuple
        is a string and is the name to be assigned to the tab of the Excel
        worksheet.  It is typically an assembly part number.  The second  item
        is a BOM (a DataFrame object).  The list of tuples consists of:

        *1* SolidWorks BOMs that have been converted to SyteLine format.  SW
        BOMs will only occur if no corresponding SL BOM was found.

        *2* Merged SW/SL BOMs.

        That is, if c=1, the form will be:

        - [('2730-2019-544_sw', df1), ('080955', df2),
          ('6890-080955-1', df3), ('0300-2019-533', df4), ...]

        and if c=0, the form will be:

        - [('SW BOMs', dfForSWboms), ('BOM Check', dfForMergedBoms)]


    uname : string
        Username to attach to the footer of the Excel file.

    Returns
    =======

    out: None
        An Excel file will result named bomcheck.xlsx.

     \u2009
    '''
    global printStrs
    
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
        ''' If bomcheck.xlsx slready exists, return bomcheck(1).xlsx.  If that
        exists, return bomcheck(2).xlsx...  and so forth.'''
        global printStrs
        d, f = os.path.split(filename)
        f, e = os.path.splitext(f)
        if d:
            dirname = d   # if user specified a directory, use it instead
        if e and not e.lower()=='.xlsx':
            printStr = '\n(Output filename extension needs to be .xlsx' + '\nProgram aborted.\n'
            printStrs.append(printStr)
            print(printStr)
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

    if uname != 'unknown':
        username = uname
    elif os.getenv('USERNAME'):
        username = os.getenv('USERNAME')  # Works only on MS Windows
    else:
        username = 'unknown'

    # ref: https://howchoo.com/g/ywi5m2vkodk/working-with-datetime-objects-and-timezones-in-python
    if cfg['timezone'].lower()[:5] == 'local' or not cfg['timezone']:
        localtime_now = datetime.datetime.now()
    else:
        utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        localtime_now = utc_now.astimezone(pytz.timezone(cfg['timezone']))
    time = localtime_now.strftime("%m-%d-%Y %I:%M %p")

    comment1 = 'This workbook created ' + time + ' by ' + username + '.  '
    comment2 = 'The drop list was not employed for this BOM check.  '
    bomfooter = '&LCreated ' + time + ' by ' + username + '&CPage &P of &N'
    if cfg['drop']:
        comment2 = ('The drop list was employed for this BOM check:  '
                    + 'drop = ' + str(cfg['drop']) +  ', exceptions = ' + str(cfg['exceptions']))
        bomfooter = bomfooter + '&Rdrop: yes'

    if excelTitle and len(excelTitle) == 1:
        bomheader = '&C&A: ' + excelTitle[0][0] + ', ' + excelTitle[0][1]
    else:
        bomheader = '&C&A'
        
    with pd.ExcelWriter(fn) as writer:
        for r in results2export:
            sheetname = r[0]
            df = r[1]
            if not df.empty:                        #TODO: some test code
                df.to_excel(writer, sheet_name=sheetname)
                worksheet = writer.sheets[sheetname]  # pull worksheet object
                autosize_excel_columns(worksheet, df)
                worksheet.set_header(bomheader)  # see: https://xlsxwriter.readthedocs.io/page_setup.html
                worksheet.set_footer(bomfooter)
                worksheet.set_landscape()
                worksheet.fit_to_pages(1, 0)
                worksheet.hide_gridlines(2)
                worksheet.write_comment('A1', comment1 + comment2, {'x_scale': 3})
        workbook = writer.book
        workbook.set_properties({'title': 'BOM Check', 'author': username,
                'subject': 'Compares a SolidWorks BOM to a SyteLine BOM',
                'company': 'Dekker Vacuum Technologies, Inc.',
                'comments': comment1 + comment2})
        writer.save()
    printStr = "\nCreated file: " + fn + '\n'
    printStrs.append(printStr)
    print(printStr)

    if sys.platform[:3] == 'win':  # Open bomcheck.xlsx in Excel when on Windows platform
        try:
            os.startfile(os.path.abspath(fn))
        except:
            printStr = '\nAttempt to open bomcheck.xlsx in Excel failed.\n'
            printStrs.append(printStr)
            print(printStr)
            
            
def create_bc_config():
    ''' Create two files: 
    1. C:\\users\kcarlton\AppData\Local\bomcheck\bc_config.py
    (or some other location depending on environmental variable LOCALAPPDATA.)
    2. README.txt
    
    bc_config.py is a file that permits local configuration settings to the
    bomcheck program.
    
    Returns
    -------
    None.

    '''
    file_contents = [
        '# Adjust this file to suit your needs.  Remove the leading comment\n',
        '# character, e.g. the pound sign and space, that precedes a setting\n',
        '# that you wish to adjust.  For any setting not set below, that is\n',
        "# the comment character is left in place, the bomcheck program will \n",
        "# use its own default value.  Here are examples of three settings\n",
        "# that will be active in the bomcheck program (but not used by it):\n\n",
        
        'example1 = "text, i.e. strings, are enclosed in single or double quotes"\n\n',
        
        'example2 = ["lists", "of", "items", "are", "enclosed", "in", "brackets"]\n\n',
        
        'example3 = 3   # an integer needs no brackets or quote marks.\n\n\n',


        '# Part numbers in this list will be discarded from the SolidWorks BOM\n',
        '# so that they will not show up in the bom check report (OK to use glob\n'
        '# expressions, https://en.wikipedia.org/wiki/Glob_(programming)):\n',
        '# drop = ["3*-025", "3*-0", "3800-*"]\n\n\n',


        '# Excecptions to the part numbers in the drop list shown above\n',
        '# (OK to use glob expressions):\n',
        '# exceptions = ["3510-0200-025", "3086-1542-025"]\n\n\n',


        '# Do not do any length conversions for these parts.  That is, at\n',
        '# times there might be a length given for a part in a SolidWorks BOM\n',
        '# that is shown for reference only; for example, for a pipe nipple.\n',
        '# (OK to use glob expressions)\n',
        '# discard_length = ["3086-*"] \n\n\n', 


        '# decimal point accuracy applied to lengths in a SolidWorks BOM\n',
        '# accuracy = 2\n\n\n',


        '# Set the time zone so that the correct time and date is shown on the\n',
        '# Excel file that bomcheck ouputs to.  For valid timezones see:\n',
        '# https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568\n',
        '# Or set timezone to "local" to get the time and date from the\n',
        '# computer or server on which bomcheck is run\n',
        '# timezone = "US/Central"\n\n\n',  


        '# The unit of measure of lengths from a SolidWorks BOM are understood\n',
        '# to be inches unless a unit of measure is afixed to a length\n', 
        '# (e.g. 507mm).  The unit of measure you specifiy must be surrounded\n', 
        '# by quotation marks.  Valid units of measure: inch, feet, yard,\n',
        '# millimenter, centimeter, meter.\n', 
        '# from_um = "inch"\n\n\n',


        '# Lengths from a SolidWorks BOM are converted to a length with this\n',
        '# unit of measure in order to compare them to lengths in SyteLine.\n',
        '# Any lengths in SyteLine are all considered to be per this unit of\n',
        '# measure.\n',
        '# to_um = "feet"\n\n\n',


        '# All the column names that might be shown on a SolidWorks BOM for\n',
        '# part numbers.  Different names occur when templates used to create\n',
        '# BOMs are not consistent.  Note that names are case sensitive, so\n',
        '# "Part Number" is not the same as "PART NUMBER".\n',
        '# part_num_sw = ["PARTNUMBER", "PART NUMBER", "Part Number"]\n\n\n',


        '# All the column names that might be shown on a SyteLine BOM for\n',
        '# part numbers.  Different names occur when templates used to create\n',
        '# BOMs are not consistent.  Note that names are case sensitive, so\n',
        '# "Part Number" is not the same as "PART NUMBER".\n',
        '# part_num_sl = ["Item", "Material"]\n\n\n',


        '# All the column names that might be shown on a SolidWorks BOM for\n',
        '# quantities of parts.  Different names occur when templates used\n', 
        '# to create BOMs are not consistent.  Note that names are case \n',
        '# sensitive, so "Qty" is not the same as "QTY".\n',
        '# qty_sw = ["QTY", "QTY."]\n\n\n',


        '# All the column names that might be shown on a SyteLine BOM for\n',
        '# quantities of parts.  Different names occur when templates used\n', 
        '# to create BOMs are not consistent.  Note that names are case\n', 
        '# sensitive, so "Qty" is not the same as "QTY".\n',
        '# qty_sl = ["Qty", "Quantity", "Qty Per"]\n\n\n',


        '# All the column names that might be shown on a SolidWorks BOM for\n',
        '# part descriptions.  Different names occur when templates used\n', 
        '# to create BOMs are not consistent.  Note that names are case\n', 
        '# sensitive, so "Description" is not the same as "DESCRIPTION".\n',
        '# descrip_sw = ["DESCRIPTION"]\n\n\n',


        '# All the column names that might be shown on a SolidWorks BOM for\n',
        '# part descriptions.  Different names occur when templates used\n',
        '# to create BOMs are not consistent.  Note that names are case\n', 
        '# sensitive, so "Description" is not the same as "DESCRIPTION".\n',
        '# descrip_sl = ["Material Description", "Description"]\n\n\n',


        '# All the column names that might be shown on a SyteLine BOM for\n',
        '# Unit of Measure.  Different names occur when templates used\n',
        '# to create BOMs are not consistent.  Note that names are case\n', 
        '# sensitive, so "um" is not the same as "UM".\n',
        '# um_sl = ["UM", "U/M"]\n\n\n',


        '# All the column names that might be shown on a Solidworks BOM for\n',
        '# the item number of a part.  Different names occur when templates\n',
        '# used to create BOMs are not consistent.  Note that names are case\n', 
        '# sensitive, so "Item No." is not the same as "ITEM NO.".  (Note:\n', 
        '# this program is not designed to manage item numbers shown on a\n',
        '# SyteLine BOM.).  The bomcheck program uses this column to determine\n',
        '# the level of a subassembly within a multilevel SolidWorks BOM.  In\n',
        '# this case, item numbers will be like 1, 2, 3, 3.1, 3.2, 4, 5, 5.1;\n',
        '# where items 3 and 5 are subassemblies.\n',
        '# itm_num_sw = ["ITEM NO."]\n\n\n',


        '# All the column names that might be shown on a SyteLine BOM for\n',
        '# subassembly level.  Different names occur when templates used to\n',
        '# create BOMs are not consistent.  Note that names are case\n', 
        '# sensitive, so "Level" is not the same as "LEVEL".  (Note: this\n',
        '# program is not designed to handle subassy levels that might be\n',
        '# shown on a SolidWorks BOM.  For SolidWorks, the item number column\n',
        '# is used to determine subassembly level). Items in the level column\n', 
        '# will look like: 0, 1, 1, 2, 2, 1, 2, 2, 3, 1... and so forth\n',
        '# level_sl = ["Level"]\n\n\n'
        
        '# Number of rows to skip when reading data from the Excel/csv files\n',
        '# that contain SolidWorks BOMs.  The first row that bomcheck is to \n',
        '# evaluate is the row containing column headings such as ITEM NO.,\n', 
        '# QTY, PART NUMBER, etc.\n',
        '# skiprows_sw = 1\n\n\n',
        
        '# Number of rows to skip when reading data from the Excel/csv files\n',
        '# that contain SyteLine BOMs.  The first row to evaluate from SL BOMs\n',
        '# is the row containing column headings such as Item, Decription, etc.\n', 
        '# skiprows_sl = 0\n\n\n',
        ]
    readme_contents = [
        'bc_config.py is a text file that can be edited with Notepad or Wordpad.\n',
        "To control aspects of bomcheck's output, change the settings within\n",
        'bc_config.py.  Follow the examples shown.'
        ]
    
    if sys.platform[:3] == 'win':
        datadir = os.getenv('LOCALAPPDATA')
        # file where bc_config.py is located
        #(e.g.  C:\users\kcarlton\AppData\Local\bomcheck\bc_config.py):
        filename = os.path.join(datadir, 'bomcheck', 'bc_config.py')
        readme = os.path.join(datadir, 'bomcheck', 'README.txt')
    elif sys.platform[:3] == 'lin' or sys.platform[:3] == 'dar':  # linux or darwin (Mac OS X)
        homedir = os.path.expanduser('~')
        filename = os.path.join(homedir, '.bomcheck', 'bc_config.py')
        readme = os.path.join(homedir, '.bomcheck', 'README.txt')
    else:
        printStr = ('At function "create_bc_config", a suitable path was not found to\n'
                    'create bc_config.py at.  Notify the programmer of this error.')
        print(printStr)       
    if not os.path.isfile(filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            with open (filename, 'w') as fname:
                fname.writelines(file_contents)
            print('\nConfiguration file created: ' + filename + '\n')
        except:
            print('Failed to create file ' + filename)
    if not os.path.isfile(readme):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            with open (readme, 'w') as fname:
                fname.writelines(readme_contents)
        except:
            pass
    
    
    

# before program begins, create global variables
set_globals()

if __name__=='__main__':
    main()                   # comment out this line for testing
    #bomcheck('*')   # use for testing #



