# **bomcheck**


## **WHAT THE PROGRAM DOES**
The bomcheck.py program compares Bills of Materials (BOMs). BOMs from
a CAD (Computer Aided Design) program like SolidWorks are compared to
BOMs from an ERP (Enterprise Resource Planning) program like SyteLine. 
The CAD and ERP programs must be able to export to excel files 
because that is where bomcheck gathers data from.

## **HOW TO INSTALL**
Assuming that you already have Python on your machine, use the package
manager software [pip](https://en.wikipedia.org/wiki/Pip_(package_manager))
that comes with Python:

`pip install bomcheck`

## **BOMS ARE COMPARED BASED ON FILE NAMES**
The name of a file containing a BOM from the CAD program has the syntax:
`PartNumberOfBOM_sw.xlsx`.  That is names like 0399-2344-005_sw.xlsx,
093352_sw.xlsx, and 35K2445_sw.xlsx are all legitimate file names. The
names of the files from the ERP program have the same syntax, but instead
end with `_sl.xlsx`. Thus the names will look like 0399-2344-005_sl.xlsx, 
093352_sl.xlsx, and 35K2445_sl.xlsx. The program will match the
0399-2344-005_**sw**.xlsx file to the 0399-2344-005_**sl**.xlsx 
file, and so forth.


## **MULTILEVEL BOMS ALLOWED**
A file can contain a mulilevel BOM, in which case individual BOMs are
extracted from a top level BOM.  For a BOM from the ERP program to be 
recognized as a multilevel BOM, a column named "Level" must exist
that gives the relative level of a subassembly to the main assembly. 
(The name "Level" can be altered with the file bc_config.py.  See info 
below.) The Level column starts out with "0" for the top level assembly,
"1" for part/subassemblies under the main assembly, "2" for a 
part/subassembly under a Level "1" subassembly, and so forth. From the
CAD program, it is similar.  However item nos. indicate the Level, for 
example item nos. like 1, 2, 3, 3.1, 3.2, 3.2.1, 3.2.2, 3.3, 4, etc.,
where item 3 is a subassembly with parts under it.


## **HOW TO RUN BOMCHECK**

From the command line do:

`bomcheck`
 
If you wish to use Jupyter Notebook, look at the files *bomcheck.ipynb*, 
*mydata/README.txt*, and *exampledata/README.txt*, located at:
[https://github.com/kcarlton55/bomcheck](https://github.com/kcarlton55/bomcheck)


If you would rather use a graphical user interface, look at: bomcheckgui.


## **SAMPLE OUTPUT**
An Excel file is output. Shown below is an example of the result of a BOM
comparison that the bomcheck program outputs:

| assy   | Item   | i | q | d | u | Q_sw | Q_sl | Descripton_sw | Description_sl | U_sw | U_sl |
|--------|--------|---|---|---|---| :-:  | :-:  |---------------|----------------| :-:  | :-:  |
| 730322 | 130031 | X | X | X | X |      |  1   |               | HOUSING        |      |  EA  |
|        | 130039 | X | X | X | X |  1   |      | HOUSING       |                |  EA  |      |
|        | 220978 |   |   |   |   |  1   |  1   | SPUR GEAR     | SPUR GEAR      |  EA  |  EA  |
|        | 275000 |   |   |   |   | 0.35 | 0.35 | TUBE          | TUBE           |  FT  |  FT  |
|        | 380000 |   |   |   |   |  2   |  2   | BEARING       | BEARING        |  EA  |  EA  |   
|        | 441530 |   |   |   |   |  1   |  1   | SHIFT ASSY    | SHIFT ASSY     |  EA  |  EA  |
|        | 799944 |   |   | X |   |  1   |  1   | SHAFT         | AXLE           |  EA  |  EA  |
|        | 877325 |   | X | X |   |  3   |  1   | PLUG          | SQ. HEAD PLUG  |  EA  |  EA  |
|        | 900000 |   |   |   |   | 0.75 | 0.75 | OIL           | OIL            |  GAL |  GAL |
| 441530 | 433255 |   |   |   |   |  1   |  1   | ROD           | ROD            |  EA  |  EA  |
|        | 500000 |   |   |   |   |  1   |  1   | SHIFT FORK    | SHIFT FORK     |  EA  |  EA  |
|        | K34452 |   |   |   |   |  1   |  1   | SPRING PIN    | SPRING PIN     |  EA  |  EA  |

The columns i, q, d, and u show Xs if  ***i*** tem, ***q***uantity, ***d***escription,
or ***u***nit of measure don't match between the two BOMs. Q_sw is the quantity
per the CAD BOM, Q_sl per the ERP BOM, and so forth. In the example above, 
1309031 is in the  ERP BOM, but not in SolidWorks. 130039 is in the CAD's BOM,
but not in the ERP's BOM.


## **UNITS OF MEASURE**
If a unit of measure (U/M) is not given for a value in the Length column of a SolidWorks' BOM,
then the U/M is assumed to be inches unless explicity specified, e.g. 336.7mm. The program will 
recognize the following abreviations for U/Ms:

`in, inch, ", ft, ', feet, foot, yrd, yd, yard, mm, millimeter, cm, centimeter, m, meter, mtr, sqin, sqi, sqft, sqf, sqyd, sqy, sqmm, sqcm, sqm, pint, pt, qt, quart, gal, g, gallon, ltr, l, liter`

When the program is run, values will be converted to the U/M given in the ERP's BOM. 
For example, if the ERP program uses FT as a U/M, then comparison results will be shown
in feet.


## **BOMCHECK.CFG**
Bomcheck has a configuration file available named bomcheck.cfg.  With it the
default U/M measure can be switched from inches to mm, or to some other U/M.
Also, column names can be changed, and so forth.  Within the bomcheck.cfg
file are explanations about settings That can be employed.  Open the file
with a text editor program such as Microsoft's wordpad.

&nbsp;

<hr style="border:2px solid grey">

&nbsp;

You can try out the program online by clicking:&nbsp; &nbsp;
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/kcarlton55/bomcheck/blob/master/bc-colab.ipynb) or
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kcarlton55/bomcheck/master?labpath=bomcheck.ipynb),&nbsp; &nbsp;
These are both
[Jupyter Notebooks](https://www.codecademy.com/article/how-to-use-jupyter-notebooks).  Open the file browser of the notebook (folder icon at upper left), create a folder named "mydata", and upload your data to it.
 
For more information, see the web page [bomcheck_help.html](https://htmlpreview.github.io/?https://github.com/kcarlton55/bomcheck/blob/master/help_files/bomcheck_help.html)



