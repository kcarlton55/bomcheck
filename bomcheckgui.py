#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 19:47:41 2021

@author: ken
"""

import sys
import bomcheck
import webbrowser

from PyQt5.QtCore import Qt #, QSize
from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QAction,
                             QStatusBar, QListWidget, QLabel, QRadioButton,
                             QDialog, QVBoxLayout, QDialogButtonBox, QMessageBox)
from PyQt5.QtGui import QIcon, QKeySequence, QPainter, QFont, QColor, QPixmap


__version__ = '1.7.5'
__author__ = 'Kenneth E. Carlton'
printStrs = []


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(QIcon('icons/bomcheck.png'))

        file_menu = self.menuBar().addMenu('&File')
        help_menu = self.menuBar().addMenu('&Help')
        self.setWindowTitle('bomcheck')
        self.setMinimumSize(850, 600)
        
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        btn_ac_execute = QAction(QIcon('icons/bomcheck.png'), 'Execute', self)  
        btn_ac_execute.triggered.connect(self.execute)
        btn_ac_execute.setStatusTip('Execute')
        toolbar.addAction(btn_ac_execute)
        
        btn_ac_clear = QAction(QIcon('icons/clear.png'), 'Clear', self) 
        btn_ac_clear.triggered.connect(self.clear)
        btn_ac_clear.setStatusTip('Clear')
        toolbar.addAction(btn_ac_clear)
        
        empty_label1 = QLabel()
        empty_label1.setText('   ')
        toolbar.addWidget(empty_label1)

        self.drop_button = QRadioButton('ignore 3*-025 SW parts')
        self.drop_button.setChecked(False)
        self.drop_button.setStatusTip("ignore 3*-025 parts from SW BOMs")
        toolbar.addWidget(self.drop_button)
        
        execute_action = QAction(QIcon('icons/bomcheck.png'), 'Execute', self)
        execute_action.triggered.connect(self.execute)
        file_menu.addAction(execute_action)
        
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
        
    def execute(self):
        global printStrs
        self.createdfile = ''
        files = []
        n = self.lstbox_view.count()
        for i in range(n):
            files.append(self.lstbox_view.item(i).text())
        msg = bomcheck.bomcheck(files, d=self.drop_button.isChecked())
        
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
            self.message(''.join(msg), msgtitle)
            
    def clear(self):
        self.lstbox_view.clear()
    
    def _help(self):
        webbrowser.open('bomcheckgui_help.html')
     
    def about(self):
        dlg = AboutDialog()
        dlg.exec_()
        
    def message(self, msg, msgtitle, msgtype='Warning', showButtons=False):
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
        msgbox.setWindowTitle(msgtitle)
        msgbox.setText(msg)
        if showButtons:
            msgbox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msgbox.exec_()
        return retval
        
        
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
        layout.addWidget(QLabel('bomcheckgui, version ' + __version__ + '\n\n' +
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
        
        
        
        
app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec_())
