# Place this file in you home directory; e.g. C:\Users\k_carlton
# Adjust this file to suit your needs.  Remove the comment characters, 
# e.g. the "# " characters in "# accuracy", to employ those settings that are
# commented out below.  For any settings not employed below, the bomcheck
# program will use its own defaults.

# Part numbers in this list will be discarded from the SolidWorks BOM so that
# they will not show up in the bom check report:
drop = ["3*-025", "3*-0", "3800-*"]

# Excecptions to the part numbers in the drop list shown above:
exceptions = ["3510-0200-025", "3086-1542-025"]

# Do not do any length conversions for these parts.  That is, at
# times there might be a length given for a part in a SolidWorks BOM
# which is used for reference only.  For the bom check this length
# is discarded.
# discard_length = ['3086-*]  

# decimal point accuracy applied to lengths of a SolidWorks BOM
# accuracy = 2

# Set the time zone so that the correct time is shown on a bom check report.
# For valid timezones see:
# https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
# timezone = "US/Central"  
