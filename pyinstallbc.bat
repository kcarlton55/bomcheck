:: A batch file to create bomcheckgui.exe from bomcheckgui.py.
:: With Python active and with modules listed in requirements.txt working in
:: a virtual environment, change directory to where you want new files created
:: and run this batch file.

pyinstaller C:\Users\Ken\Documents\shared\projects\project1\bomcheckgui.py -w --icon=C:\Users\Ken\Documents\shared\projects\project1\icons\bomcheck.ico

mkdir dist\bomcheckgui\icons
copy C:\Users\Ken\Documents\shared\projects\project1\icons dist\bomcheckgui\icons

mkdir dist\bomcheckgui\help_files
copy C:\Users\Ken\Documents\shared\projects\project1\help_files dist\bomcheckgui\help_files

mkdir dist\bomcheckgui\sourcefiles
copy C:\Users\Ken\Documents\shared\projects\project1\* dist\bomcheckgui\sourcefiles

copy C:\Users\Ken\Documents\shared\projects\project1\bc_config\bc_config.py dist\bomcheckgui\

mkdir dist\bomcheckgui\sourcefiles\bc_config
copy C:\Users\Ken\Documents\shared\projects\project1\bc_config dist\bomcheckgui\sourcefiles\bc_config


