# Place this file in you home directory, e.g. C:\Users\k_carlton, or
# in the same direcory as the bomcheck program.  Adjust this file to
# suit your needs.  Remove the comment characters, e.g. the pound
# character and space character that immediate follows (# ), in order
# to activate a particular setting.  For any setting not set below, 
# the bomcheck program will set it's values it deems appropriate.


# Part numbers in this list will be discarded from the SolidWorks BOM so that
# they will not show up in the bom check report:
# drop = ["3*-025", "3*-0", "3800-*"]


# Excecptions to the part numbers in the drop list shown above:
# exceptions = ["3510-0200-025", "3086-1542-025"]


# Do not do any length conversions for these parts.  That is, at
# times there might be a length given for a part in a SolidWorks BOM
# that is shown for reference only; for example, for a pipe nipple.
# discard_length = ["3086-*"]  


# decimal point accuracy applied to lengths of a SolidWorks BOM
# accuracy = 2


# Set the time zone so that the correct time is shown on a bom check report.
# For valid timezones see:
# https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
# timezone = "US/Central"  


# Unit of measure that lengths from a SolidWorks BOM are understood
# to be unless a unit of measure is afixed to a length, for example 
# 507mm.  The unit of measure you specifiy must be surrounded by 
# quotation marks.  Valid units of measure: inch, feet, yard,
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
# sensitive, so "um" is not the same as "UM".  (Note: this
# program is not designed to handle in Units of Measure that
# might be shown on a SolidWorks BOM.)
# um_sl = ["UM", "U/M"]


# All the column names that might be shown on a Solidworks BOM for
# the item number of a part.  Different names occur when templates
# used to create BOMs are not consistent.  Note that names are case 
# sensitive, so "Item No." is not the same as "ITEM NO.".  (Note: 
# this program is not designed to manage in item numbers that
# might be shown on a SyteLine BOM.).  The bomcheck program uses
# this column to determine the level of a subassembly within a
# multilevel SolidWorks BOM.  In this case, item numbers will be
# like 1, 2, 3, 3.1, 3.2, 4, 5, 5.1; where items 3 and 5 are
# subassemblies.
# itm_num_sw = ["ITEM NO."]


# All the column names that might be shown on a SyteLine BOM for
# subassembly level.  Different names occur when templates used to
# create BOMs are not consistent.  Note that names are case 
# sensitive, so "Level" is not the same as "LEVEL".  (Note: this
# program is not designed to handle in subassy levels that might be
# shown on a SolidWorks BOM.  For SolidWorks, the item number column
# is used to determine subassembly level) Items in the level column 
# will look like: 0, 1, 1, 2, 2, 1, 2, 2, 3, 1... and so forth
# level_sl = ["Level"]
















