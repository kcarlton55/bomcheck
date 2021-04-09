#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  6 22:19:57 2021

@author: ken
"""

import os


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
        
        '#####################################################################\n'
        '#                                                                   #\n'
        '#      The settings below work only if bomcheck is run from the     #\n'
        '#      command line or, when using bomcheckgui, if the drop and     #\n'
        '#      exceptions settings in bomcheckgui are empty.                #\n'
        '#                                                                   #\n'
        '#####################################################################\n\n\n'
                
        '# Part numbers in this list will be discarded from the SolidWorks BOM\n',
        '# so that they will not show up in the bom check report (OK to use glob\n'
        '# expressions, https://en.wikipedia.org/wiki/Glob_(programming)):\n',
        '# drop = ["3*-025", "3*-0", "3800-*"]\n\n\n',


        '# Excecptions to the part numbers in the drop list shown above\n',
        '# (OK to use glob expressions):\n',
        '# exceptions = ["3510-0200-025", "3086-1542-025"]\n\n\n',
        
        
        
        ]
    readme_contents = [
        'You should never have to adjust any settings within the files that are\n',
        'located in this directory.\n\n',
        
        'Settings within the file bc_config.py are primarily to allow future use\n'
        'of this program by, for example, a sister company.  If, for example,\n',
        'column headings are different, settings in the bc_config.py file can\n',
        'be adjusted to compensate.  An example of a different column heading\n',
        'might be "Número de Pieza" instead of "Part Number"\n\n',
        
        'Settings within the file named config.txt are generated by the\n',
        'bomcheckgui program.  Do not edit this file.  Let the bomcheckgui\n',
        'program do it.\n\n',
        
        'Edit the bc_config.py file with a text editor like Notepad or Wordpad\n',
        'There are explanations in the bc_config.py file about how to adjust\n',
        'settings.\n\n',
        
        'If the bc_config.py is not edited correctly, for example a bracket is\n',
        'missing or a comma is out of place, then the bomcheck program may\n',
        'malfunction.  A quick remedy is to close the bomcheck program and\n',
        'delete all the files in this folder.  The next time the bomcheck\n',
        'program is ran, the orignal, default files will be regenerated.\n\n'
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