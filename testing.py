#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 22:12:44 2019

@author: ken
"""

import pprint
import pandas as pd

f = '/home/ken/projects/bomdata/top_level/084387_sltop2.xlsx'
f = '/home/ken/projects/bomdata/top_level/084387_truncated_sltop.xlsx'
df = pd.read_excel(f, na_values=[' '])

#for i, x in enumerate(df['Level']):
#    print(i, x)


collectPNs = []
pushPopPNs = []
lvl = 0
for item, row in df.iterrows():
    if row['Level'] == 0:
        collectPNs.append('TOP')
        pushPopPNs.append(row['Item'].strip())
    elif row['Level'] > lvl:
        lvl = row['Level']
        collectPNs.append(pushPopPNs[-1])
        pushPopPNs.append(row['Item'].strip())  
    elif row['Level'] == lvl:
        collectPNs.append(pushPopPNs[-2])
        pushPopPNs.pop()
        pushPopPNs.append(row['Item'].strip())
    elif row['Level'] < lvl:
        #for i in range(row['Level'] - lvl)
        pushPopPNs.pop()
        pushPopPNs.pop()
        pushPopPNs.append(row['Item'].strip())
        collectPNs.append(pushPopPNs[-2])
        lvl = row['Level']
        
for i, x in enumerate(collectPNs):
    print(i+2, x)
    
        

        
        
        

    