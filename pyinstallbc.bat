pyinstaller C:\Users\Ken\Documents\shared\projects\project1\bomcheckgui.py -w  --icon=C:\Users\Ken\Documents\shared\projects\project1\icons\bomcheck.ico
mkdir dist\bomcheckgui\icons
copy C:\Users\Ken\Documents\shared\projects\project1\icons dist\bomcheckgui\icons
copy C:\Users\Ken\Documents\shared\projects\project1\bomcheckgui_help.html dist\bomcheckgui
mkdir dist\bomcheckgui\sourcefiles
copy C:\Users\Ken\Documents\shared\projects\project1\* dist\bomcheckgui\sourcefiles