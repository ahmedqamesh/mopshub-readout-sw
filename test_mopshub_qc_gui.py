########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 29.08.2023
"""
########################################################
# -*- coding: utf-8 -*-
import sys
from matplotlib.backends.qt_compat import  QtWidgets
from PyQt5.QtWidgets import QApplication
from mopshubGUI import  mopshub_child_window
from mopshubGUI import  mopshub_qc_gui
qApp =None

def main():
    app = QApplication(sys.argv)
    window = mopshub_qc_gui.TestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()