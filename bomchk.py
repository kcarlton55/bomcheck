#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 21:18:58 2019

@author: ken

"""

import sys
from PyQt5.QtWidgets import (QMainWindow, QAction, qApp, QApplication,
                             QDesktopWidget)
from PyQt5.QtGui import QIcon


class Bomchk(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(250, 150)
        self.center()
        self.setWindowTitle('bomcheck')
        self.setWindowIcon(QIcon('icons/dekker.ico'))
        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        
        exitAct = QAction(QIcon('icons/exit.png'), '&Exit', self)        
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        
        #self.statusBar()
        

        helpMenu = menubar.addMenu('&Help')
        

  
        self.show() 

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    bc = Bomchk()
    sys.exit(app.exec_())
        