#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File initial creation on Sun Nov 18 2018

@author: Kenneth E. Carlton

This program compares two BOMs: one originating from a CAD program like
SolidWorks (SW) and the other from an ERP program like SyteLine (SL).  
The structure of the BOMs (headings, structure, etc.) are very unique to a
particular company.  A configuration file, bomcheck.cfg, can be altered
to help adapt it to another company.
"""

__version__ = '1.8.2'
__author__ = 'Kenneth E. Carlton'

import glob, argparse, sys, warnings
import pandas as pd
import os.path
import os
import tempfile
import re
from datetime import datetime
import fnmatch
import ast
from configparser import ConfigParser
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)


def get_version():
    return __version__


def getcfg():
    ''' Return the value of "cfg".  cfg shows configuration
    variables and values thereof that are applied to
    bomcheck when it is run. For example, the variable 
    "accuracy" is the no. of decimal places that length
    values are rounded to.  (See the function "setcfg")
    
    Returns
    =======
    
    out: dictionary
    
    Examples
    ========
    
    getcfg()
    '''
    return cfg


def setcfg(**kwargs):
    ''' Set configuration variables that effect how bomcheck
    operates.  For example, set the unit of measure that
    length values are calculated to.  Run the function 
    getcfg() to see the names of variables that can be set.  
    Open the file bomcheck.cfg to see an explanation of the
    variables.  
    
    The object type that a variable holds (list, string, 
    etc.) should be like that seen via the getcfg()
    function, else bomcheck could crash (correcting is just
    a matter rerunning setcfg with the correct values).  
    
    Values can be set to something more permanent by 
    altering the file bomcheck.cfg.
    
    Examples
    ========
    
    setcfg(drop=["3*-025", "3*-008"], accuracy=4) 
    '''
    global cfg
    if not kwargs:
        print("You did not set any configuration values.  Do so like this:")
        print("setcfg(drop=['3886-*'], from_um='IN', to_um='FT')")
        print("Do help(setcfg) for more info")
    else:
        cfg.update(kwargs)

              
def get_bomcheckcfg(pathname):
    ''' Get configuration settings from the file bomcheck.cfg.
    
    Parameters
    ==========
    pathname: str
        pathname of the config file, e.g. r"C:\\folder\\bomcheck.cfg"
        
    Returns
    =======
    out: dict
         dictionary of values derived from bomcheck.cfg.
    '''
    global printStrs
    dic = {}
    fn = os.path.abspath(pathname)
    if not os.path.isfile(fn):
        printStr = ('\n\n---------------------------------------------------------\n'
                    'The config file could not be found at:\n\n        ' + fn + '\n\n'
                    'The pathname that you enter should look like this:\n\n'
                    '1.  MS Windows running bomcheckgui: C:\\folder\\bomcheck.cfg\n'
                    '2.  MS Windows running bomcheck:  r"C:\\folder\\bomcheck.cfg"\n'
                    '                             or:  "C:\\\\folder\\\\bomcheck.cfg"\n'
                    '                             or:  "C:/folder/bomcheck.cfg"\n'
                    '3.  Linux/Mac  running bomcheckgui: /home/ken/bomcheck.cfg\n' 
                    '4.  Linux/Mac  running bomcheck:   "/home/ken/bomcheck.cfg"\n\n'
                    '(The \\ character is a special "escape" character for the \n'
                    'programming language used for bomcheck.  Using the r character \n'
                    'or using \\\\ are work-arounds to allow using the \\ character.)\n'
                    '---------------------------------------------------------\n\n')
        printStrs.append(printStr)
        print(printStr)
        return dic
    config = ConfigParser()
    config.read(fn)
    for i in config['integers']:
        dic[i] = int(config['integers'][i])
    for l in config['lists']:
        lst = config['lists'][l].split(',')
        dic[l] = [i.strip() for i in lst]  # strip leading and trailing spaces from str
        #dic[l] = config['lists'][l].split(',')
    for s in config['single_values']:
        dic[s] = config['single_values'][s]
    return dic        
        
        
def set_globals():
    ''' Create a global variables including the primary one named cfg.
    cfg is a dictionary containing settings used by this program.

    set_globals() is ran when bomcheck first starts up.
    '''
    global cfg, printStrs, excelTitle

    cfg = {}
    printStrs = []
    excelTitle = []

    # default settings for bomcheck.  See bomcheck.cfg are explanations about variables
    cfg = {'accuracy': 2,   'ignore': ['3086-*'], 'drop': ['3*-025'],  'exceptions': [],
           'from_um': 'IN', 'to_um': 'FT',        'toL_um': 'GAL',     'toA_um': 'SQF',   
           'part_num':  ["PARTNUMBER", "PART NUMBER", "Part Number", "Item", "Material"],
           'qty':       ["QTY", "QTY.", "Qty", "Quantity", "Qty Per"],
           'descrip':   ["DESCRIPTION", "Material Description", "Description"],
           'um_sl':     ["UM", "U/M"],
           'level_sl':  ["Level"],
           'itm_sw':    ["ITEM NO."],
           'length_sw': ["LENGTH", "Length", "L", "SIZE", "AMT", "AMOUNT", "MEAS"]}
    

def getresults(i=1):
    ''' If i = 0, return a dataframe containing SW's BOMs for which no matching
    SL BOMs were found.  If i = 1, return a dataframe containing compared
    SW/SL BOMs. If i = 2, return a tuple of two items:
    (getresults(0), getresults(1))'''
    r = []
    r.append(None) if not results[0] else r.append(results[0][0][1])
    r.append(None) if not results[1] else r.append(results[1][0][1])
    if i == 0 or i == 1:
        return r[i]
    elif i == 2:
        return getresults(0), getresults(1)
    else:
        print('i = 0, 1, or 2 only')
        return None


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
    global cfg
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                        description='Program compares SolidWorks BOMs to SyteLine BOMs.  ' +
                        'Output is sent to a Microsoft Excel spreadsheet.')
    parser.add_argument('filename', help='Name of file containing a BOM.  Name ' +
                        'must end with _sw.xlsx, _sl.xlsx. _sw.csv, or ' +
                        '_sl.csv.  Enclose filename in quote marks!  An asterisk, i.e. *, ' +
                        'is a wild card character.  Examples: "6890-*", "*".  ' +
                        'Or if filename is instead a directory, all _sw and _sl files ' +
                        'in that directory and subdirectories thereof will be ' +
                        'gathered.  BOMs gathered from _sl files without ' +
                        'corresponding SolidWorks BOMs found are ignored.')
    parser.add_argument('-b', '--sheets', action='store_true', default=False,
                        help='Break up results across multiple sheets in the ' +
                        'Excel file that is output.') 
    parser.add_argument('-c', '--cfgpathname', help='pathname where configuration file ' +
                        'resides (e.g. r"C\\folder\\bomcheck.cfg"', default='') , 
    parser.add_argument('-d', '--drop_bool', action='store_true', default=False,
                        help='Ignore 3*-025 pns, i.e. do not use in the bom check')
    parser.add_argument('-f', '--followlinks', action='store_false', default=False,
                        help='Follow symbolic links when searching for files to process.  ' +
                        "  (MS Windows doesn't honor this option.)")
    parser.add_argument('-p', '--pause', help='Pause the program just before the program ' +
                        'the program would normally close after completing its work.',
                        default=False, action='store_true')
    parser.add_argument('-v', '--version', action='version', version=__version__,
                        help="Show program's version number and exit")
    parser.add_argument('-x', '--excel', help='Create Excel file showing check results.',
                        default=False, action='store_true')

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    
    bomcheck(args.filename, vars(args))


def bomcheck(fn, dic={}, **kwargs):
    '''
    This is the primary function of the bomcheck program
    and acts as a hub for other functions within the 
    bomcheck module.

    This function will handle single and multilevel BOMs 
    that are derived from SW and/or SL.  For multilevel 
    BOMs, subassemblies will automatically be extracted 
    from the top level BOM.

    Any BOMs from SW files found for which no matching SL 
    file is found will be converted into a SyteLine like
    BOM format.  If a SL BOM is present for which no 
    corresponding SW BOM is found, the SW file is ignored;
    that is, no output is shown for this SW file.

    Parmeters
    =========

    fn: string or list
        *  Files constaining BOMs from SolidWorks and/or 
           SyteLine.  Files from Solidworks must end with 
           _sw.xlsx or _sw.csv.  Files from SyteLine must
           end with _sl.xlsx or _sl.csv.
        *  An asterisk, *, matches any characters.  E.g. 
           "6890-083544-*" will match 6890-083544-1_sw.xlsx, 
           6890-083544-2_sw.xlsx, etc.        
        *  fn can be a directory name, in which case files
           in that directory, and subdirectories thereof,
           will be analized.
        *  If a list is given, then it is a list of 
           filenames and/or directories.
        *  PNs shown in filenames must correspond, e.g. 
           099238_sw.xlsx and 099238_sl.xlsx.  Exception: 
           BOM from SyteLine is a multilevel BOM.

    dic: dictionary
        default: {} (i.e. an empty dictionary).  This
        variable is used ONLY if the function "main" is used
        to run the bomcheck program; that is "main" itself 
        puts it in. This happens when the bomcheck program 
        is run from the command line.  If so, the values 
        from "main" for the keys "drop", "sheets", 
        "from_um", "to_um", etc. will have been put into 
        dic.  DO NOT PUT IN VALUES FOR DIC MANUALLY!

    kwargs: dictionary
        Here is an example of entering arguments into the
        bomcheck function:
        
        bomcheck("6890*", c=r"C:\bomcheck.cfg", d=1, x=1)
        
        The program will gather the c=r"C:\bomchk.cfg", d=1,
        and x=1, and put them into what's called a 
        dictionary, i.e. {c:"C:\bomchk.cfg", d:1, x=1}; and
        then assign that dicitionary to the kwargs argument.
        c, d, and x are called "keys".  "C:\bomchk.cfg", 1, 
        and 1 are values for those keys.  If no keys and
        their vaules are entered, bomcheck will use its own
        defaults.  The key/value pairs must go after the 
        fn ("6890*") argument.
    
        The keys in kwargs that will be recognized are
        listed below.  Any other keys will be ignored.

        b:  bool
            If True (or = 1), break up results across 
            multiple sheets within the Excel bomcheck.xlsx
            file.  Default: False
            
        c:  str 
            Pathname of the file bomcheck.cfg. For MS 
            Windows, the format should look like this:
            r"C:\\folder\\bomcheck.cfg".  The leadin r 
            character means 'raw'.  It is needed to 
            correctly read a file path in windows.  For a 
            unix-like operating system, something like this:
            "/home/ken/docs/bomcheck.cfg" 
            
        d: bool
            If True (or = 1), make use of the list named
            "drop".  The list "drop" is either defined
            internally within the bomcheck program itself,
            or overridden by the "drop" list defined in the
            bomcheck.cfg file.  Default: False
            
        f: bool
            If True (or = 1), follow symbolic links when
            searching for files to process.  (Doesn't work
            when using MS Windows.)  Default: False
            
        l: bool
            If True (or = 1), export a list of errors, if 
            any, that occured during the bomcheck.  
            Default: False
            
        m: int
            Max no. of rows to display when results are 
            output.  (This does not effect results that are
            exported an Excel file.)  Default: None (That 
            is, all rows are output.  Nothing is truncated.)

        u: str
            Username.  This will be fed to the export2exel 
            function so that a username will be placed
            into  the footer of the bomcheck.xlsx file.  
            Default: 'unknown'

        x: bool
            It True (or = 1), export results to an Excel
            file named bomcheck.xlsx. (If bomcheckgui is 
            used, name can be changed.) Default: False

    Returns
    =======

    out: list|tuple

        If argument l is set to True:
            return a list of strings.  Each string describes 
            an error that occurred during the bomcheck.  If
            no errors occurred, return [], i.e. an empty 
            string. (bomcheckgui automatically sets 
            l = True).
        Else:
            Return a tuple of two items that contains 
            bomcheck results.  Each of the two items of the 
            tuple is a Pandas dataframe object.
            *  The first dataframe shows SolidWorks BOMs for
               which no SyteLine BOMs were found to compare
               them to.  
            *  The second dataframe is SW to SL BOM 
               comparisons.

    Examples
    ========

    >>> # files names starting with 6890
    >>> bomcheck("folder1/6890*", d=True, u="John Doe")  

    >>> # all files in 'folder1' and in subfolders thereof
    >>> bomcheck("folder1")

    >>> # all files, one level deep
    >>> bomcheck("folder1/*") 

    >>> bomcheck(["folder1/*", "folder2/*"], d=True)

    '''
    global printStrs, cfg, results
    printStrs = []
    results = [None, None]
    
    c = dic.get('cfgpathname')    # if from the command line, e.g. bomcheck or python bomcheck.py
    if c: cfg.update(get_bomcheckcfg(c))
    c = kwargs.get('c')           # if from an arg of the bomcheck() function.
    if c: cfg.update(get_bomcheckcfg(c))
    
    # Set settings
    b = (dic.get('sheets') if dic.get('sheets') else kwargs.get('b', False))
    cfg['drop_bool'] = (dic.get('drop_bool') if dic.get('drop_bool')
                        else kwargs.get('d', False))
    f = kwargs.get('f', False)
    l = kwargs.get('l', False) 
    p = dic.get('pause', False)
    u = kwargs.get('u', 'unknown')
    m = kwargs.get('m', None)
    x = (dic.get('excel') if dic.get('excel') else kwargs.get('x', False))
    
    # If dbdic is in kwargs, it comes from bomcheckgui.
    # Variables therefrom take precedence.
    if 'dbdic' in kwargs:
        dbdic = kwargs['dbdic']
        c = dbdic.get('cfgpathname')   # activated if from bomcheckgui
        if c: cfg.update(get_bomcheckcfg(c))
        udrop =  dbdic.get('udrop', '')
        uexceptions = dbdic.get('uexceptions', '')
        udrop = udrop.replace(',', ' ')
        uexceptions = uexceptions.replace(',', ' ')
        if udrop:
            cfg['drop'] = udrop.split()
        if uexceptions:
            cfg['exceptions'] = uexceptions.split()
        cfg['file2save2'] = dbdic.get('file2save2', 'bomcheck')
        cfg['overwrite'] = dbdic.get('overwrite', False)
        cfg['accuracy'] = dbdic.get('accuracy', 2)
        cfg['from_um'] = dbdic.get('from_um', 'in')
        cfg['to_um'] = dbdic.get('to_um', 'FT')
        u = dbdic.get('author', 'unknown')
    else:
        cfg['file2save2'] = 'bomcheck'
        cfg['overwrite'] = False
        
     

    if isinstance(fn, str) and fn.startswith('[') and fn.endswith(']'):
        # fn = eval(fn)  # change a string to a list
        fn = ast.literal_eval(fn)  # change a string to a list
    elif isinstance(fn, str):
        fn = [fn]
        
    pd.set_option('display.max_rows', m)

    fn = get_fnames(fn, followlinks=f)  # get filenames with any extension.

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

    if b == False:                 # concat_boms is a bomcheck function
        title_dfsw, title_dfmerged = concat_boms(title_dfsw, title_dfmerged)
        results = title_dfsw, title_dfmerged

    if x:
        try:
            if title_dfsw or title_dfmerged:
                export2excel(dirname, cfg['file2save2'], title_dfsw + title_dfmerged, u)
            else:
                printStr = ('\nNotice 203\n\n' +
                            'No SolidWorks files found to process.  (Lone SyteLine\n' +
                            'BOMs will be ignored.)  Make sure file names end with\n' +
                            '_sw.xlsx, _sw.csv, _sl.xlsx, or _sl.csv.\n')
                printStrs.append(printStr)
                print(printStr)
        except PermissionError:
            printStr = ('\nError 202:\n\nFailed to write to bomcheck.xlsx\n'
                        'Cause unknown')
            printStrs.append(printStr)
            print(printStr)

    if p == True:
            input("Press enter to exit")

    if title_dfsw or title_dfmerged:
        print('calculation done')
    else:
        print('program produced no results')

    if l:
        return printStrs
    else:
        return getresults(2)


def get_fnames(fn, followlinks=False):
    ''' Interpret fn to get a list of filenames based on fn's value.

    Parameters
    ----------
    fn: str or list
        fn is a filename or a list of filenames.  A filename can also be a
        directory name.  Example 1, strings: "C:/myfile_.xlsx", "C:/dirname",
        or "['filename1', 'filename2', 'dirname1' ...]". Example 2, list:
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
            #fn = eval(fn)  # if fn a string like "['fname1', 'fname2', ...]", convert to a list
            fn = ast.literal_eval(fn)  # if fn a string like "['fname1', 'fname2', ...]", convert to a list
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


def common_data(list1, list2):
    ''' function to determine if two lists have at least one common element'''
    result = False
    for x in list1:
        for y in list2:
            if x == y:
                result = True
    return result

    
def clean(s):
    ''' Remove end of line characters, \\n, from a string.
    
    Parameters
    ==========
    s: str | other
        The string from which any \\n characters are to be removed.  If s
        is not a string, such as an int or float, it is ignored.
        
    Returns
    =======
    out: str | other
         If s is a string, and \\n, or multiples of, are in s, then s is 
         returned less the \\n charaters.  Otherwise return the original
         value of s no matter what type of object it is.
    '''
    if isinstance(s, str) and ('\n' in s):
        return s.replace('\n', '')
    else:
        return s

    
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
                df = pd.read_csv(temp, na_values=[' '], skiprows=1, sep='$',
                                     encoding='iso8859_1', engine='python',
                                     dtype = dict.fromkeys(cfg['itm_sw'], 'str')).applymap(clean)
                df.columns = [clean(c) for c in df.columns]
                if test_for_missing_columns('sw', df, '', printerror=False):
                    df = pd.read_csv(temp, na_values=[' '], sep='$',
                                     encoding='iso8859_1', engine='python',
                                     dtype = dict.fromkeys(cfg['itm_sw'], 'str')).applymap(clean)
                    df.columns = [clean(c) for c in df.columns]
                temp.close()
            elif file_extension.lower() == '.xlsx' or file_extension.lower() == '.xls':
                df = pd.read_excel(v, na_values=[' '], skiprows=1).applymap(clean)
                df.columns = [clean(c) for c in df.columns]
                if test_for_missing_columns('sw', df, '', printerror=False):
                    df = pd.read_excel(v, na_values=[' ']).applymap(clean)
                    df.columns = [clean(c) for c in df.columns]

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
                                     #skiprows=cfg['skiprows_sl'],
                                     encoding='utf-16', sep='\t')
                except UnicodeError:
                    printStr = ("\nError 204.\n\n."
                                "Probable cause: This program expects Unicode text encoding from\n"
                                "a csv file.  The file " + v + " does not have this.  The\n"
                                "correct way to achieve a functional csv file is:\n\n"
                                '    From Excel, save the file as type “Unicode Text (*.txt)”, and then\n'
                                '    change the file extension from txt to csv.\n\n'
                                "On the other hand, easiest solution: use an Excel file instead.\n")
                    printStrs.append(printStr)
                    print(printStr)
                    sys.exit(1)
            elif file_extension.lower() == '.xlsx' or file_extension.lower == '.xls':
                df = pd.read_excel(v, na_values=[' '])  #, skiprows=cfg['skiprows_sl'])

            if (not (test_for_missing_columns('sl', df, k)) and
                    common_data(cfg['level_sl'], df.columns)):
                sldfsdic.update(deconstructMultilevelBOM(df, 'sl', 'TOPLEVEL'))
            elif not test_for_missing_columns('sl', df, k):
                sldfsdic.update(deconstructMultilevelBOM(df, 'sl', k))

        except:
            printStr = ('\nError 201.\n\n' + ' processing file: ' + v +
                        '\nIt has been excluded from the BOM check.\n')
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
        required_columns = [cfg['qty'], cfg['descrip'],
                            cfg['part_num'], cfg['itm_sw']]
    else: # 'for sl bom'
        required_columns = [cfg['qty'], cfg['descrip'],
                            cfg['part_num'], cfg['um_sl']]

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
    __lvl = col_name(df, cfg['level_sl'])
    __itm = col_name(df, cfg['itm_sw'])
    __pn = col_name(df, cfg['part_num'])  # get the column name for pns

    p = None
    df[__pn] = df[__pn].astype('str').str.strip() # make sure pt nos. are "clean"
    df[__pn].replace('', 'no pn from BOM!', inplace=True)

    # https://stackoverflow.com/questions/2974022/is-it-possible-to-assign-the-same-value-to-multiple-keys-in-a-dict-object-at-onc
    values = dict.fromkeys((cfg['qty'] + cfg['length_sw']), 0)
    values.update(dict.fromkeys(cfg['descrip'], 'no descrip from BOM!'))
    values.update(dict.fromkeys(cfg['part_num'], 'no pn from BOM!'))
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


def is_in(find, series, xcept):
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

    series:  Pandas Series
        Series to search

    xcept: string or list of strings
        Exceptions to items to search for

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

    values = dict.fromkeys(cfg['part_num'], 'Item')
    values.update(dict.fromkeys(cfg['length_sw'], 'LENGTH'))
    values.update(dict.fromkeys(cfg['descrip'], 'Description'))
    values.update(dict.fromkeys(cfg['qty'], 'Q'))
    df.rename(columns=values, inplace=True)

    if 'LENGTH' in df.columns:  # convert lengths to other unit of measure, i.e. to_um
        ser = df['LENGTH']
        value = ser.replace('[^\d.]', '', regex=True).apply(str).str.strip('.').astype(float)  # "3.5MM" -> 3.5
        from_um = ser.apply(str).replace('[\d.]', '', regex=True)  # e.g. "3.5MM" -> "mm"
        from_um.replace('', cfg['from_um'].lower(), inplace=True)  # e.g. "" -> "ft"
        from_um = from_um.str.strip().str.lower()   # e.g. "SQI\n" -> "sqi"
        to_um = from_um.apply(lambda x: cfg['toL_um'].lower() if x.lower() in liquidUMs else
                                       (cfg['toA_um'].lower() if x.lower() in areaUMs else cfg['to_um'].lower()))
        ignore_filter = ~is_in(cfg['ignore'], df['Item'], [])
        df['U'] = to_um.str.upper().mask(value <= 0.0001, 'EA').mask(~ignore_filter, 'EA')
        factors = (from_um.map(factorpool) * 1/to_um.map(factorpool)).fillna(-1)
        q = df['Q'].replace('[^\d]', '', regex=True).apply(str).str.strip('.')  # strip away any text
        q = q.replace('', '0').astype(float)  # if any empty strings, set to '0'
        value2 = value * q * factors * ignore_filter
        df['Q'] = q*(value2<.0001) + value2    # move lengths to the Qty column
    else:
        df['U'] = 'EA'  # if no length colunm exists then set all units of measure to EA

    df = df.reindex(['Op', 'WC','Item', 'Q', 'Description', 'U'], axis=1)  # rename and/or remove columns
    dd = {'Q': 'sum', 'Description': 'first', 'U': 'first'}   # funtions to apply to next line
    df = df.groupby('Item', as_index=False).aggregate(dd).reindex(columns=df.columns)

    if cfg['drop_bool']==True:
        filtr3 = is_in(cfg['drop'], df['Item'], cfg['exceptions'])
        df.drop(df[filtr3].index, inplace=True)

    df['WC'] = 'PICK'    # WC is a standard column shown in a SL BOM.
    df['Op'] = 10   # Op is a standard column shown in a SL BOM, usually set to 10
    df.set_index('Op', inplace=True)

    return df


def compare_a_sw_bom_to_a_sl_bom(dfsw, dfsl):
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

    values = dict.fromkeys(cfg['part_num'], 'Item')
    values.update(dict.fromkeys(cfg['um_sl'], 'U'))
    values.update(dict.fromkeys(cfg['descrip'], 'Description'))
    values.update(dict.fromkeys(cfg['qty'], 'Q'))
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
    dfmerged.Q_sw.fillna(0, inplace=True)
    dfmerged.U_sl.fillna('', inplace=True)

    ###########################################################################
    # If U/M in SW isn't the same as that in SL, adjust SW's length values    #
    # so that lengths are per SL's U/M.  Then replace the U/M in the column   #
    # named U_sw with the updated U/M that matches that in SL.                #
    from_um = dfmerged.U_sw.str.lower().fillna('')                            #
    to_um = dfmerged.U_sl.str.lower().fillna('')                              #
    factors = (from_um.map(factorpool) * 1/to_um.map(factorpool)).fillna(1)   #
    dfmerged.Q_sw = dfmerged.Q_sw * factors                                   #
    dfmerged.Q_sw = round(dfmerged.Q_sw, cfg['accuracy'])                     #
    func = lambda x1, x2:   x1 if (x1 and x2) else x2                         #
    dfmerged.U_sw = to_um.combine(from_um, func, fill_value='').str.upper()   #
    ###########################################################################

    dfmerged.sort_values(by=['Item'], inplace=True)
    filtrI = dfmerged['_merge'].str.contains('both')  # this filter determines if pn in both SW and SL
    maxdiff = .51 / (10**cfg['accuracy'])
    filtrQ = abs(dfmerged['Q_sw'] - dfmerged['Q_sl']) < maxdiff  # If diff in qty greater than this value, show X
    filtrM = dfmerged['Description_sw'].str.split() == dfmerged['Description_sl'].str.split()
    filtrU = dfmerged['U_sw'].astype('str').str.upper().str.strip() == dfmerged['U_sl'].astype('str').str.upper().str.strip()
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
    dfmerged.Q_sw.replace(0, '', inplace=True)

    return dfmerged


def collect_checked_boms(swdic, sldic):
    ''' Match SolidWorks assembly nos. to those from SyteLine and then merge
    their BOMs to create a BOM check.  For any SolidWorks BOMs for which no
    SyteLine BOM was found, put those in a separate dictionary for output.

    calls: convert_sw_bom_to_sl_format, compare_a_sw_bom_to_a_sl_bom

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
        The output tuple contains two values: 1.  Dictionary containing
        SolidWorks BOMs for which no matching SyteLine BOM was found.  The
        BOMs have been converted to a SyteLine like format.  Keys of the
        dictionary are assembly part numbers.  2.  Dictionary of merged
        SolidWorks and SyteLine BOMs, thus creating a BOM check.  Keys for the
        dictionary are assembly part numbers.
    '''
    lone_sw_dic = {}  # sw boms with no matching sl bom found
    combined_dic = {}   # sl bom found for given sw bom.  Then merged
    for key, dfsw in swdic.items():
        if key in sldic:
            combined_dic[key] = compare_a_sw_bom_to_a_sl_bom(
                                convert_sw_bom_to_sl_format(dfsw), sldic[key])
        else:
            df = convert_sw_bom_to_sl_format(dfsw)
            df['Q'] = round(df['Q'], cfg['accuracy'])
            #lone_sw_dic[key + '_sw'] = df
            lone_sw_dic[key] = df
    return lone_sw_dic, combined_dic


def concat_boms(title_dfsw, title_dfmerged):
    ''' Concatenate all the SW BOMs into one long list (if there are any SW
    BOMs without a matching SL BOM being found), and concatenate all the
    merged SW/SL BOMs into another long list.

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
        the number of BOMs analyzed, and if bomcheck's b (sheets) option was
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

    ok2go = True
    if cfg['overwrite']:
        fn = os.path.join(dirname, filename + '.xlsx')
        if os.path.exists(fn):
            try:
                os.remove(fn)
            except Exception as e:
                printStr = ('\nOverwrite of output file failed.' +
                            '\nPossibly the current file is open in Excel.' +
                            '\n' + str(e) + '\n')
                printStrs.append(printStr)
                ok2go = False
    else:
        fn = definefn(dirname, filename)

    if uname != 'unknown':
        username = uname
    elif os.getenv('USERNAME'):
        username = os.getenv('USERNAME')  # Works only on MS Windows
    else:
        username = 'unknown'

    localtime_now = datetime.now()
    time = localtime_now.strftime("%m-%d-%Y %I:%M %p")

    comment1 = 'This workbook created ' + time + ' by ' + username + '.  '
    comment2 = 'The drop list was NOT employed for this BOM check.  '
    bomfooter = '&LCreated ' + time + ' by ' + username + '&CPage &P of &N'
    if cfg['drop_bool']:
        comment2 = ('The drop list was employed for this BOM check:  '
                    + 'drop = ' + str(cfg['drop']) +  ', exceptions = ' + str(cfg['exceptions']))
        bomfooter = bomfooter + '&Rdrop: yes'

    if excelTitle and len(excelTitle) == 1:
        bomheader = '&C&A: ' + excelTitle[0][0] + ', ' + excelTitle[0][1]
    else:
        bomheader = '&C&A'


    if ok2go:
        try:
            with pd.ExcelWriter(fn) as writer:
                for r in results2export:
                    sheetname = r[0]
                    df = r[1]
                    if not df.empty:                        #TODO: some test code
                        df.to_excel(writer, sheet_name=sheetname)
                        try:
                            worksheet = writer.sheets[sheetname]  # pull worksheet object
                            autosize_excel_columns(worksheet, df)   #<<<
                            worksheet.set_header(bomheader)  #<<< see: https://xlsxwriter.readthedocs.io/page_setup.html
                            worksheet.set_footer(bomfooter)  #<<<
                            worksheet.set_landscape()        #<<<
                            worksheet.fit_to_pages(1, 0)     #<<<
                            worksheet.hide_gridlines(2)      #<<<
                            worksheet.write_comment('A1', comment1 + comment2, {'x_scale': 3})   #<<<
                        except Exception as e:
                            msg = (str(e) + '.  (Minor error caused by Colab.  Can be ignored.)')
                            #print(msg)
                try:
                    workbook = writer.book
                    workbook.set_properties({'title': 'BOM Check', 'author': username,           #<<<
                            'subject': 'Compares a SolidWorks BOM to a SyteLine BOM',
                            'company': 'Dekker Vacuum Technologies, Inc.',
                            'comments': comment1 + comment2})
                except Exception as e:
                    msg = (str(e) + '.  (Minor error caused by Colab.  Can be ignored.)')
                    #print(msg)
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
        except Exception as e:
            printStr = ('\nOverwrite of output file failed.' +
            '\nPossibly the current file is open in Excel.' +
            '\n' + str(e) + '\n')
            printStrs.append(printStr)


# before program begins, create global variables
set_globals()

# An example of how the factorpool is used: to convert 29mm to inch:
#   1/(25.4*12) = 0.00328   (inches to feet)
#   1/12 = .08333,          (foot to inches)
#   Then: 29 * factorpool['mm'] / factorpool['in'] = 0.00328 / .08333 = 1.141
# Only lower case keys are acceptable.  No digits allowed in keys (like "2" in "ft2")
factorpool = {'in':1/12,     '"':1/12, 'inch':1/12,  chr(8221):1/12,
              'ft':1.0,      "'":1.0,  'feet':1.0,  'foot':1.0,  chr(8217):1.0,
              'yrd':3.0,     'yd':3.0, 'yard':3.0,
              'mm': 1/(25.4*12),       'millimeter':1/(25.4*12),
              'cm':10/(25.4*12),       'centimeter':10/(25.4*12),
              'm':1000/(25.4*12),      'meter':1000/(25.4*12), 'mtr':1000/(25.4*12),
              'sqin':1/144,            'sqi':1/144,
              'sqft':1,      'sqf':1,  'sqyd':3,   'sqy':3,
              'sqmm':1/92903.04,       'sqcm':1/929.0304,      'sqm':1/(.09290304),
              'pint':1/8,    'pt':1/8, 'qt':1/4,   'quart':1/4,
              'gal':1.0,     'g':1.0,  'gallon':1.0,
              'ltr':0.2641720524,      'liter':0.2641720524,   'l':0.2641720524}
areaUMs = set(['sqi', 'sqin','sqf', 'sqft', 'sqyd', 'sqy', 'sqmm', 'sqcm', 'sqm'])
liquidUMs = set(['pint',  'pt', 'quart', 'qt', 'gallon', 'g', 'gal' 'ltr', 'liter', 'l'])


if __name__=='__main__':
    main()           # comment out this line for testing -.- . -.-.
    #bomcheck('*')   # use for testing



