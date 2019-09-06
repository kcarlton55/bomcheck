#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 21:18:58 2019

@author: ken

"""



import sys
#from PySide2.QtCore import Qt
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QLabel,
                             QMainWindow, QPushButton)
from PyQt5.QtGui import QIcon, QPixmap


#from PySide2.QtWidgets import (QWidget, QMainWindow, QAction, qApp, QApplication,
#                             QDesktopWidget, QCheckBox, QLabel, QVBoxLayout,
#                             QHBoxLayout, QPushButton, QLineEdit)
#from PySide2.QtCore import Qt
#from PySide2.QtGui import QIcon, QPixmap


class Dropbox(QLabel):
    def __init__(self):
        super().__init__()
        pixmap = QPixmap('icons/dragndrop.png') #https://pythonspot.com/pyqt5-image/
        self.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            print(f)


class Bomchk(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        global useDrop
        #self.setDragEnabled(True)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAct = QAction(QIcon('icons/exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)

        runButton = QPushButton("Run", self)
        runButton.clicked.connect(self.runBomcheck)
        runButton.move(15, 25)

        chkBox = QCheckBox('Use Drop', self)
        chkBox.stateChanged.connect(self.changeUseDrop)
        chkBox.move(150,25)

        #dragAndDrop = QLabel(self)
        #pixmap = QPixmap('icons/dragndrop.png') #https://pythonspot.com/pyqt5-image/
        #dragAndDrop.setPixmap(pixmap)
        #dragAndDrop.resize(pixmap.width(), pixmap.height())
        #dragAndDrop.move(15, 65)
        #dragAndDrop.setAcceptDrops(True)

        dragAndDrop = Dropbox()
        dragAndDrop.move(15, 65)

        #helpMenu = menubar.addMenu('&Help')
        #self.setAcceptDrops(True)

        self.setGeometry(300, 300, 345, 235)
        self.setWindowTitle('Dekker BOM Check')
        self.setWindowIcon(QIcon('icons/dekker.ico'))

        #self.statusBar()
        #self.show()

    def changeUseDrop(self, state):
        if state == Qt.Checked:
            useDrop = True
        else:
            useDrop = False



    def runBomcheck(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    bc = Bomchk()
    bc.show
    app.exec_()
