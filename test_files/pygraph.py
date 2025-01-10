########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
from random import randint

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.init_status_figure()
        self.update_status_figure()
        
    def init_status_figure(self):

        
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.status_x = list(range(100))  # 100 time points
        self.status_y = [randint(0,100) for _ in range(100)]  # 100 data points

        self.graphWidget.setBackground('w')

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line =  self.graphWidget.plot(self.status_x, self.status_y, pen=pen)
    #
    # def status_fig_window(self):
    #     trendGroupBox = QGroupBox("")   
    #     childWindow.setObjectName("")
    #     childWindow.setWindowTitle("Online data monitoring for ADC channel %s" % str(subindex))
    #     childWindow.resize(600, 300)  # w*h
    #     logframe = QFrame()
    #     logframe.setLineWidth(1)
    #     childWindow.setCentralWidget(logframe)
    #     self.trendLayout = QGridLayout()
    #     Fig = self.graphWidget
    #     self.trendLayout.addWidget(Fig, 0, 0)
    #     trendGroupBox.setLayout(self.trendLayout)
    #     logframe.setLayout(self.trendLayout) 
                            
    def update_status_figure(self):     
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_communication_status)
        self.timer.start()
        
    def update_communication_status(self):

        self.status_x = self.status_x[1:]  # Remove the first y element.
        self.status_x.append(self.status_x[-1] + 1)  # Add a new value 1 higher than the last.

        self.status_y = self.status_y[1:]  # Remove the first
        self.status_y.append( randint(0,100))  # Add a new random value.

        self.data_line.setData(self.status_x, self.status_y)  # Update the data.
        
app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec_())