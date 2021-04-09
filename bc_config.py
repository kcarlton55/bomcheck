# This file needs to be in the same directory as the bomcheckgui.exe
# (or bomcheck.exe) file for it to take affect.  It allows for different
# column headings in Excel files, different units of measure, etc..

# Adjust this file to suit your needs.  Remove the leading comment
# character, e.g. the pound sign and space, that precedes a setting
# that you wish to adjust.  For any setting not set below, that is
# the comment character is left in place, the bomcheck program will 
# use its own default value.  Here are examples of three settings
# that will be active in the bomcheck program (but not used by it):

example1 = "text, i.e. strings, are enclosed in single or double quotes"

example2 = ["lists", "of", "items", "are", "enclosed", "in", "brackets"]

example3 = 3   # an integer needs no brackets or quote marks.


# Do not do any length conversions for these parts.  That is, at
# times there might be a length given for a part in a SolidWorks BOM
# that is shown for reference only; for example, for a pipe nipple.
# (OK to use glob expressions)
# discard_length = ["3086-*"] 


# decimal point accuracy applied to lengths in a SolidWorks BOM
# accuracy = 2


# Set the time zone so that the correct time and date is shown on the
# Excel file that bomcheck ouputs to.  For valid timezones see:
# https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
# Or set timezone to "local" to get the time and date from the
# computer or server on which bomcheck is run
# timezone = "US/Central"


# The unit of measure of lengths from a SolidWorks BOM are understood
# to be inches unless a unit of measure is afixed to a length
# (e.g. 507mm).  The unit of measure you specifiy must be surrounded
# by quotation marks.  Valid units of measure: inch, feet, yard,
# millimenter, centimeter, meter.
# from_um = "inch"


# Lengths from a SolidWorks BOM are converted to a length with this
# unit of measure in order to compare them to lengths in SyteLine.
# Any lengths in SyteLine are all considered to be per this unit of
# measure.
# to_um = "feet"


# All the column names that might be shown on a SolidWorks BOM for
# part numbers.  Different names occur when templates used to create
# BOMs are not consistent.  Note that names are case sensitive, so
# "Part Number" is not the same as "PART NUMBER".
# part_num_sw = ["PARTNUMBER", "PART NUMBER", "Part Number"]


# All the column names that might be shown on a SyteLine BOM for
# part numbers.  Different names occur when templates used to create
# BOMs are not consistent.  Note that names are case sensitive, so
# "Part Number" is not the same as "PART NUMBER".
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


# Number of rows to skip when reading data from the Excel/csv files
# that contain SolidWorks BOMs.  The first row that bomcheck is to 
# evaluate is the row containing column headings such as ITEM NO.,
# QTY, PART NUMBER, etc.
# skiprows_sw = 1


# Number of rows to skip when reading data from the Excel/csv files
# that contain SyteLine BOMs.  The first row to evaluate from SL BOMs
# is the row containing column headings such as Item, Decription, etc.
# skiprows_sl = 0


#####################################################################
#                                                                   #
#      The settings below work only if bomcheck is run from the     #
#      command line or, when using bomcheckgui, if the drop and     #
#      exceptions settings in bomcheckgui are empty.                #
#                                                                   #
#####################################################################


# Part numbers in this list will be discarded from the SolidWorks BOM
# so that they will not show up in the bom check report (OK to use glob
# expressions, https://en.wikipedia.org/wiki/Glob_(programming)):
# drop = ["3*-025", "3*-0", "3800-*"]


# Excecptions to the part numbers in the drop list shown above
# (OK to use glob expressions):
# exceptions = ["3510-0200-025", "3086-1542-025"]


