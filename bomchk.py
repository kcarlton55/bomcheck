#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 21:18:58 2019

@author: ken

"""

import sys
from PyQt5.QtWidgets import (QMainWindow, QAction, qApp, QApplication,
                             QDesktopWidget, QCheckBox, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap


class Bomchk(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        global useDrop
        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('Dekker BOM Check')
        self.setWindowIcon(QIcon('icons/dekker.ico'))

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAct = QAction(QIcon('icons/exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)

        cb = QCheckBox('Use Drop', self)
        cb.move(10, 30)
        cb.stateChanged.connect(self.changeUseDrop)

        label = QLabel(self)
        pixmap = QPixmap('icons/dragndrop.png') #https://pythonspot.com/pyqt5-image/
        label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())




        #helpMenu = menubar.addMenu('&Help')
        #self.setAcceptDrops(True)

        self.statusBar()
        self.show()

    def changeUseDrop(self, state):
        if state == Qt.Checked:
            useDrop = True
        else:
            useDrop = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    bc = Bomchk()
    sys.exit(app.exec_())
