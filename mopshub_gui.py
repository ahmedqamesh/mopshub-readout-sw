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