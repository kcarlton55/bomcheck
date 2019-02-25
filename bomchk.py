#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 21:18:58 2019

@author: ken

https://www.youtube.com/watch?v=oMyd0ay2QhI 1
https://www.youtube.com/watch?v=1o3XGOT2YUs 2
https://www.youtube.com/watch?v=SXOG5GOsscU 3

# 2

from easygui import *

version = 'Tutorial v.1.0'

options = ["Choice 1: Ice Cream", "Choice 2: Soda Pop", "Choice 3: Pizza", "Cancel"]

button = buttonbox("Choose a button", title=version, choices=options)

if button == 'a': #options[0]:
    button = "You chose ice cream"
elif button == options[1]:
    button = "You chose soda pop"
elif button == options[2]:
    button = "You chose pizza"
else:
    button = "You didn't chose anything"
    

msgbox(msg=button, title=version)


# 3

from easygui import *

version = "Video Tutorial #3"
v = ccbox(title=version)
if v == 1:
    msgbox(msg='You chose to continue', title=version)
elif v == 0:
    msgbox(msg="Exiting...", title=version)
    
"""
#4
from easygui import *
msg = "Please make a choice"
title = "Choice Box"
choices = ["Choice 1: Ice Cream", "Choice 2: Soda Pop", 
          "Choice 3: Cake", "Choice 4: Ice Cream",
          "Choice 5: Soda Pop", "Choice 6: Cake"]
var = choicebox(msg, title, choices)
print(var)
print(choices[1])
if var == choices[1]:
    msgbox(msg = "You cholse Soda Pop!  Yeah!", title=title)