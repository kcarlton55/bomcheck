# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 21:25:48 2026

@author: Ken Carlton
"""

#import pdb # use with pdb.set_trace()
#from pathlib import Path
import os.path
import pandas as pd
from datetime import date
import os
import warnings
import ast

from bomcheckgui import get_configfn

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# =============================================================================
# path = 'C:\\Users\\Ken\\Documents\\shared\\projects\\mydata\\DVT01261720\\'
# files = [path + '3180-UNV2-000_sw.csv', path + '6890-064545-2_sw.csv',  
#          path + '6890-dvt0161720-01_sw.csv', path + 'DVT0161720_sw.csv',
#          path + 'DVT0161720_sl.xlsx']
# =============================================================================
         

def get_getfilename(kind, files):
    
# =============================================================================
#     path = 'C:\\Users\\Ken\\Documents\\shared\\projects\\mydata\\DVT01261720\\'
#     files = [path + '3180-UNV2-000_sw.csv', path + '6890-064545-2_sw.csv',  
#              path + '6890-dvt0161720-01_sw.csv', path + 'DVT0161720_sw.csv',
#              path + 'DVT0161720_sl.xlsx']
#     production_folder = r"C:\Users\Ken\Documents\shared\projects\mydata\production"    
#     system_folders = "C:\\Users/Ken/Documents\\shared\\projects\\mydata\\Projects folder\\2025\\, C:\\Users\\Ken\\Documents\\shared\\projects\\mydata\\Projects folder\\2026"
#     eng_planner = r"C:\Users\Ken\Documents\shared\projects\mydata\Engineering Planner.xlsm"
# =============================================================================

    # from dbdic looking to get values of keys 'prod_folder', 'proj_folder',
    # and 'eng_planner'.  The first values is s folder, the second a list of
    # folders (each separated by a comma), and the thirt the path name of the
    # file "Engineering Planner.xlsx".
    try:
        configdb = get_configfn()
        with open(configdb, 'r') as file:
            x = file.read()
        dbdic = ast.literal_eval(x)
    except Exception as e:
        msg = ("Error 901:\n\n"
               "Unable to open config.txt file which allows the program\n"
               "to remember user settings.  Default settings will be used.\n"
               "Otherwise the program will run as normal.\n\n" + str(e))
        print(msg)
        #msgtitle = 'Warning'
        #message(msg, msgtitle, msgtype='Warning', showButtons=False)
        dbdic = {'udrop': '3*-025', 'uexceptions': '', 
                      'folder': '', 'file2save2': 'bomcheck',
                      'prod_folder': None, 'proj_folder': None,
                      'eng_planner': None}
        configdb = ''
    production_folder = dbdic.get('prod_folder', None)
    system_folders =  dbdic.get('proj_folder', None)
    eng_planner =  dbdic.get('eng_planner', None)

    # create two lists, one for sw files, the other sl.  Sort the lists pushing
    # to the back of the lists pns with the fifth characater being a -,
    # e.g. 3818-UNV2-000, and 6890-064545-2.  These are subassemblies and not
    # system part numbers.
    sw_files = []
    sl_files = []       
    for f in files:
        _ , fn = os.path.split(f)  
        if '_sw' in fn.lower():
            fn = fn.split('_')[0]
            if fn[4] == '-':
                sw_files.append(fn)
            else:
                sw_files.insert(0, fn)
        elif '_sl' in fn.lower(): 
            fn = fn.split('_')[0]
            if fn[4] == '-':
                sl_files.append(fn)
            else:
                sl_files.insert(0, fn)   
    # Sort again.  System part nos. most often begin with AC, DV, QS, etc.
    # Move these to the start of the lists.            
    sw_files2 = []
    sl_files2 = []
    for sw in sw_files:
        if (sw.startswith('AC') or sw.startswith('DV') or sw.startswith('QS')
                or sw.startswith('QC') or sw.startswith('SV') or sw.startswith('NR')
                or sw.startswith('NY') or sw.startswith('ED')):
            sw_files2.insert(0, sw)
        else:
            sw_files2.append(sw)
    for sl in sl_files:
        if (sl.startswith('AC') or sw.startswith('DV') or sw.startswith('QS')
                or sw.startswith('QC') or sw.startswith('SV') or sw.startswith('NR')
                or sw.startswith('NY') or sw.startswith('ED')):
            sl_files2.insert(0, sl)
        else:
            sl_files2.append(sl)
            
    # sl more often than not will contain a system pn.  It's the first choice.
    if sl_files2:
        systemNo = sl_files2[0]
    elif sw_files2:
        systemNo = sw_files2[0]
        
    # import an Excel file that allow system_pn to CO_number pairing        
    df = pd.read_excel(eng_planner, na_values=[' '], skiprows=3, 
                       usecols=['Item ', 'CO Number'])   # 'Item ', not 'Item', is the eng_planner Excel file
    df.columns = df.columns.str.strip()                  # Change 'Item ' to 'Item'
    df = df.dropna(how='any')
    CO_dict = dict(zip(df['Item'], df['CO Number']))
    CO = CO_dict[systemNo]   
    
    
    def subfunction(system_folders = system_folders):   # this function called when "kind" = projects or bomcheck
        # Create a dic that looks like: 
        # {'C:\\...\\Projects folder\\2025\\':
        #     ['CO00118889 Edwards - ATLAS COPCO Rebrand', ...], 
        # 'C:\\...\\Projects folder\\2026':
        #     ['CO00120400 Edwards - ATLAS COPCO Rebrand', ...]}             
        system_folders = system_folders.replace('\n', '').split(',')  # creates a list object
        system_folders = [s.strip() for s in system_folders]  # remove any leading or trailing spaces from items in the list
        system_folders_dic = {}
        for s in system_folders:
            folders = os.listdir(s)   # obtain a list of dirs in each system folder, e.g. in 2025 folder, 2026, etc.
            system_folders_dic[s] = folders
        flag = False
        for key in system_folders_dic:
            for f in system_folders_dic[key]:
                if CO in f:
                    folder = os.path.join(key, f, 'Engineering')          
                    flag = True
                    break
        if flag:
            if not os.path.exists(folder):
                os.mkdir(folder)   # Make and "Engineering" folder if it does not already exist.
        else:
            folder = key
        return folder, systemNo + '_' + CO
    
    
    if kind == 'production':
        filename = os.path.join(production_folder, fn) + '_' + str(date.today()) 
    elif kind == 'projects':
        folder, pn_CO = subfunction()      
        filename = os.path.join(folder, pn_CO + '_long_' + str(date.today()))
    elif kind == 'bomcheck':
        folder, pn_CO = subfunction()      
        filename = os.path.join(folder, pn_CO + '_bomcheck_' + str(date.today()) )
    
    return filename
    
        
        

        

            

    
    

