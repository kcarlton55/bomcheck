# Place this file in you home directory; e.g. C:\Users\k_carlton
# Adjust this file to suit your needs.  Remove the comment characters, 
# e.g. the "# " characters that are in front of a setting that you
# wish to employ.  For example, change "# accuracy = 2" to 
# "accuracy = 2".  For setting not set below, the bomcheck program
# will use it's own defaults.


# Part numbers in this list will be discarded from the SolidWorks BOM so that
# they will not show up in the bom check report:
drop = ["3*-025", "3*-0", "3800-*"]


# Excecptions to the part numbers in the drop list shown above:
exceptions = ["3510-0200-025", "3086-1542-025"]


# Do not do any length conversions for these parts.  That is, at
# times there might be a length given for a part in a SolidWorks BOM
# which is used for reference only.  For the bom check this length
# is discarded.
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





