########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
# -*- coding: utf-8 -*-
import sys
from matplotlib.backends.qt_compat import  QtWidgets
from mopshubGUI import  mopshub_child_window

qApp =None

def main():
    global qApp
    qApp = QtWidgets.QApplication(sys.argv)
    app_widget = mopshub_child_window.mopshubWindow()
    app_widget.Ui_ApplicationWindow()
    qApp.exec_()

if __name__ == '__main__':
    main()