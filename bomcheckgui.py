
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 19:47:41 2021

@author: ken
"""

import sys
import bomcheck
import webbrowser
import os.path

from PyQt5.QtCore import Qt #, QSize
from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QAction,
                             QStatusBar, QListWidget, QLabel, QCheckBox,
                             QDialog, QVBoxLayout, QDialogButtonBox, QHBoxLayout, 
                             QMessageBox, QLineEdit, QPushButton, QTextEdit)
from PyQt5.QtGui import QIcon, QKeySequence, QPainter, QFont, QColor, QPixmap
# import dbm
from configfn import *


__version__ = '1.7.6'
__author__ = 'Kenneth E. Carlton'
printStrs = []


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(QIcon('icons/bomcheck.png'))
        

        try:
            self.configdb = get_configfn()[0]        
            with open(self.configdb, 'r') as file:
                x = file.read()     
            self.dbdic = eval(x)
        except Exception as e:
            print("error1 in MainWindow", e)
            self.dbdic = {'udrop': '3*-025', 'uexceptions': '', 'ask': False, 
                          'overwrite': False, 'folder': '', 'file2save2': 'bomcheck'}
            self.configdb = ('', '')
            
        self.folder = self.dbdic.get('folder')
        
        file_menu = self.menuBar().addMenu('&File')
        help_menu = self.menuBar().addMenu('&Help')
        self.setWindowTitle('bomcheck')
        self.setMinimumSize(925, 300)
        
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        btn_ac_execute = QAction(QIcon('icons/bomcheck.png'), 'Execute', self)  
        btn_ac_execute.triggered.connect(self.execute)
        btn_ac_execute.setStatusTip('Do a bomcheck of the files listed in the drag-drop zone.')
        toolbar.addAction(btn_ac_execute)
        
        btn_ac_clear = QAction(QIcon('icons/clear.png'), 'Clear', self) 
        btn_ac_clear.triggered.connect(self.clear)
        btn_ac_clear.setStatusTip('Clear the drag-drop zone of data.')
        toolbar.addAction(btn_ac_clear)
        
        btn_ac_folder = QAction(QIcon('icons/folder.png'), "Open the folder", self) 
        btn_ac_folder.triggered.connect(self.openfolder)
        btn_ac_folder.setStatusTip('Open the the most recently active BOM folder.')
        toolbar.addAction(btn_ac_folder)
        
        empty_label1 = QLabel()
        empty_label1.setText('   ')
        toolbar.addWidget(empty_label1)

        self.drop_chkbox = QCheckBox('Activate the drop list')
        self.drop_chkbox.setChecked(False)
        self.drop_chkbox.setStatusTip('Ignore pt. nos of SW parts that are in the drop list.  See File>Settings.')
        toolbar.addWidget(self.drop_chkbox)
                
        execute_action = QAction(QIcon('icons/bomcheck.png'), 'Execute', self)
        execute_action.triggered.connect(self.execute)
        file_menu.addAction(execute_action)
        
        settings_action = QAction(QIcon('icons/settings.png'), 'Settings', self)
        settings_action.triggered.connect(self.settings)
        file_menu.addAction(settings_action)
        
        quit_action = QAction(QIcon('icons/quit.png'), '&Quit', self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        help_action = QAction(QIcon('icons/question-mark.png'), '&Help', self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self._help)
        help_menu.addAction(help_action)
        
        about_action = QAction(QIcon('icons/about.png'), '&About', self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)
        
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.lstbox_view = ListboxWidget(self)
        self.lstbox_view.setWordWrap(True)
        self.setCentralWidget(self.lstbox_view)
        
    def openfolder(self):
        ''' Open the folder determined by variable "self.folder"'''
                
        err = False
        try:   # get BOM folder name from 1st item in drag/drop list
            self.folder = os.path.dirname(self.lstbox_view.item(0).text())
            with open(self.configdb, 'r+') as file:
                x = file.read() 
                self.dbdic = eval(x)
                self.dbdic['folder'] = self.folder
                file.seek(0)
                file.write(str(self.dbdic))
                file.truncate()
            self.folder = self.dbdic['folder']
            os.system(cmdtxt(self.folder))
        except Exception as e:  # it an error occured, moset likely and AttributeError
            print("error2 at MainWindow/openfolder", e)
            print("error2 at MainWindow/openfolder... possibly due to no data in drag&drop zone")
            err = True
            
        if err:    
            try: 
                with open(self.configdb, 'r') as file:
                    x = file.read()     
                    self.dbdic = eval(x)
                self.folder = self.dbdic.get('folder', '')
                if self.folder:
                    os.system(cmdtxt(self.folder))
                else:
                    msg = ('Drag in some files first.  Thereafter\n'
                       'clicking the folder icon will open the\n'
                       'folder where BOMs are located.')
                    msgtitle = 'Folder location not set'
                    message(msg, msgtitle, msgtype='Information')
            except Exception as e:  # it an error occured, moset likely and AttributeError
                print("error3 at MainWindow/openfolder", e)
            
    def execute(self):
        global printStrs, standardflow
        
        try: 
            with open(self.configdb, 'r+') as file:   
                x = file.read()
                self.dbdic = eval(x)
                try:
                    self.folder = os.path.dirname(self.lstbox_view.item(0).text())
                    self.dbdic['folder'] = self.folder
                    file.seek(0)
                    file.write(str(self.dbdic))
                    file.truncate()
                except Exception as e:  # it an error occured, moset likely and AttributeError
                    print("error4 at MainWindow/execute", e)
        except Exception as e:  # it an error occured, moset likely and AttributeError
            print("error5 at MainWindow/execute", e)
 
        ask = self.dbdic.get('ask', False)
        defaultfname = self.getdefaultfname()
        if ask:
            standardflow = False
            # AskDialog sets standardflow, a global variable, to True if user hits its the OK button
            dlg = AskDialog(defaultfname)  # call up the dialog box to add a new record.
            dlg.exec_()
            try: 
                with open(self.configdb, 'r') as file:
                    x = file.read()     
                    self.dbdic = eval(x)
            except Exception as e:  # it an error occured, moset likely and AttributeError
                print("error10 at MainWindow/execute", e) 
        else:
            standardflow = True
            try:
                with open(self.configdb, 'r+') as file:
                    x = file.read()     
                    self.dbdic = eval(x)
                    self.dbdic['file2save2'] = defaultfname
                    file.seek(0)
                    file.write(str(self.dbdic))
                    file.truncate()
            except Exception as e:  # it an error occured, moset likely and AttributeError
                print("error6 at MainWindow/execute", e)
        
        self.createdfile = ''
        files = []
        n = self.lstbox_view.count()
        for i in range(n):
            files.append(self.lstbox_view.item(i).text())
        
        if standardflow == True:   
            msg = bomcheck.bomcheck(files, d=self.drop_chkbox.isChecked(), dbdic = self.dbdic)
        else:
            msg = []         
            
        createdfile = 'Created file: unknown'
        for x in msg:
            if 'Created file:' in x and len(x) > 4:
                k = x.strip('\n')
                if '/' in k:
                    lst = k.split('/')
                    createdfile = 'Created file: .../' + '/'.join(lst[-3:])
                elif '\\' in k:
                    lst = k.split('\\')
                    createdfile = 'Created file: ...\\' + '\\'.join(lst[-3:])
            elif 'Created file:' in x:
                createdfile = x
                
        if len(msg) == 1 and  'Created file:' in msg[0]:
            del msg[0]
        
        self.statusbar.showMessage(createdfile, 1000000) 
        if msg:
            msgtitle = 'bomcheck discrepancy warning'
            message(''.join(msg), msgtitle)
            
    def clear(self):
        self.lstbox_view.clear()
    
    def _help(self):
        webbrowser.open('bomcheckgui_help.html')
     
    def about(self):
        dlg = AboutDialog()
        dlg.exec_()
        
    def settings(self):
        dlg = SettingsDialog()
        dlg.exec_()
    
    def getdefaultfname(self):
        '''Look at the list of filenames that have been dropped.  From that 
        list look for a name that ends with '_sl.xlsx', and extract a potential
        name to assign to the bomcheck output file.  E.g. from 093345_sl.xlsx, 
        present to the user: 093345_bomcheck.  If no filename found ending
        with _sl.xlsx, or if more than one such file, then present the name:
        bomcheck.

        Returns
        -------
        defaultFname: str
            default filename for the output xlsx file that bomcheck creates. 
        '''
        j = 0
        files = []
        found = None
        n = self.lstbox_view.count()
        for i in range(n):
            files.append(self.lstbox_view.item(i).text())
        for f in files:
            if '_sl.xls' in f.lower():
                found = os.path.splitext(os.path.basename(f))[0]  # name sripped of path and extension
                found = found[:-3]  # take the _sl characters off the end
                j += 1
        if found and j == 1:
            defaultFname = found + '_bomcheck'
        else:
            defaultFname = 'bomcheck'
        return defaultFname
        
    
class AskDialog(QDialog):
    ''' A dialog box asking the user what the output filename should be.
    '''        
    def __init__(self, default):
        super(AskDialog, self).__init__()
         
        global standardflow
        standardflow = False  # Assumes that the user won't hit the OK button
        
        self.setWindowTitle('Filename for results?')
        self.setFixedWidth(350)
        self.setFixedHeight(150)

        layout = QVBoxLayout()

        self.fnameinput = QLineEdit()
        self.fnameinput.setPlaceholderText('Filename for the bomcheck file')
        self.fnameinput.setMaxLength(40)
        self.fnameinput.setText(default)
        layout.addWidget(self.fnameinput)
        
        self.QBtn = QPushButton('text-align:center')
        self.QBtn.setText("OK")
        self.QBtn.setMaximumWidth(75)
        self.QBtn.clicked.connect(self.fname)
    
        hbox = QHBoxLayout()
        hbox.addWidget(self.QBtn)
        layout.addLayout(hbox)
        self.setLayout(layout)

    def fname(self):
        global standardflow
        
        askfname = self.fnameinput.text()
        if askfname.strip() == '':
            askfname = 'bomcheck'
        askfname = os.path.splitext(os.path.basename(askfname))[0]
        
        configdb = get_configfn()[0] 
        try:
            with open(configdb, 'r+') as file:
                x = file.read()     
                self.dbdic = eval(x)
                self.dbdic['file2save2'] = askfname
                file.seek(0)
                file.write(str(self.dbdic))
                file.truncate()
        except Exception as e:  # if an error occured, moset likely and AttributeError
            print("error7 at AskDialog", e)
        standardflow = True
        self.close()
        
           
class SettingsDialog(QDialog):
    ''' A dialog box asking the user what the settings he would like to make.
    '''
        
    def __init__(self):
        super(SettingsDialog, self).__init__()

        self.setWindowTitle('Settings')
        self.setFixedWidth(350)
        self.setFixedHeight(350)  # was 150

        layout = QVBoxLayout()
        
        self.configdb = ''
        try:
            self.configdb = get_configfn()[0]
            with open(self.configdb, 'r') as file: # Use file to refer to the file object
                x = file.read()
            self.dbdic = eval(x) 
        except Exception as e:  # it an error occured, moset likely and AttributeError
            print("error8 at SettingsDialog", e)
            
        self.ask_chkbox = QCheckBox('Ask what name the bomcheck file should be.')
        _bool = self.dbdic.get('ask', False)
        self.ask_chkbox.setChecked(_bool)
        layout.addWidget(self.ask_chkbox)
        
        self.overwrite_chkbox = QCheckBox('Allow overwrite of existing bomcheck file.')
        _bool = self.dbdic.get('overwrite', False)
        self.overwrite_chkbox.setChecked(_bool)
        layout.addWidget(self.overwrite_chkbox)

        drop_label = QLabel()
        drop_label.setText('drop list (Ignore these pt. nos. shown in SW BOMs):')
        layout.addWidget(drop_label)
        
        self.drop_input = QTextEdit()
        self.drop_input.setPlaceholderText('Separate pt. nos. with commas and/or spaces.  Letters are case sensitive')
        if 'udrop' in self.dbdic:
            self.drop_input.setPlainText(self.dbdic.get('udrop', ''))
        layout.addWidget(self.drop_input)
        
        exceptions_label = QLabel()
        exceptions_label.setText('exceptions list (exceptions to pt. nos. in the drop list):')
        layout.addWidget(exceptions_label)
        
        self.exceptions_input = QTextEdit()
        self.exceptions_input.setPlaceholderText('Separate pt. nos. with commas and/or spaces.  Letters are case sensitive.')
        if 'uexceptions' in self.dbdic:
            self.exceptions_input.setPlainText(self.dbdic.get('uexceptions', ''))
        layout.addWidget(self.exceptions_input)
        
        self.QBtnOK = QPushButton('text-align:center')
        self.QBtnOK.setText("OK")
        self.QBtnOK.setMaximumWidth(75)
        self.QBtnOK.clicked.connect(self._done)
        
        self.QBtnCancel = QPushButton('text-align:center')
        self.QBtnCancel.setText("Cancel")
        self.QBtnCancel.setMaximumWidth(75)
        self.QBtnCancel.clicked.connect(self.cancel)

        hbox = QHBoxLayout()
        hbox.addWidget(self.QBtnOK)
        hbox.addWidget(self.QBtnCancel)
        layout.addLayout(hbox)
        self.setLayout(layout)

    def _done(self):
        try:
            with open(self.configdb, "r+") as file:
                x = file.read()    
                self.dbdic = eval(x)    
                if self.ask_chkbox.isChecked():
                    self.dbdic['ask'] = True
                else:
                    self.dbdic['ask'] = False
                if self.overwrite_chkbox.isChecked(): 
                    self.dbdic['overwrite'] = True
                else:
                    self.dbdic['overwrite'] = False 
                drp = self.drop_input.toPlainText()
                self.dbdic['udrop'] = drp
                excep = self.exceptions_input.toPlainText()
                self.dbdic['uexceptions'] = excep
                file.seek(0)
                file.write(str(self.dbdic))
                file.truncate()
        except Exception as e:  # it an error occured, moset likely and AttributeError
            msg =  "error9 at SettingsDialog.  " + str(e)
            print(msg)
            message(msg, 'Error', msgtype='Warning', showButtons=False)
        self.close()
        
    def cancel(self):
        self.close()
                

class AboutDialog(QDialog):
    ''' Show company name, logo, program author, program creation date
    '''
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)

        self.setFixedHeight(320)
        
        QBtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()

        self.setWindowTitle('About')

        labelpic = QLabel()
        pixmap = QPixmap('icons/DekkerLogo.png')
        labelpic.setPixmap(pixmap)
        labelpic.setFixedHeight(150)

        layout.addWidget(labelpic)
        layout.addWidget(QLabel('bomcheckgui version: ' + __version__ + '\n' +
                                'A program to commpare BOMs from SolidWorks to\n' +
                                'to those in the SiteLine database.  Written for\n' +
                                'Dekker Vacuum Technologies, Inc.\n\n' +
                                'Written by Ken Carlton, January 27, 2021'))
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)       
        
        
class ListboxWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._placeholder_text = "Drag & Drop"
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        #global folder
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            links = []            
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    links.append(str(url.toLocalFile()))
                else:
                    links.append(str(url.toString()))
                    
            self.addItems(links)

        else:
            event.ignore()
    
    # https://stackoverflow.com/questions/60076333/how-to-set-the-placeholder-text-in-the-center-when-the-qlistwidget-is-empty            
    @property
    def placeholder_text(self):
        return self._placeholder_text

    @placeholder_text.setter
    def placeholder_text(self, text):
        self._placeholder_text = text
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(192, 192, 192))
            painter.setFont(QFont('Decorative', 20, QFont.Bold))
            painter.save()
            fm = self.fontMetrics()
            elided_text = fm.elidedText(
                self.placeholder_text, Qt.ElideRight, self.viewport().width()
            )
            painter.drawText(self.viewport().rect(), Qt.AlignCenter, elided_text)
            painter.restore()  
            
            
def cmdtxt(foldr):
    ''' Create a dirpath name based on a URI type scheme.  Put in front of
    it the command that will be capable of opening it in file manager program.  
    
    e.g. in Windows: 
        exlorer file:///C:/SW_Vault/CAD%20Documents/PRODUCTION%20SYSTEMS
        
    e.g. on my Ubuntu Linux system:
        thunar file:///home/ken/tmp/bom%20files
        
    Where %20 is equivalent to a space character.
    referece: https://en.wikipedia.org/wiki/File_URI_scheme
    '''
    if sys.platform[:3] == 'win':
        foldr = foldr.replace(' ', '%20')
        command = 'explorer file:///' + foldr
    elif sys.platform[:3] == 'lin':
        homedir = os.path.expanduser('~')
        foldr = os.path.join(homedir, foldr)
        foldr = foldr.replace(' ', '%20')
        command = 'thunar file:///' + foldr  # thunar is the name of a file manager
    return command


def message(msg, msgtitle, msgtype='Warning', showButtons=False):
    '''
    UI message to show to the user

    Parameters
    ----------
    msg: str
        Message presented to the user.
    msgtitle: str
        Title of the message.
    msgtype: str, optional
        Type of message.  Currenly only valid input is 'Warning'.
        The default is 'Warning'.
    showButtons: bool, optional
        If True, show OK and Cancel buttons. The default is False.

    Returns
    -------
    retval: QMessageBox.StandardButton
        "OK" or "Cancel" is returned
    '''
    msgbox = QMessageBox()
    if msgtype == 'Warning':
        msgbox.setIcon(QMessageBox.Warning)
    elif msgtype == 'Information':
        msgbox.setIcon(QMessageBox.Information)
    msgbox.setWindowTitle(msgtitle)
    msgbox.setText(msg)
    if showButtons:
        msgbox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    retval = msgbox.exec_()
    return retval

        
            
app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec_())
