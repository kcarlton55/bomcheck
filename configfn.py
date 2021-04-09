#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  7 20:12:11 2021

@author: ken
"""

import os.path
import sys
# import dbm

def get_configfn():
    '''Get the file names used to store config settings.
    1. Derive a suitable dir path to where config files for the bomcheck
    will be stored.  The name and location depend on what OS the bomcheck
    program is being used... Windows or Linux.
    2.  If directories in the pathname do not already exists, crete them.
    3.  Derive two filenames (prefixed with the dir path) that will be used
    to store bomcheck configurations.
        a.  config.db - will contain the primary info.
        b.  bc_config.py - for advanced use if bomcheck is ever used outside
            Dekker.
    4  If the config.db file doesn't already exist, create it and put a 
       value in it: 3*-025
    5.  Return the two filenames in a tuple.
    '''
    if sys.platform[:3] == 'win':
        datadir = os.getenv('LOCALAPPDATA')
        path = os.path.join(datadir, 'bomcheck')
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
        configdb = os.path.join(datadir, 'bomcheck', 'config.txt')
        bc_config = os.path.join(datadir, 'bomcheck', 'bc_config.py')
                
    elif sys.platform[:3] == 'lin' or sys.platform[:3] == 'dar':  # linux or darwin (Mac OS X)
        homedir = os.path.expanduser('~')
        path = os.path.join(homedir, '.bomcheck')
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True) 
        configdb = os.path.join(homedir, '.bomcheck', 'config.txt')
        bc_config = os.path.join(homedir, '.bomcheck', 'bc_config.py')   
            
    else:
        printStr = ('At method "get_db_pathname", a suitable path was not found to\n'
                    'create file bc_settings.db.  Notify the programmer of this error.')
        print(printStr) 
        return ('', '')
    
    _bool = os.path.exists(configdb)
    if not _bool or (_bool and os.path.getsize(configdb) == 0):
        with open(configdb, 'w') as file: 
            file.write("{'udrop':'3*-025'}")
                
    return (configdb, bc_config)
    




