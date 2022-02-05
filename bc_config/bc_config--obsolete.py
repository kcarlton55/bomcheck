# This file needs to be in the same directory as the bomcheck.exe
# file, or the bomcheck.py file, for it to take affect.  It allows
# for different column headings in BOMs, different units of 
# measure, etc..

# Adjust this file to suit your needs.  Remove the leading comment
# character, e.g. the pound sign and space, that precedes a setting
# that you wish to adjust.  For any setting not set below, i.e.
# when the comment character is left in place, the bomcheck program will
# use its own default value.  Here are examples of three settings
# that will be active when bomcheck is run... however bomcheck will
# not use them:

example1 = "text, i.e. strings, are enclosed in single or double quotes"

example2 = ["lists", "of", "items", "are", "enclosed", "in", "brackets"]

example3 = 3   # an integer needs no brackets or quote marks.


# Do not do any length conversions for these parts.  That is, at
# times there might be a length given for a part in a SolidWorks BOM
# that is shown for reference only; for example, for a pipe nipple.
# (OK to use glob expressions)
# ignore = ["3086-*"]


# decimal point accuracy applied to lengths in a SolidWorks BOM
# accuracy = 2


# All the column names that might be shown on a SolidWorks BOM for
# part numbers.  Different names occur when templates used to create
# BOMs are not consistent.  Note that names are case sensitive, so
# "Part Number" is not the same as "PART NUMBER".
# part_num_sw = ["PARTNUMBER", "PART NUMBER", "Part Number"]


# All the column names that might be shown on a SyteLine BOM for
# part numbers.  Different names occur when templates used to create
# BOMs are not consistent.  Note that names are case sensitive, so
# "Item" is not the same as "ITEM".
# part_num_sl = ["Item", "Material"]


# All the column names that might be shown on a SolidWorks BOM for
# quantities of parts.  Different names occur when templates used
# to create BOMs are not consistent.  Note that names are case
# sensitive, so "Qty" is not the same as "QTY".
# qty_sw = ["QTY", "QTY."]


# All the column names that might be shown on a SyteLine BOM for
# quantities of parts.  Different names occur when templates used
# to create BOMs are not consistent.  Note that names are case
# sensitive, so "Qty" is not the same as "QTY".
# qty_sl = ["Qty", "Quantity", "Qty Per"]


# All the column names that might be shown on a SolidWorks BOM for
# part descriptions.  Different names occur when templates used
# to create BOMs are not consistent.  Note that names are case
# sensitive, so "Description" is not the same as "DESCRIPTION".
# descrip_sw = ["DESCRIPTION"]


# All the column names that might be shown on a SolidWorks BOM for
# part descriptions.  Different names occur when templates used
# to create BOMs are not consistent.  Note that names are case
# sensitive, so "Description" is not the same as "DESCRIPTION".
# descrip_sl = ["Material Description", "Description"]


# All the column names that might be shown on a SyteLine BOM for
# Unit of Measure.  Different names occur when templates used
# to create BOMs are not consistent.  Note that names are case
# sensitive, so "um" is not the same as "UM".
# um_sl = ["UM", "U/M"]


# All the column names that might be shown on a Solidworks BOM for
# the item number of a part.  Different names occur when templates
# used to create BOMs are not consistent.  Note that names are case
# sensitive, so "Item No." is not the same as "ITEM NO.".  (Note:
# this program is not designed to manage item numbers shown on a
# SyteLine BOM.).  The bomcheck program uses this column to determine
# the level of a subassembly within a multilevel SolidWorks BOM.  In
# this case, item numbers will be like 1, 2, 3, 3.1, 3.2, 4, 5, 5.1;
# where items 3 and 5 are subassemblies.
# itm_num_sw = ["ITEM NO."]


# All the column names that might be shown on a SyteLine BOM for
# subassembly level.  Different names occur when templates used to
# create BOMs are not consistent.  Note that names are case
# sensitive, so "Level" is not the same as "LEVEL".  (Note: this
# program is not designed to handle subassy levels that might be
# shown on a SolidWorks BOM.  For SolidWorks, the item number column
# is used to determine subassembly level). Items in the level column
# will look like: 0, 1, 1, 2, 2, 1, 2, 2, 3, 1... and so forth
# level_sl = ["Level"]


# Various names that the Length column in SolidWorks might have.
# Note that, in SolidWorks, the quantity column the number of a
# particular item, and the length column contains the length of that
# item.  For exaample, a quatity of 4 beams, each 20" long.
# length_sw: ['LENGTH', 'Length', 'L', 'SIZE', 'AMT', 'AMOUNT', 'MEAS']


# If an area of an item is specified in the SW length column,
# e.g. 13.5 sqmm, then during program execution convert to this U/M
# just prior to comparing the SW BOM to that in SyteLine.  And if
# the item is found in the SyteLine BOM, then convert it to the
# U/M that is there.
# toA_um = 'SQI'


# If a liguid volume of an item is specified in the length column, e.g. 4.5 pt,
# convert to this U/M.  If the item is found in the SyteLine BOM, it will be
# converted to the U/M there, and this U/M will be ignored.
# toL_um = 'GAL'


#####################################################################
#                                                                   #
#      The settings below this point work only if bomcheck is run   #
#      from the command line.  That is, bomcheckgui is not used.    #
#                                                                   #
#####################################################################


# Part numbers in this list will be discarded from the SolidWorks BOM
# so that they will not show up in the bom check report (OK to use glob
# expressions, https://en.wikipedia.org/wiki/Glob_(programming)):
# drop = ["3*-025", "3*-0", "3800-*"]


# Excecptions to the part numbers in the drop list shown above
# (OK to use glob expressions):
# exceptions = ["3510-0200-025", "3086-1542-025"]


# The unit of measure of lengths from a SolidWorks BOM are understood
# to be inches unless a unit of measure is afixed to a length
# (e.g. 507mm).  The unit of measure you specifiy must be surrounded
# by quotation marks.  Valid units of measure: inch, feet, yard,
# millimenter, centimeter, meter.
# from_um = "inch"


# If no matching item is found in a SyteLine BOM for a given item
# in a SW BOM, then convert to this U/M.  Else convert to the U/M
# given in the SL BOM measure.
# to_um = "feet"
