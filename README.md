# **bomcheck**


## **What the program does**
The bomcheck.py program compares Bills of Materials (BOMs). BOMs from
a CAD (Computer Aided Design) program like SolidWorks are compared to
BOMs from an ERP (Enterprise Resource Planning) program like SyteLine.
The CAD and ERP programs must be able to export to Excel files
because that is where bomcheck gathers data from.

## **How to install**
Assuming that you already have Python on your machine, use the package
manager software [pip](https://en.wikipedia.org/wiki/Pip_(package_manager))
that comes with Python and run this from a command line:

`pip install bomcheck`

## **Compared BOMs come from Excel files**
The name of a file containing a BOM from the CAD program has the syntax:
`PartNumberOfBOM_sw.xlsx`.  That is, names like 0399-2344-005_sw.xlsx,
093352_sw.xlsx, and 35K2445_sw.xlsx are all legitimate file names. The
names of the files from the ERP program have the same syntax, but instead
end with `_sl.xlsx`. Thus the names will look like 0399-2344-005_sl.xlsx,
093352_sl.xlsx, and 35K2445_sl.xlsx. The program will match the
0399-2344-005_**sw**.xlsx file to the 0399-2344-005_**sl**.xlsx
file, and so forth.


## **Multilevel BOMs are allowed**
A file can contain a mulilevel BOM.  In which case individual BOMs are
extracted from a top level BOM.  For a BOM from the ERP program to be
recognized as a multilevel BOM, a column named "Level" must exist
that gives the relative level of a subassembly to the main assembly.
(The name "Level" can be altered with the file bomcheck.cfg.  See info
below.) The Level column starts out with "0" for the top level assembly,
"1" for part/subassemblies under the main assembly, "2" for a
part/subassembly under a Level "1" subassembly, and so forth. From the
CAD program, it is similar.  However item nos. indicate the Level, for
example item nos. like 1, 2, 3, 3.1, 3.2, 3.2.1, 3.2.2, 3.3, 4, etc.,
where item 3 is a subassembly with parts under it.


## **How to run**

Enter this on the command line to run:

`bomcheck`

(An easier way to get started is to use [bomcheckgui](https://github.com/kcarlton55/bomcheckgui))


## **Sample output**
An Excel file is output. Shown below is an example of the result of a BOM
comparison:

| assy   | Item   | IQDU | Q_sw | Q_sl | Descripton_sw | Description_sl | U_sw | U_sl |
|--------|--------|------| :-:  | :-:  |---------------|----------------| :-:  | :-:  |
| 730322 | 130031 | XXXX |      |  1   |               | HOUSING        |      |  EA  |
|        | 130039 | XXXX |  1   |      | HOUSING       |                |  EA  |      |
|        | 220978 | ‒‒‒‒ |  1   |  1   | SPUR GEAR     | SPUR GEAR      |  EA  |  EA  |
|        | 275000 | ‒‒‒‒ | 0.35 | 0.35 | TUBE          | TUBE           |  FT  |  FT  |
|        | 380000 | ‒‒‒‒ |  2   |  2   | BEARING       | BEARING        |  EA  |  EA  |
|        | 441530 | ‒‒‒‒ |  1   |  1   | SHIFT ASSY    | SHIFT ASSY     |  EA  |  EA  |
|        | 799944 | ‒‒X‒ |  1   |  1   | SHAFT         | AXLE           |  EA  |  EA  |
|        | 877325 | ‒XX‒ |  3   |  1   | PLUG          | SQ. HEAD PLUG  |  EA  |  EA  |
|        | 900000 | ‒‒‒‒ | 0.75 | 0.75 | OIL           | OIL            |  GAL |  GAL |
| 441530 | 433255 | ‒‒‒‒ |  1   |  1   | ROD           | ROD            |  EA  |  EA  |
|        | 500000 | ‒‒‒‒ |  1   |  1   | SHIFT FORK    | SHIFT FORK     |  EA  |  EA  |
|        | K34452 | ‒‒‒‒ |  1   |  1   | SPRING PIN    | SPRING PIN     |  EA  |  EA  |

The column IQDU shows Xs if  ***I***tem, ***Q***uantity, ***D***escription,
or ***U***nit of measure don't match between the two BOMs. Q_sw is the quantity
per the CAD BOM, Q_sl per the ERP BOM, and so forth. In the example above,
1309031 is in the  ERP BOM, but not in SolidWorks. 130039 is in the CAD's BOM,
but not in the ERP's BOM.


## **Units of measure**
If a Unit of Measure (U/M) is not given for a value in the Length column of
a SolidWorks' BOM, then the U/M is assumed to be inches unless explicity
specified, e.g. 336.7 mm. The program recognizes the follwing U/Ms:

`in, inch, ", ft, ', feet, foot, yrd, yd, yard, mm, millimeter, cm, centimeter, m, meter, mtr, sqin, sqi, sqft, sqf, sqyd, sqy, sqmm, sqcm, sqm, pint, pt, qt, quart, gal, g, gallon, ltr, l, liter`

When the program is run, values will be converted to the U/M given in the ERP's
BOM.  For example, if the ERP program uses FT as a U/M, then comparison results
will be shown in feet.


## **bomcheck.cfg**
Bomcheck has a configuration file available named bomcheck.cfg.  With it the
default U/M measure can be switched from inches to mm, or to some other U/M.
Also, column names can be changed, and so forth.  Within the bomcheck.cfg
file are explanations about settings that can be employed.  To get started, download
the bomcheck.cfg from [here](https://github.com/kcarlton55/bomcheck/tree/master/docs),
then open the file with a text editor and modify it as suits you best.

&nbsp;

<hr style="border:2px solid grey">

&nbsp;

You can try out the program online by clicking:&nbsp; &nbsp;
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/kcarlton55/bomcheck/blob/master/bc-colab.ipynb) or
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/kcarlton55/bomcheck/master?labpath=bomcheck.ipynb),&nbsp; &nbsp;
These are both
[Jupyter Notebooks](https://www.codecademy.com/article/how-to-use-jupyter-notebooks).  Open the file browser of the notebook (folder icon at upper left), create a folder named "mydata", and upload your data to it.

For more information, see the web page [bomcheck_help.html](https://htmlpreview.github.io/?https://github.com/kcarlton55/bomcheck/blob/master/help_files/bomcheck_help.html)



