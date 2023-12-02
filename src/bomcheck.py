#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File initial creation on Sun Nov 18 2018

@author: Kenneth E. Carlton

This program compares two Bills of Materials (BOMs). One BOM
originating from a Computer Aided Design (CAD) program like
SolidWorks (SW) and the other from an Enterprise Resource
Planning (ERP) program like SyteLine (SL).

BOMs are extracted from Microsoft Excel files.  For bomcheck
to be able to identify files that are suitable for
evaluation, append the characters _sw.xlsx to the files that
contain SW BOMs, and append the characters _sl.xlsx to the
files that contain ERP BOMs. Any submitted files without
these trailing characters will be ignored.

For more information, see the help files for this program.
"""

__version__ = '1.9.5'
__author__ = 'Kenneth E. Carlton'

import pdb # use with pdb.set_trace()
import glob, argparse, sys, warnings
import pandas as pd
import os.path
import os
import fnmatch
import ast
import tomllib
import webbrowser
warnings.filterwarnings('ignore')  # the program has its own error checking.
pd.set_option('display.max_rows', None)  # was pd.set_option('display.max_rows', 150)
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', 200)


def get_version():
    return __version__

version = get_version

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


def get_bomcheckcfg(filename):
    ''' Load a toml file (ref.: https://toml.io/en/). A user
    of the bomcheck program can open up 'filename' with a
    text editor program such as notepad, and edit it to
    adjust how the bomcheck program behaves.

    (Note: backslash characters have a special function in
    Python known as excape characters. Don't use them in
    filename.  Instead replace backslash characters with
    forwardslash characters.  Python accepts this.
    Reference:
    https://sites.pitt.edu/~naraehan/python3/file_path_cwd.html)

    Parameters
    ==========

    filename: str
        name of the file containing user settings, e.g.
        bomcheck.cfg

    Returns
    =======

    out: dict
        dictionary of settings
    '''
    global printStrs
    try:
        with open(filename, 'rb') as f:
            tomldata = tomllib.load(f)
            return tomldata
    except OSError as e:
        printStr = f"\n{e}\n"
        if not printStr in printStrs:
            printStrs.append(printStr)
            print(printStr)
        return {}
    except tomllib.TOMLDecodeError as e:
        printStr = (f"\nYour {filename} file is not configured correctly.  It will be "
              "ignored.\nIs probably a missing bracket, quotation mark, comma,"
              f" etc.\n({e})\n")
        if not printStr in printStrs:
            printStrs.append(printStr)
            print(printStr)
        return


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
    cfg = {'accuracy': 2,   'ignore': ['3086-*'], 'drop': [],  'exceptions': [],
           'from_um': 'IN', 'to_um': 'FT', 'toL_um': 'GAL', 'toA_um': 'SQF',
           'part_num':  ["Material", "PARTNUMBER", "PART NUMBER", "Part Number", "Item"],
           'qty':       ["QTY", "QTY.", "Qty", "Quantity", "Qty Per"],
           'descrip':   ["DESCRIPTION", "Material Description", "Description"],
           'um_sl':     ["UM", "U/M"],
           'level_sl':  ["Level"],
           'itm_sw':    ["ITEM NO."],
           'length_sw': ["LENGTH", "Length", "L", "SIZE", "AMT", "AMOUNT", "MEAS", "COST"],
           'obs': ['Obsolete Date', 'Obsolete'], 'del_whitespace': True,
           # Column names shown in the results (for a given key, one value only):
           'assy':'assy', 'Item':'Item', 'iqdu':'IQDU', 'Q':'Q',
           'Description':'Description', 'U':'U',
           # When a SW BOM is converted to a BOM looking like that of SL, these columns and
           # values thereof are added to the SW BOM, thereby making it look like a SL BOM.
           'Op':'Op', 'OpValue':'10', 'WC':'WC',  'WCvalue':'PICK'
          }


def getresults(i=1):
    ''' If i = 0, return a dataframe containing SW's BOMs
    for which no matching SL BOMs were found.  If i = 1,
    return a dataframe containing compared SW/SL BOMs. If
    i = 2, return a tuple of two items:
    (getresults(0), getresults(1))'''
    # This function gets results from the global variable named "results".
    # results is created within the function "bomcheck".
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
    '''This fuction allows this bomcheck.py program to be
    run from the command line.  It is started automatically
    (via the "if __name__=='__main__'" command at the bottom
    of this file) when bomecheck.py is run.

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
                        'must end with _sw.xlsx, or _sl.xlsx.  ' +
                        'Enclose filename in quote marks!  An asterisk, i.e. *, ' +
                        'is a wild card character.  Examples: "6890-*", "*".  ' +
                        'Or if filename is instead a directory, all _sw and _sl files ' +
                        'in that directory and subdirectories thereof will be ' +
                        'gathered.  BOMs gathered from _sl files without ' +
                        'corresponding SolidWorks BOMs being found are ignored.')
    parser.add_argument('-a', '--about', action='version',
                        version="Author: " + __author__ +
                        ".  Initial creation: Nov 18 2018.  "
                        "bomcheck's home: https://github.com/kcarlton55/bomcheck."
                        '  Version: ' + __version__,
                        help="Show author, date, web site, version, then exit")
    parser.add_argument('-c', '--cfgpathname', help='pathname where configuration file ' +
                        'resides (e.g. C:/folder1/folder2/bomcheck.cfg.  Note: use ' +
                        "forward slashes.  Backslashes won't work") ,
    parser.add_argument('-csdsc', '--csdescription', action='store_true', default=False,
                        help='Enable case sensitive checking of descriptions'),
    parser.add_argument('-cspn', '--cspartnuber', action='store_true', default=False,
                        help='Enable case sensitive checking of part numbers'),
    parser.add_argument('-d', '--drop_bool', action='store_true', default=False,
                        help="Don't show part nos. from the drop list in check results.")
    parser.add_argument('-dp', '--drop', help='Enter a "drop list", i.e. a list of part '
                        'numbers from the CAD BOM that you wish to be ignored.  '
                        "E.g. -dp \"['3*-025', '3081-*']\" (If active, -d "
                        'is automatically set to True.)', type=str)
    parser.add_argument('-exc', '--exceptions', help='Exceptions to part numbers shown in '
                        "the drop list.  E.g. -exc \"['3142-3034-025', '3081-*-001']\"", type=str)
    parser.add_argument('-f', '--followlinks', action='store_true', default=False,
                        help='Follow symbolic links when searching for files to process.  ' +
                        "  (MS Windows doesn't honor this option.)"),
    parser.add_argument('-v', '--version', action='version', version=__version__,
                        help="Show program's version number and exit")
    parser.add_argument('-x', '--excel', help='Export results to a csv file ' +
                        'that can be opened by Excel', default=False, action='store_true')

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
        *  Files containing BOMs from SolidWorks and/or
           ERP.  Files from Solidworks must end with
           _sw.xlsx.  Files from ERP must end with
           _sl.xlsx.
           >>>  An asterisk, *, matches any characters. E.g.
                *083544* will match 6890-083544-1_sw.xlsx
                 6890-083544_sl.xlsx, and 6430-083544_sw.xlsx
        *  fn can also be a directory name, in which case
           files in that directory, and subdirectories
           thereof, will be analized.
        *  If instead a list is given, then it is a list of
           filenames and/or directories.
        *  Note: PNs shown in filenames must correspond for
           a comparison to occur; e.g. 099238_sw.xlsx and
           099238_sl.xlsx.  An exception to this is if the
           BOM is from an ERP multilevel BOM.

    dic: dictionary
        default: {}, i.e. an empty dictionary.  Do not
        assign values to dic.  dic is only used internally
        by the bomcheck program when bomcheck is run from a
        command line terminal.

    kwargs: dictionary
        Here is an example of entering kwargs arguments
        into the bomcheck function:

        bomcheck("6890*", c="C:/bomcheck.cfg", d=1, x=1)

        In this case the first value, *6890*, is assigned
        to variable fn, and the remaining variables
        c="C:/bomcheck.cfg" (note: use a forward slash
        instead of of backslash), d=1, and x=1,
        are put into a python dictionary object in
        key:value pairs, e.g. {c:"C:/bomcheck.cfg", d:1,
        x=1}. That dictionary is then delivered to the
        bomcheck program.  Other keys and types of
        values that those keys can accept are:

        c:  str
            Pathname of the file bomcheck.cfg. For MS
            Windows, the format should look like this:
            "C:/myfolder/bomcheck.cfg".  That it, use
            a forward slash instead of a backslash.
            Otherwise the file will not be read. For a
            unix-like operating system, like this:
            "/home/ken/bomcheck.cfg"/

        d: bool
            If True (or = 1), make use of the list named
            "drop".  See bomcheck_help for more
            information. Default: False

        drop: list
           list of part nos. from the CAD BOM to exclude
           from the bom check.  e.g. [3*-025, 3108-*]
           (if set, set arg d to True)

        exceptions: list
           list of exceptions to part nos. shown in the
           drop list.  e.g. [3125-*-025]

        f: bool
            If True (or = 1), follow symbolic links when
            searching for files to process.  (Doesn't work
            when using MS Windows.)  Default: False

        m: int
            Display only m rows of the results to the user.

        o: str
            Output file name.  x has to be set to True
            for this to function.  The output file name
            cannot be a path name; that is, it cannot
            contain / or \\ characters.  Default: bomcheck

        csdsc: bool
            Enable case sensitive matching of part
            descriptions.  Devalult = False

        cspn: bool
            Enable case sensitive matching of part numbers.
            Devalult = False

        x: bool
            If True (or = 1), export results to a csv file
            that Excel can open.  Default: False

    Returns
    =======

    out: tuple
        Return a tuple containing three items.  Items are:
        0: A pandas dataframe containing SolidWorks BOMs for
           which with no matching SyteLine BOMs were found.
           If no BOMs exist, None is returned.
        1: A pandas dataframe showing a side-by-side
           comparison of SolidWorks BOMs and ERP BOMs. If
           not BOMs exist, None is returned.
        2: A python list object containing a list of errors
           that occured during bomchecks' execution.  If no
           errors occured, then an empty string is returned.

    Examples
    ========

    Evaluate files names starting with 6890 (on a Windows
    operating system, replace backslashes with a forward
    slashes, /):

        >>> bomcheck("C:/folder1/6890*", d=True, x=True,
                     u="kcarlton"
                     c="C:/mydocuments/bomcheck.cfg")

    String values, like folder1/6890* and kcarlton, must
    be surrounded by quotation marks.

    Evaluate all files in folder1 and in subfolders thereof:

        >>> bomcheck("C:folder1")

    Same as above, but evaluate files only one level deep:

        >>> bomcheck("C:folder1/*")

    Evaluate files in a couple of locations:

        >>> bomcheck(["C:/folder1/*", "C:/folder2/*"], d=True)

    The \\ character can cause problems.  See this site for more information:
    https://pro.arcgis.com/en/pro-app/2.8/arcpy/get-started/setting-paths-to-data.htm

        >>> bomcheck("C:/myprojects/folder1", c="C:/mycfgpath/bomcheck.cfg")

    '''
    global printStrs, cfg, results
    printStrs = []
    results = [None, None]

    c = dic.get('cfgpathname')    # if from the command line, e.g. bomcheck or python bomcheck.py

    if c:
        cfg.update(get_bomcheckcfg(c))

    c = kwargs.get('c')           # if from an arg of the bomcheck() function.
    if c:
        cfg.update(get_bomcheckcfg(c))

    # Set settings
    cfg['drop_bool'] = (dic.get('drop_bool') if dic.get('drop_bool')
                        else kwargs.get('d', False))
    cfg['cspartnumber'] = (dic.get('cspartnumber') if dic.get('cspartnumber')
                        else kwargs.get('cspn', False))
    cfg['csdescription'] = (dic.get('csdescription') if dic.get('csdescription')
                        else kwargs.get('csdsc', False))
    #pdb.set_trace()
    if dic.get('drop'):
        try:
            string = dic.get('drop')
            cfg['drop'] = ast.literal_eval(string)  # change a string to a list
            cfg['drop_bool'] = True
        except:
            print('\nExecution stoped.  Improper syntax for drop list.  Example of proper syntax:\n\n'
                    "bomcheck filename --drop \"['3*-025', '3018-*']\"\n")
            exit()
    if dic.get('exceptions'):
        try:
            string = dic.get('exceptions')
            cfg['exceptions'] = ast.literal_eval(string)  # change a string to a list
        except:
            print('\nExecution stoped.  Improper syntax for exceptions list.  Example of proper syntax:\n\n'
                    "bomcheck filename --drop \"['3*-025', '3018-*'] --exceptions \"['32*-025', '3018-7*']\"\n")
            exit()
    if kwargs.get('drop'):
        cfg['drop'] = kwargs.get('drop')
        cfg['drop_bool'] = True
    if kwargs.get('exeptions'):
        cfg['exceptions'] = kwargs.get('exceptions')
    f = kwargs.get('f', False)
    m = kwargs.get('m', None)
    outputFileName = kwargs.get('o', 'bomcheck')
    x = (dic.get('excel') if dic.get('excel') else kwargs.get('x', False))

    # If dbdic is in kwargs, it comes from bomcheckgui.
    # Variables therefrom take precedence.
    if 'dbdic' in kwargs:
        dbdic = kwargs['dbdic']
        c = dbdic.get('cfgpathname')   # activated if from bomcheckgui
        if c:
            cfg.update(get_bomcheckcfg(c))
        udrop =  dbdic.get('udrop', '')
        uexceptions = dbdic.get('uexceptions', '')
        udrop = udrop.replace(',', ' ')
        uexceptions = uexceptions.replace(',', ' ')
        if udrop:
            cfg['drop'] = udrop.split()  # e.g. '3*025 NO_PN' -> ['3*025', 'NO_PN']
        if uexceptions:
            cfg['exceptions'] = uexceptions.split()
        outputFileName = dbdic.get('file2save2', 'bomcheck')
        cfg['overwrite'] = dbdic.get('overwrite', True)
        cfg['accuracy'] = dbdic.get('accuracy', 2)
        cfg['from_um'] = dbdic.get('from_um', 'in')
        cfg['to_um'] = dbdic.get('to_um', 'FT')
    else:
        cfg['overwrite'] = False


    if isinstance(fn, str) and fn.startswith('[') and fn.endswith(']'):
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
        title_dfmerged.append((k, v))  # e.g. {assynum1:bomdf1, ... assynumn:bomdfn}

    title_dfsw, title_dfmerged = concat_boms(title_dfsw, title_dfmerged)
    results = title_dfsw, title_dfmerged

    if x:
        try:
            if title_dfsw or title_dfmerged:
                export2excel(dirname, outputFileName, title_dfsw + title_dfmerged)
            else:
                printStr = ('\nNotice 203\n\n' +
                            'No SolidWorks files found to process.  (Lone SyteLine\n' +
                            'BOMs will be ignored.)  Make sure file names end with\n' +
                            '_sw.xlsx or _sl.xlsx.\n')
                printStrs.append(printStr)
                print(printStr)
        except PermissionError:
            printStr = ('\nError 202:\n\nFailed to write to bomcheck.xlsx\n'
                        'Cause unknown')
            printStrs.append(printStr)
            print(printStr)

    if title_dfsw or title_dfmerged:
        print('calculation done')
    else:
        print('program produced no results')

    if dic:  # if bomcheck run from the command line, show results
        print('\n', getresults(0))
        print('\n', getresults(1))
        print('\n', printStrs)

    return getresults(0), getresults(1), printStrs


def get_fnames(fn, followlinks=False):
    ''' Interpret fn to get a list of filenames based on
    fn's value.

    Parameters
    ----------
    fn: str or list
        fn is a filename or a list of filenames.  A filename
        can also be a directory name.  Example 1, strings:
        "C:/myfile_.xlsx", "C:/dirname", or "['filename1',
        'filename2', 'dirname1' ...]". Example 2, list:
        ["filename1", "filename2", "dirname1", "dirname2"].
        When a a directory name is given, filenames are
        gathered from that directory and from subdirectories
        thereof.
    followlinks: Boolean, optional
        If True, follow symbolic links. If a link is to a
        direcory, then filenames are gathered from that
        directory and from subdirectories thereof.  The
        default is False.

    Returns
    -------
    _fn: list
        A list of filenames, e.g. ["filename1", "filename2",
        ...].  Each value in the list is a string.  Each
        string is the name of a file.  The filename can be
        a pathname, e.g. "C:/dir1/dir2/filename".  The
        filenames can have any type of extension.
    '''
    if isinstance(fn, str) and fn.startswith('[') and fn.endswith(']'):
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


def gatherBOMs_from_fnames(filename):
    ''' Gather all SolidWorks and SyteLine BOMs derived from
    "filename".  "filename" can be a string containing
    wildcards, e.g. 6890-085555-*, which allows the capture
    of multiple files; or "filename" can be a list of such
    strings.  These files (BOMs) will be converted to Pandas
    DataFrame objects.

    Only files suffixed with _sw.xlsx or _sl.xlsx will be
    chosen.  Others are discarded.  These files will then be
    converted into two python dictionaries.  One dictionary
    will contain SolidWorks BOMs only, and the other will
    contain only SyteLine BOMs.

    If a filename has a BOM containing a multiple level BOM,
    then the subassembly BOMs will be extracted from that
    BOM and be added to the dictionaries.

    calls:  deconstructMultilevelBOM, test_for_missing_columns

    Parmeters
    =========

    filename: list
        List of filenames to be analyzed.

    Returns
    =======

    out: tuple
        The output tuple contains three items.  The first is
        the directory corresponding to the first file in the
        filename list.  If this directory is an empty
        string, then it refers to the current working
        directory.  The remainder of the tuple items are two
        python dictionaries. The first dictionary contains
        SolidWorks BOMs, and the second contains SyteLine
        BOMs.  The keys for these two dictionaries are part
        nos. of assemblies derived from the filenames (e.g.
        085952 from 085953_sw.xlsx), or derived from
        subassembly part numbers of a file containing
        multilevel BOM.
    '''
    dirname = '.'  # to this will assign the name of 1st directory a _sw is found in
    global printStrs
    swfilesdic = {}
    slfilesdic = {}
    XLSnotAllowed = ('\nBomcheck does not support .xls formated Excel files.\n'
                     'Those files will be ignored.  Save to .xlsx instead\n')
    for f in filename:  # from filename extract all _sw & _sl files and put into swfilesdic & slfilesdic
        i = f.rfind('_')
        if f[i:i+4].lower() == '_sw.' or f[i:i+4].lower() == '_sl.':
            dname, fname = os.path.split(f)
            k = fname.find('_')
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
            if file_extension.lower() == '.xlsx':
                df = pd.read_excel(v, na_values=[' '])
                df.columns = df.columns.str.replace(r'\n', '', regex=True)
                df.replace(r'\n',' ', regex=True, inplace=True)
                if df.columns[1] == 'Unnamed: 1':
                    df = pd.read_excel(v, na_values=[' '], skiprows=1)
                    df.columns = df.columns.str.replace(r'\n', '', regex=True)
                    df.replace(r'\n',' ', regex=True, inplace=True)
                    if col_name(df, cfg['descrip']):
                        df[col_name(df, cfg['descrip'])].fillna('----- sw_description_missing -----', inplace=True)
                    df = df.astype(str)
                    df = df.replace('nan', 0)
                dfsw_found=True
                if dfsw_found:  # do this if a _sl.xlsx file renamed to a _sw.xlsx file.  That is a sl file maskarading as a sw file.
                    df.drop(df[df.iloc[:,0].astype('str').str.contains('Group')].index, inplace=True)
            elif file_extension.lower() == '.xls' and XLSnotAllowed not in printStrs:
                printStrs.append(XLSnotAllowed)
                print(XLSnotAllowed)
                dfsw_found = False
            else:
                dfsw_found = False
            if (dfsw_found and (not (test_for_missing_columns('sw', df, k))) and
                    col_name(df, cfg['level_sl'])): # if "Level" found if df.columns, return "Level"
                swdfsdic.update(deconstructMultilevelBOM(df, 'sw', 'TOPLEVEL'))
            elif dfsw_found and (not test_for_missing_columns('sw', df, k)):
                swdfsdic.update(deconstructMultilevelBOM(df, 'sw', k))
        except ZeroDivisionError:
            printStr =  ('\nError processing file: ' + v + '\nIt has been excluded from the BOM check.\n')
            printStrs.append(printStr)
            print(printStr)
    sldfsdic = {}  # for collecting SL BOMs to a dic
    for k, v in slfilesdic.items():
        try:
            _, file_extension = os.path.splitext(v)
            if file_extension.lower() == '.xlsx':
                df = pd.read_excel(v, na_values=[' '])
                dfsl_found=True
            elif file_extension.lower() == '.xls' and XLSnotAllowed not in printStrs:
                printStrs.append(XLSnotAllowed)
                print(XLSnotAllowed)
                dfsl_found=False
            else:
                dfsl_found=False

            # Grrr! SyteLine version 10 puts in unwanted lines.  Deal with it:
            if dfsl_found:
                df.drop(df[df.iloc[:,0].astype(str).str.contains('Group')].index, inplace=True)
                # df.iloc[:,0]                                  yields: Group Item: SC300TL2111311, 0, 1, 1, 2, 2, ...
                # df[df.iloc[:,0].str.contains('Group')].index  yields: Index([0], dtype='int64')
                # df.index                                      yields: df.drop([0], inplace=True) RangeIndex(start=0, stop=74, step=1)
                # df[df.iloc[:,0].str.contains('1')].index      yields: Index([0, 2, 3, 6, 10, 47, 52, 57, 58, 59, 60, 61, 73], dtype='int64')
                # df.drop(index=[0, 8, 12, 23])                 will drop rows 0, 8, 12, 23
                # reference: https://www.geeksforgeeks.org/drop-a-list-of-rows-from-a-pandas-dataframe/, see row: Drop Rows with Conditions in Pandas
            if (dfsl_found and (not (test_for_missing_columns('sl', df, k))) and
                    col_name(df, cfg['level_sl'])):
                sldfsdic.update(deconstructMultilevelBOM(df, 'sl', 'TOPLEVEL'))
            elif dfsl_found and (not test_for_missing_columns('sl', df, k)):
                sldfsdic.update(deconstructMultilevelBOM(df, 'sl', k))
        except:
            printStr = ('\nError 201.\n\n' + ' processing file: ' + v +
                        '\nIt has been excluded from the BOM check.\n')
            printStrs.append(printStr)
            print(printStr)
    try:
        df = pd.read_clipboard(engine='python', na_values=[' '])
        if not test_for_missing_columns('sl', df, 'BOMfromClipboard', showErrMsg=False):
            sldfsdic.update(deconstructMultilevelBOM(df, 'sl', 'TOPLEVEL'))
    except:
        pass
    if os.path.islink(dirname):
        dirname = os.readlink(dirname)
    return dirname, swdfsdic, sldfsdic


def test_for_missing_columns(bomtype, df, pn):
    ''' SolidWorks and SyteLine BOMs require certain
    essential columns to be present.  This function
    looks at those BOMs that are within df to see if
    any required columns are missing.  If found,
    print to screen.

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
                            cfg['part_num']]#, cfg['itm_sw']]
    else: # 'for sl bom'
        required_columns = [cfg['qty'], cfg['descrip'],
                            cfg['part_num'], cfg['um_sl']]

    if bomtype == 'sw' and  col_name(df, cfg['level_sl']) and not col_name(df, cfg['itm_sw']):
        pass
    elif bomtype == 'sw' and not col_name(df, cfg['itm_sw']):
        printStr = ('\nBOM column {0} missing from sw file {1}.\n'.format(' or '.join(cfg['itm_sw']), pn)
                    + "This if fine unless you're intending that it be a multilevel BOM.\n")
        if not printStr in printStrs:
            printStrs.append(printStr)
            print(printStr)

    missing = []
    for r in required_columns:
        if not col_name(df, r):
            m = ', '.join(r)                     # e.g. ['QTY', 'Qty', 'Qty Per'] -> "QTY, Qty, Qty Per"
            m = ', or '.join(m.rsplit(', ', 1))  # e.g. "QTY, Qty, Qty Per" ->  "QTY, Qty, or Qty Per"
            missing.append(m)
    if missing:
        jm = ';\n    '.join(missing)
        s = ''
        _is = 'is'
        if len(missing) > 1:
            s = 's'
            _is = 'are'
        printStr = ('\nBOM column{0} missing. This BOM will not be processed:\n    {1}'
                     '_{2}\nColumn{3} missing {4}:\n    {5}\n'.format(s, pn, bomtype, s, _is, jm))
        if not printStr in printStrs:
            printStrs.append(printStr)
            print(printStr)
        return True
    else:
        return False


def col_name(df, col):
    '''
    Find one common name from the list of column names
    derived from the DataFrame, df, and the list of names
    from col.  For example, if list(df.columns) is [ITEM
    NO., QTY, LENGTH, DESCRIPTION, PART NUMBER]; and col
    is [PARTNUMBER, PART NUMBER, Part Number, Item,
    Material], then return PART NUMBER because it is
    common to both lists.

    Parameters
    ----------
    df: Pandas DataFrame or list
        If a DataFrame, then df.columns will be extracted
        and it will be converted to a list.  If df is
        instead simply a list, it is a list of column
        names.

    col: list
        List of column names that will be compared to the
        list of column names from df (i.e. from df.columns)

    Returns
    -------
    out: string
        Name of column that is common to both df.columns
        and col
    '''
    try:
        if isinstance(df, pd.DataFrame):
            s = set(list(df.columns))
        else:
            s = set(df)
        intersect = s.intersection(col)
        return list(intersect)[0]
    except IndexError:
        return ""


def row_w_DESCRIPTION(filedata):
    ''' Return the row no. of the row that contains the word
    DESRIPTION (or the equivalent of, i.e. DESCRIP,
    Description, etc.).  That is, determine the row that
    contains the column names.

    Parameters
    ----------
    filedata: str
        A BOM file that has been read in as a string.

    Returns
    -------
    out: int
        0 if row one, or 1 if row two. (Only two rows
        searched.)
    '''
    for c in cfg['descrip']:
        if c in filedata[0]:
            return 0
        else:
            return 1


def deconstructMultilevelBOM(df, source, top='TOPLEVEL'):
    ''' If the BOM is a multilevel BOM, pull out the BOMs
    thereof; that is, pull out the main assembly and the
    subassemblies thereof.  These assys/subassys are placed
    in a python dictionary and returned.  If df is a single
    level BOM, a dictionary with one item is returned.

    For this function to pull out subassembly BOMs from an
    ERP BOM, the column named Level must exist in the ERP
    BOM.  It contains integers indicating the level of a
    subassemby within the BOM; e.g. 1, 2, 3, 2, 3, 3, 3, 4,
    4, 2.  Only multilevel ERP BOMs contain this column.
    On the other hand for this function to  pull out
    subassemblies from a SolidWorks BOM, the column ITEM NO.
    (see set_globals() for other optional names) must exist
    and contain values that indicate which values are
    subassemblies; e.g, with item numbers like "1, 2, 2.1,
    2.2, 3, 4, etc., items 2.1 and 2.2 are members of the
    item number 2 subassembly.

    Parmeters
    =========

    df: Pandas DataFrame
        The DataFrame is that of a SolidWorks or ERP BOM.

    source: string
        Choices for source are "sw" or "sl".  That is, is
        the BOM being deconstructed from SolidWorks or ERP.

    top: string
        Top level part number.  This number is automatically
        generated by the bomcheck program in two ways:
        1. If df originated from a SolidWorks BOM or from a
        single level SyteLine BOM, then “top" is derived
        from the filename; e.g. 091828 from the filename
        091828_sw.xlsx.  2. If df originated from a
        multilevel BOM, (i.e. SL) then it has a column named
        “Level" (i.e. the level of subassemblies and parts
        within subassemblies relative to the main, top
        assembly part number).  In this case the part number
        associated with level "0" is assigned to "top".

    Returns
    =======

    out: python dictionary
        The dictionary has the form {assypn1: BOM1,
        assypn2: BOM2, ...}, where assypn1, assypn2, etc.
        are string objects and are the part numbers for
        BOMs; and BOM1, BOM2, etc. are pandas DataFrame
        objects that pertain to those part numbers.
    '''
    __lvl = col_name(df, cfg['level_sl'])  # if not a multilevel BOM from SL, then is empty string, ""
    __itm = col_name(df, cfg['itm_sw'])
    __pn = col_name(df, cfg['part_num'])  # get the column name for pns
    __descrip = col_name(df, cfg['descrip'])

    p = None
    df[__pn] = df[__pn].astype('str').str.strip() # make sure pt nos. are "clean"
    df[__pn].replace('', 'PN_MISSING', inplace=True)

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
    elif __lvl and __lvl in df.columns:  # dealing w/ SL
        df['__Level'] = df[__lvl].astype(float).astype(int)
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
            elif __lvl and lvl == 0:  #  If multilevel BOM from SL, & lvl==0, then Pn not based on file name, but pn at level 0.
                excelTitle.append((row[__pn], row[__descrip])) # excelTitle is a global variable
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
    '''Argument "find" is a list of strings that are glob
    expressions.  The Pandas Series "series" will be
    evaluated to see if any members of find exists as
    substrings within each member of series.  Glob
    expressions are strings like '3086-*-025' or *2020*.
    '3086-*-025' for example will match'3086-0050-025'
    and '3086-0215-025'.

    The output of the is_in function is a Pandas Series.
    Each member of the Series is True or False depending on
    whether a substring has been found or not.

    xcept is a list of exceptions to those in the find list.
    For example, if '3086-*-025' is in the find list and
    '3086-3*-025' is in the xcept list, then series members
    like '3086-0515-025' or '3086-0560-025' will return a
    True, and '3086-3050-025' or '3086-3060-025' will
    return a False.

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
        Each item is True or False depending on whether a
        match was found or not
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
    '''Take a SolidWorks BOM and restructure it to be like
    that of a SyteLine BOM.  That is, the following is done:

    - For parts with a length provided, the length is
      converted from from_um to to_um (see the function main
      for a definition of these variables). Typically the
      unit of measure in a SolidWorks BOM is inches, and in
      SyteLine, feet.
    - If the part is a pipe or beam and it is listed
      multiple times in the BOM, the BOM is updated so that
      only one listing is shown and the lengths of the
      removed listings are added to the remaining listing.
    - Similar to above, parts such as pipe nipples often
      show up more that once on a BOM.  Remove the excess
      listings and add the quantities of the removed
      listings to the remaining listing.
    - If global variable cfg['drop'] is set to True, then
      part no. (items) listed in the variable cfg['drop']
      will not be shown in the output results.
    - Column titles are changed to match those of SyteLine
      and thus will allow merging to a SyteLine BOM.

    calls: create_um_factors

    Parmeters
    =========

    df: Pandas DataFrame
        SolidWorks DataFrame object to process.

    Returns
    =======

    out: pandas DataFrame
        A SolidWorks BOM with a structure like that of ERP.

    '''
    values = dict.fromkeys(cfg['part_num'], cfg['Item'])
    values.update(dict.fromkeys(cfg['descrip'], cfg['Description']))
    values.update(dict.fromkeys(cfg['qty'], cfg['Q']))
    df.rename(columns=values, inplace=True)
    if not cfg['cspartnumber']:
        df[cfg['Item']] = df[cfg['Item']].str.upper()

    __len = col_name(df, cfg['length_sw'])

    if __len:  # convert lengths to other unit of measure, i.e. to_um
        ser = df[__len].apply(str)
        df_extract = ser.str.extract(r'(\W*)([\d.]*)\s*([\w\^]*)') # e.g. '34.4 ft^2' > '' '34.4' 'ft^2', or '$34.4' > '$' '34.4' ''
        value = df_extract[1].astype(float)
        from_um = df_extract[0].str.lower().fillna('') + df_extract[2].str.lower().fillna('') # e.g. '$ft^2; actually '$' or 'ft^2'
        from_um.replace('', cfg['from_um'].lower(), inplace=True)  # e.g. "" -> "ft"
        from_um = from_um.str.strip().str.lower()   # e.g. "SQI\n" -> "sqi"
        to_um = from_um.apply(lambda x: cfg['toL_um'].lower() if x.lower() in liquidUMs else
                                       (cfg['toA_um'].lower() if x.lower() in areaUMs else cfg['to_um'].lower()))
        ignore_filter = ~is_in(cfg['ignore'], df[cfg['Item']], [])
        df[cfg['U']] = to_um.str.upper().mask(value <= 0.0001, 'EA').mask(~ignore_filter, 'EA')
        factors = (from_um.map(factorpool) * 1/to_um.map(factorpool)).fillna(-1)
        q = df[cfg['Q']].replace('[^\d]', '', regex=True).apply(str).str.strip('.')  # strip away any text
        q = q.replace('', '0').astype(float)  # if any empty strings, set to '0'
        value2 = value * q * factors * ignore_filter
        df[cfg['Q']] = q*(value2<.0001) + value2    # move lengths to the Qty column

    else:
        df[cfg['Q']] = df[cfg['Q']].astype(float)  # If elements strings, 'sum' adds like '2' + '1' = '21'.  But want 2 + 1 = 3
        df[cfg['U']] = 'EA'  # if no length colunm exists then set all units of measure to EA

    df = df.reindex(['Op', 'WC', cfg['Item'], cfg['Q'], cfg['Description'], cfg['U']], axis=1)  # rename and/or remove columns
    dd = {cfg['Q']: 'sum', cfg['Description']: 'first', cfg['U']: 'first'}   # funtions to apply to next line
    df = df.groupby(cfg['Item'], as_index=False).aggregate(dd).reindex(columns=df.columns)

    df = df.applymap(lambda x: x.strip() if type(x)==str else x)  # " BASEPLATE 095000  " -> "BASEPLATE 095000"
    if cfg['del_whitespace']:
        df[cfg['Item']] = df[cfg['Item']].str.replace(' ', '')

    if cfg['drop_bool']==True and cfg['drop']:
        filtr3 = is_in(cfg['drop'], df[cfg['Item']], cfg['exceptions'])
        df.drop(df[filtr3].index, inplace=True)

    df[cfg['WC']] = cfg['WCvalue']    # WC is a standard column shown in a SL BOM.
    df[cfg['Op']] = cfg['OpValue']   # Op is a standard column shown in a SL BOM, usually set to 10

    df.set_index(cfg['Op'], inplace=True)

    return df


def compare_a_sw_bom_to_a_sl_bom(dfsw, dfsl):
    '''This function takes in one SW BOM and one ERP BOM and
    merges them. The newly created merged BOM allows for a
    side by side comparison of the SW/ERP BOMs so that
    differences between the two can be easily distinguished.

    A set of columns in the output are labeled i, q, d, and
    u.  Xs at a row in any of these columns indicate
    something didn't match up between the SW and ERP BOMs.
    An X in the i column means the SW and ERP Items
    (i.e. pns) don't match.  q means quantity, d means
    description, u means unit of measure.

    Parmeters
    =========

    dfsw: Pandas DataFrame
        A DataFrame of a SolidWorks BOM

    dfsl: Pandas DataFrame
        A DataFrame of a SyteLine BOM

    Returns
    =======

    df_merged: Pandas DataFrame
        df_merged is a DataFrame that shows a side-by-side
        comparison of a SolidWorks BOM to a ERP BOM.

    '''
    global printStrs
    if not str(type(dfsw))[-11:-2] == 'DataFrame':
        printStr = '\nProgram halted.  A fault with SolidWorks DataFrame occurred.\n'
        printStrs.append(printStr)
        print(printStr)
        sys.exit()

    # In dfsl if, for example, Item & Material (both names of pn cols) found
    # in table, get rid of the useless col.  First coinciding name from
    # cfg['part_num'] will be used.  Do same for cfg['descrip']
    for x in [cfg['part_num'], cfg['descrip']]:
        lst = [c for c in x if c in dfsl.columns]
        if len(lst)>1:
            dfsl.drop(lst[1:], axis=1, inplace=True)

    values = dict.fromkeys(cfg['part_num'], cfg['Item'])  # type(cfg['Item']) is a str
    values.update(dict.fromkeys(cfg['um_sl'], cfg['U']))  # type(cfg['U']) also a str
    values.update(dict.fromkeys(cfg['descrip'], cfg['Description']))
    values.update(dict.fromkeys(cfg['qty'], cfg['Q']))
    values.update(dict.fromkeys(cfg['obs'], 'Obsolete'))
    dfsl.rename(columns=values, inplace=True) # rename columns so proper comparison can be made
    if not cfg['cspartnumber']:
        dfsl[cfg['Item']] = dfsl[cfg['Item']].str.upper()

    if 'Obsolete' in dfsl.columns:  # Don't use any obsolete pns (even though shown in the SL BOM)
        filtr4 = dfsl['Obsolete'].notnull()
        dfsl.drop(dfsl[filtr4].index, inplace=True)    # https://stackoverflow.com/questions/13851535/how-to-delete-rows-from-a-pandas-dataframe-based-on-a-conditional-expression

    if cfg['drop_bool']==True and cfg['drop']:
       filtr3 = is_in(cfg['drop'], dfsl[cfg['Item']], cfg['exceptions'])
       dfsl.drop(dfsl[filtr3].index, inplace=True)

    dfmerged = pd.merge(dfsw, dfsl, on=cfg['Item'], how='outer', suffixes=('_sw', '_sl') ,indicator=True)
    dfmerged[cfg['Q'] + '_sw'].fillna(0, inplace=True)
    dfmerged[cfg['U'] + '_sl'].fillna('', inplace=True)

    ######################################################################################
    # If U/M in SW isn't the same as that in SL, adjust SW's length values               #
    # so that lengths are per SL's U/M.  Then replace the U/M in the column              #
    # named U_sw with the updated U/M that matches that in SL.                           #
    from_um = dfmerged[cfg['U'] + '_sw'].str.lower().fillna('')                          #
    to_um = dfmerged[cfg['U'] + '_sl'].str.lower().fillna('')                            #
    factors = (from_um.map(factorpool) * 1/to_um.map(factorpool)).fillna(1)              #
    dfmerged[cfg['Q'] + '_sw'] = dfmerged[cfg['Q'] + '_sw'].astype(float) * factors      #
    dfmerged[cfg['Q'] + '_sw'] = round(dfmerged[cfg['Q'] + '_sw'], cfg['accuracy'])      #
    func = lambda x1, x2:   x1 if (x1 and x2) else x2                                    #
    dfmerged[cfg['U'] + '_sw'] = to_um.combine(from_um, func, fill_value='').str.upper() #
    ######################################################################################

    dfmerged.sort_values(by=[cfg['Item']], inplace=True)
    filtrI = dfmerged['_merge'].str.contains('both')  # this filter determines if pn in both SW and SL
    maxdiff = .51 / (10**cfg['accuracy'])
    filtrQ = abs(dfmerged[cfg['Q'] + '_sw'].astype(float) - dfmerged[cfg['Q'] + '_sl']) < maxdiff  # If diff in qty greater than this value, show X
    if not cfg['csdescription']:
        filtrD = dfmerged[cfg['Description'] + '_sw'].str.upper().str.split() == dfmerged[cfg['Description'] + '_sl'].str.upper().str.split()
    else:
        filtrD = dfmerged[cfg['Description'] + '_sw'].str.split() == dfmerged[cfg['Description'] + '_sl'].str.split()
    filtrU = dfmerged[cfg['U'] + '_sw'].astype('str').str.upper().str.strip() == dfmerged[cfg['U'] + '_sl'].astype('str').str.upper().str.strip()
    _pass = '\u2012' #   character name: figure dash
    _fail = 'X'

    i = filtrI.apply(lambda x: _pass if x else _fail)     # _fail = Item not in SW or SL
    q = filtrQ.apply(lambda x: _pass if x else _fail)     # _fail = Qty differs btwn SW and SL
    d = filtrD.apply(lambda x: _pass if x else _fail)     # _fail = Mtl differs btwn SW & SL
    u = filtrU.apply(lambda x: _pass if x else _fail)     # _fail = U differs btwn SW & SL
    i = ~dfmerged[cfg['Item']].duplicated(keep=False) * i # duplicate in SL? i-> blank
    q = ~dfmerged[cfg['Item']].duplicated(keep=False) * q # duplicate in SL? q-> blank
    d = ~dfmerged[cfg['Item']].duplicated(keep=False) * d # duplicate in SL? d-> blank
    u = ~dfmerged[cfg['Item']].duplicated(keep=False) * u # duplicate in SL? u-> blank
    dfmerged[cfg['iqdu']] = i + q + d + u

    dfmerged = dfmerged[[cfg['Item'], cfg['iqdu'], (cfg['Q'] + '_sw'), (cfg['Q'] + '_sl'),
                         cfg['Description'] + '_sw', cfg['Description'] + '_sl', (cfg['U'] + '_sw'), (cfg['U'] + '_sl')]]
    dfmerged.fillna('', inplace=True)
    dfmerged.set_index(cfg['Item'], inplace=True)
    dfmerged[cfg['Q'] + '_sw'].replace(0, '', inplace=True)

    return dfmerged.applymap(lambda x: x.strip() if type(x)==str else x)


def collect_checked_boms(swdic, sldic):
    ''' Match SolidWorks assembly nos. to those from ERP and
    then merge their BOMs to create a BOM check.  For any
    SolidWorks BOMs for which no ERP BOM was found, put
    those in a separate dictionary for output.

    calls: convert_sw_bom_to_sl_format, compare_a_sw_bom_to_a_sl_bom

    Parameters
    ==========

    swdic: dictionary
        Dictionary of SolidWorks BOMs.  Dictionary keys are
        strings and they are of assembly part numbers.
        Dictionary values are pandas DataFrame objects which
        are BOMs for those assembly pns.

    sldic: dictionary
        Dictionary of ERP BOMs.  Dictionary keys are strings
        and they are of assembly part numbers.  Dictionary
        values are pandas DataFrame objects which are BOMs
        for those assembly pns.

    Returns
    =======

    out: tuple
        The output tuple contains two values: 1.  Dictionary
        containing SolidWorks BOMs for which no matching ERP
        BOM was found.  The BOMs have been converted to a
        ERP like format.  Keys of the dictionary are
        assembly part numbers.  2.  Dictionary of merged
        SolidWorks and ERP BOMs, thus creating a BOM check.
        Keys for the dictionary are assembly part numbers.

    '''
    lone_sw_dic = {}  # sw boms with no matching sl bom found
    combined_dic = {}   # sl bom found for given sw bom.  Then merged
    for key, dfsw in swdic.items():
        key2 = key.replace(' ', '') if cfg['del_whitespace'] else key
        if key2 in sldic:
            combined_dic[key2] = compare_a_sw_bom_to_a_sl_bom(
                                convert_sw_bom_to_sl_format(dfsw), sldic[key2])
        else:
            df = convert_sw_bom_to_sl_format(dfsw)
            df[cfg['Q']] = round(df[cfg['Q']].astype(float), cfg['accuracy'])
            lone_sw_dic[key2] = df
    return lone_sw_dic, combined_dic


def concat_boms(title_dfsw, title_dfmerged):
    ''' Concatenate all the SW BOMs into one long list
    (if there are any SW BOMs without a matching ERP BOM
    being found), and concatenate all the merged SW/ERP
    BOMs into another long list.

    Each BOM, before concatenation, will get a new column
    added: assy.  Values for assy will all be the same for
    a given BOM: the pn (a string) of the BOM. BOMs are then
    concatenated.  Finally Pandas set_index function will
    applied to the assy column resulting in the ouput being
    categorized by the assy pn.


    Parameters
    ==========

    title_dfsw: list
        A list of tuples, each tuple has two items: a string
        and a DataFrame.  The string is the assy pn for the
        DataFrame.  The DataFrame is that derived from a SW
        BOM.

    title_dfmerged: list
        A list of tuples, each tuple has two items: a string
        and a DataFrame.  The string is the assy pn for the
        DataFrame.  The DataFrame is that derived from a
        merged SW/ERP BOM.

    Returns
    =======

    out: tuple
        The output is a tuple comprised of two items.  Each
        item is a list. Each list contains one item: a
        tuple.  The structure has the form:

            ``out = ([("SW BOMS", DataFrame1)], [("BOM Check", DataFrame2)])``

        Where...
            "SW BOMS" is the title. (when c=True in the
            bomcheck function, the title will be an assembly
            part no.).  DataFrame1 = SW BOMs that have been
            concatenated together.

            "BOM Check" is another title.
            DataFrame2 = Merged SW/SL BOMs that have been
            concatenated together.

    '''
    dfswDFrames = []
    dfmergedDFrames = []
    swresults = []
    mrgresults = []
    for t in title_dfsw:
        t[1][cfg['assy']] = t[0]
        dfswDFrames.append(t[1])
    for t in title_dfmerged:
        t[1][cfg['assy']] = t[0]
        dfmergedDFrames.append(t[1])
    if dfswDFrames:
        dfswCCat = pd.concat(dfswDFrames).reset_index()
        swresults.append(('SW BOMs', dfswCCat.set_index([cfg['assy'], cfg['Op']]).sort_index(axis=0)))
    if dfmergedDFrames:
        dfmergedCCat = pd.concat(dfmergedDFrames).reset_index()
        mrgresults.append(('BOM Check', dfmergedCCat.set_index([cfg['assy'], cfg['Item']]).sort_index(axis=0)))
    return swresults, mrgresults


def export2excel(dirname, filename, results2export):
    '''Export to an Excel file the results of all the BOM
    checks.

    Parmeters
    =========

    dirname: string
        The directory to which the csv file that this
        function generates will be sent.

    filename: string
        The name of the csv file.

    results2export: list
        List of two tuples with each tuple containing two
        items. First item of each tuple is a string.  The
        second item of each tuple is a Pandas Dataframe.

        The list has this form:

        - [('SW BOMs', dfForSWboms), ('BOM Check', dfForMergedBoms)]

        The two strings are to be either 'SW BOMs' or 'BOM Check'

    Returns
    =======

    out: None
        A csv file named, unless otherwise specified, bomcheck.xlsx.

    '''
    global printStrs
    ok2go = True
    if cfg['overwrite']:
        fn = os.path.join(dirname, filename + '.csv')
        sw_fn = os.path.join(dirname, "sw_"+ filename + '.csv')
        if os.path.exists(fn):
            try:
                os.remove(fn)
            except Exception as e:
                printStr = ('\nOverwrite of output file failed.' +
                            '\nPossibly the current file is open.' +
                            '\n' + str(e) + '\n')
                printStrs.append(printStr)
                ok2go = False
            try:
                os.remove(sw_fn)
            except Exception as e:
                printStr = ('\nOverwrite of output file failed.' +
                            '\nPossibly the current file is open.' +
                            '\n' + str(e) + '\n')
                printStrs.append(printStr)
                ok2go = False
    else:
        fn = definefn(dirname, filename)
        d, f = os.path.split(fn)
        sw_fn = os.path.join(d, "sw_"+ f)

    if ok2go:
        try:
            if len(results2export) == 1:
                df = prepare_multiindex_for_export(results2export[0][1])
                df.to_csv(fn, sep='\t',  encoding='utf-8', index=False)
                print('\n' + fn + ' created\n')
            if len(results2export) == 2:
                sw_df = prepare_multiindex_for_export(results2export[0][1])
                sw_df.to_csv(sw_fn, sep='\t',  encoding='utf-8', index=False)
                df = prepare_multiindex_for_export(results2export[1][1])
                df.to_csv(fn, sep='\t',  encoding='utf-8', index=False)
                print('\n' + sw_fn + ' created\n' + fn + ' created\n')
        except Exception as e:
            printStr = ('\nOverwrite of output file failed.' +
            '\nPossibly the current file is open.' +
            '\n' + str(e) + '\n')
            printStrs.append(printStr)


def definefn(dirname, filename, i=0):
    ''' If bomcheck.csv already exists or sw_bomcheck.csv, return
    bomcheck(1).csv.  If that or sw_bomcheck(1).csv exists, return
    bomcheck(2).csv, and so forth.'''
    global printStrs
    d, f = os.path.split(filename)
    f, e = os.path.splitext(f)
    if d:
        dirname = d   # if user specified a directory, use d instead
    if e and not e.lower()=='.csv':
        printStr = '\n(Output filename extension needs to be .csv' + '\nProgram aborted.\n'
        printStrs.append(printStr)
        print(printStr)
        sys.exit(0)
    else:
        e = '.csv'
    if i == 0:
        fn = os.path.join(dirname, f+e)
        sw_fn = os.path.join(dirname, "sw_"+f+e)
    else:
        fn = os.path.join(dirname, f+ '(' + str(i) + ')'+e)
        sw_fn = os.path.join(dirname, "sw_"+f+ '(' + str(i) + ')'+e)
    if os.path.exists(fn) or os.path.exists(sw_fn):
        return definefn(dirname, filename, i+1)
    else:
        return fn


def prepare_multiindex_for_export(df):
    '''  Remove the duplicate index items created before writing a multiindex
    dataframe to CSV.  E.g.:

    from: 083119 2321-0600-001   to: 083119 2321-0600-001
          083119 3085-0050-025              3085-0050-025
          083119 3180-DV27-000              3180-DV27-000

    Parameters
    ----------
    df : Pandas Dataframe

    Returns
    -------
    out : Pandas Dataframe.
    '''
    new_df = df.copy()
    for i in range(df.index.nlevels, 0, -1):
        new_df = new_df.sort_index(level=i-1)
    replace_cols = dict()
    for i in range(new_df.index.nlevels):
        idx = new_df.index.get_level_values(i)
        new_df.insert(i, idx.name, idx)
        replace_cols[idx.name] = new_df[idx.name].where(
            ~new_df.duplicated(subset=new_df.index.names[:i+1]))
    for col, ser in replace_cols.items():
        new_df[col] = ser
    return new_df.reset_index(drop=True)





def view_help(help_type='bomcheck_help', version=__version__, dbdic=None):
    '''  Open a help webpage for bomcheck, bomcheckgui, troubleshoot, or the
    software license

    Parameters
    ----------
    type_of_help : string
        valid values: 'bomcheck_help', 'bomcheckgui_help',
        'bomcheck_troubleshoot', 'license'.  Default: 'bomcheck_help'
    version : string
        software version.  The version is used to open up help on github's
        site based on the software version.  Default: bomcheck's version no.

    Returns
    -------
    out : None
    '''
    if dbdic and 'cfgpathname' in dbdic:
        # if dbdic provided, comes from bomcheckgui
        cfg.update(get_bomcheckcfg(dbdic['cfgpathname']))

    d = {'bomcheck_help': 'https://htmlpreview.github.io/?https://github.com/'
             'kcarlton55/bomcheck/blob/' + version + '/help_files/bomcheck_help.html',
         'bomcheckgui_help': 'https://htmlpreview.github.io/?https://github.com/'
             'kcarlton55/bomcheckgui/blob/' + version +'/help_files/bomcheckgui_help.html',
         'bomcheck_troubleshoot': 'https://htmlpreview.github.io/?https://github.com/'
             'kcarlton55/bomcheck/blob/' + version + '/help_files/bomcheck_troubleshoot.html',
         'license': 'https://github.com/kcarlton55/bomcheckgui/blob/main/LICENSE.txt'}

    if help_type in cfg:
        webbrowser.open(cfg[help_type])
    elif help_type in d:
        webbrowser.open(d[help_type])
    else:
        print("bomcheck.view_help didn't function correctly")


# before program begins, create global variables
set_globals()

# An example of how the factorpool is used: to convert 29mm to inch:
#   1/(25.4*12) = 0.00328   (inches to feet)
#   1/12 = .08333,          (foot to inches)
#   Then: 29 * factorpool['mm'] / factorpool['in'] = 0.00328 / .08333 = 1.141
# Only lower case keys are acceptable.
factorpool = {'in':1/12,     '"':1/12, 'inch':1/12,   'inches':1/12, chr(8221):1/12,
              'ft':1.0,      "'":1.0,  'feet':1.0,    'foot':1.0,    chr(8217):1.0,
              'yrd':3.0,     'yd':3.0, 'yard':3.0,
              'mm': 1/(25.4*12),       'millimeter':1/(25.4*12),
              'cm':10/(25.4*12),       'centimeter':10/(25.4*12),
              'm':1000/(25.4*12),      'meter':1000/(25.4*12), 'mtr':1000/(25.4*12),
              'sqin':1/144,            'sqi':1/144,            'in^2':1/144,
              'sqft':1,                'sqf':1,                'ft^2':1,
              'sqyd':3,                'sqy':3,                'yd^2':3,
              'sqmm':1/92903.04,       'mm^2':1/92903.04,
              'sqcm':1/929.0304,       'cm^2':1/929.0304,
              'sqm':1/(.09290304),     'm^2':1/(.09290304),
              'pint':1/8,  'pt':1/8,   'qt':1/4,               'quart':1/4,
              'gal':1.0,   'g':1.0,    'gallon':1.0,
              '$':1.0,     'usd':1.0,  'dols.':1.0,  'dols':1.0,  'dol.':1.0,  'dol':1.0,
              'ltr':0.2641720524,      'liter':0.2641720524,   'l':0.2641720524}
areaUMs = set(['sqi', 'sqin', 'in^2', 'sqf', 'sqft', 'ft^2' 'sqyd', 'sqy', 'yd^2',
               'sqmm', 'mm^2', 'sqcm', 'cm^2', 'sqm', 'm^2'])
liquidUMs = set(['pint',  'pt', 'quart', 'qt', 'gallon', 'g', 'gal' 'ltr', 'liter', 'l'])


if __name__=='__main__':
    main()           # comment out this line for testing -.- . -.-.
    #bomcheck('*')   # use for testing



