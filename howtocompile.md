# How to Compile bomcheckgui.py

An executable EXE file can be created to use on a Microsoft Windows 10 computer.  Here I explain how this is done.

First of all, I use the Anaconda version of Python.  Anaconda is just Python, from https://www.python.org/, but with many extra packages installed.  One of these extra packages is Pandas which bomcheckgui.py heavily relies upon.  Anaconda can be downloaded from https://www.anaconda.com/distribution/.  The method I use to compile the bomcheckgui.py program relies on Anaconda's functionality.

bomcheckgui.exe is created with an add-on app called pyinstaller.  But pyinstaller will not work without some prep work being done first.  An "environment" must be first established conducive to bomcheckgui.py's compilation, otherwise the compile process will fail.  A cheat-sheet I use explaining setting up an environment is at https://kapeli.com/cheat_sheets/Conda.docset/Contents/Resources/Documents/index.  It would be better though that you do some research for yourself to learn more about setting up environments.

The environmment requires that certain add-on apps be present within the environment prior to compilation.  These necesary files are listed in the file named requirements.txt.  Furthermore the compile process MUST be done on a Windows 10 machine; that is, the type of machine you wish to use bomcheck on.

With Anaconda now installed on my machine, here are the steps to set up the environment (using an Anaconda cmd window):

```
$ conda create -n pyinst python=3.7
$ conda activate pyinst

$ conda install pandas
$ conda install xlrd
$ conda install openpyxl
$ conda install xlsxwriter
$ conda install -c conda-forge pyinstaller 
$ conda install PySide2 (or PyQt5 if that with bomcheckgui is using).
```

(Note that on a Windows machine go "Anaconda" in the Windows menu and look to activate a command prompt window there.)  The first line creates the environment called "pyinst".  The second activates the environment.  The rest of the lines install required packages for the environment.

Next place the bomcheckgui.py file in an empty folder (create any named folder you want).  Now in that folder activate the environment:

```
$ conda activate pyinst
```
Then run pyinstaller:
```
$ pyinstaller bomcheckgui.py
```
The program will take a few minutes to run.  After completion, when you dig around in the folders that have been created you'll find a folder named dist.  dist means distribution.  This folder and the contents thereof are all that is needed on the Windows machines that you want bomcheck to run on.  Under the dist folder is a folder named bomcheck.  And in this bomcheck folder is bomcheck.exe.
