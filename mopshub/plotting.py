from __future__ import division
import numpy as np
from numpy import loadtxt, arange
import csv
from scipy.optimize import curve_fit
import tables as tb
from mpl_toolkits.mplot3d import Axes3D
import itertools
from math import pi, cos, sin
from scipy.linalg import norm
import os
import seaborn as sns
from matplotlib.pyplot import *
import pylab as P
import pandas as pd
import matplotlib as mpl
import matplotlib.ticker as ticker
import matplotlib.transforms as mtransforms
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import gridspec
from matplotlib.colors import LogNorm
from matplotlib.patches import Circle
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredDrawingArea
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
from matplotlib.ticker import NullFormatter
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from .analysis_utils      import AnalysisUtils
import matplotlib.image as image
from scipy import interpolate
from .logger_main   import Logger
from .plot_style import *
import logging
from collections import Counter
import seaborn as sns
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="Plotting", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()#

class Plotting(object): 

    def __init__(self):
        pass
    
    def calculate_dose(self, period):
        """
        Calculate the dose for each period based on the dose rate.
        
        Parameters:
            periods (array-like): Array of time periods.
            dose_rate (float): Dose rate in gray per hour.
        
        Returns:
            array: Array containing the dose for each period.
        """
        dose_rate = 2 #gy/hr
        return [h * dose_rate for h in period]
    
    def plot_histogram(self,xValues =  None, zValues = None, xlabel="Value", ylabel="Frequency", title="Histogram", bins=10, file_out=None, PdfPages=None):
        
        
        xValues = np.array(xValues)
        # Calculate the differences
        #xValues = np.diff(xValues)
        cmap = plt.cm.get_cmap('viridis')   # Choose a colormap          

        fig1, ax1 = plt.subplots()
        #get the dose              
        #zValues = self.calculate_dose(zValues)

                
        start_index = 0
        max_voltage = max(xValues)
        min_voltage = min(xValues)
        ctick_size = (max_voltage - min_voltage) / (bins)  
        plot_range = np.round(np.arange(min_voltage, max_voltage, ctick_size),3)
        tick_size = 1
        hist, bin_edges = np.histogram(xValues, bins=plot_range)
        bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2
        p0 = (np.amax(hist), np.nanmean(bin_edges), np.std(bin_edges))
        def _gauss(x, *p):
            amplitude, mu, sigma = p
            return amplitude * np.exp(- (x - mu)**2.0 / (2.0 * sigma**2.0))
        coeff = None
        try:
            coeff, _ = curve_fit(_gauss, bin_centres, hist, p0=p0)
            points = np.linspace(min(bin_edges[:]), max(bin_edges[:]), bins)
            gau = _gauss(points, *coeff)
        except: 
            pass
        
        if coeff is not None:
            ax1.bar(np.arange(0,len(hist)), hist,width=tick_size)
            ax1.set_xlabel(xlabel)
            ax1.set_ylabel(ylabel)
            ax1.set_title(title)
            #ax.set_xlim(min(xValues)-0.2, max(xValues)+0.2)  # Set x-axis range from 3 to 6
            ax1.set_xticks(np.arange(0,len(bin_edges)))
            ax1.set_xticklabels(bin_edges, rotation = 90)

            ax1.plot(np.arange(0,len(hist)+1), gau, "r-", label='Normal distribution')
            ax1.grid(True)
            fig1.savefig(file_out[:-4]+"_gaus.pdf", bbox_inches='tight')  
                    
        fig2, ax2 = plt.subplots()
        consecutive_array, repeats, zValues = AnalysisUtils().count_consecutive_repeats(zValues)
        voltage_frequency = Counter(xValues)
        volt_dict = dict(voltage_frequency)
        hist_volt = {}
        replaced_volt_dict = {}
        
        for element, frequency in volt_dict.items(): replaced_volt_dict[element] = [zValues[i]*2 for i, x in enumerate(xValues) if x == element]
        for volt, frequency in volt_dict.items(): 
            hist_volt[volt], _ = np.histogram(replaced_volt_dict[volt], bins=bins)
        norm = Normalize(vmin=min(replaced_volt_dict.keys()), vmax=max(replaced_volt_dict.keys()))    
       
        for dose, histogram in hist_volt.items(): 
            hist, bin_edges = np.histogram(hist_volt[dose], bins=plot_range)           
            color = cmap(norm(dose))
            ax2.bar(np.arange(0,len(histogram)), histogram, color=color,width=tick_size)#, edgecolor='black')                    
        
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm)
        cbar.set_label('Dose [Gy]')       

        ax2.set_xlabel(xlabel)
        ax2.set_ylabel(ylabel)
        ax2.set_title(title)
        #ax.set_xlim(min(xValues)-0.2, max(xValues)+0.2)  # Set x-axis range from 3 to 6
        ax2.grid(True)
        fig2.savefig(file_out[:-4]+"_volt.pdf", bbox_inches='tight')  
        if PdfPages:
            PdfPages.savefig()
            
     
        fig, ax = plt.subplots()  
        hist_dose = {}
        dose_frequency = Counter(zValues)
        dose_dict = dict(dose_frequency)

        # Initialize an empty list to store the reconstructed array
        #replaced_dict = {}
        replaced_dose_dict = {}
        # Iterate over the items in the frequency dictionary
        #dose_bar = {}
        # for element, frequency in dose_dict.items():
        #     # Replace the element with the corresponding element from the replacement array
        #     replaced_dict[consecutive_array[element]] = frequency

        for time, frequency in dose_dict.items():
            dose = time*2 
            replaced_dose_dict[dose] = list(xValues[start_index:start_index + frequency])
            # Update the start index for the next iteration
            start_index += frequency  
            hist_dose[dose], _ = np.histogram(replaced_dose_dict[dose], bins=bins)


                    
        norm = Normalize(vmin=min(replaced_dose_dict.keys()), vmax=max(replaced_dose_dict.keys()))    
        for dose, histogram in hist_dose.items(): 
            hist, bin_edges = np.histogram(replaced_dose_dict[dose], bins=plot_range)           
            color = cmap(norm(dose))
            ax.bar(np.arange(0,len(histogram)), histogram, color=color,width=tick_size)#, edgecolor='black')
            
        ax.set_xticks(np.arange(0,len(plot_range)))
        ax.set_xticklabels(plot_range, rotation = 90)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm)
        cbar.set_label('Dose [Gy]')       

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        #ax.set_xlim(min(xValues)-0.2, max(xValues)+0.2)  # Set x-axis range from 3 to 6
        ax.grid(True)
        fig.savefig(file_out[:-4]+"_dose.pdf", bbox_inches='tight')  
        if PdfPages:
            PdfPages.savefig()
    
        return fig, ax

    def plot_data(self,plot = None , xValues = None, yValues = None, eyValues = [0], xLabel = None, yLabel = None,
                    ymax = None, ymin= None, modules_name= ["vorTID"], 
                    yValues2 = None, yLabel2 = None,title = None, posX = None, 
                    posY = None,steps = None,file_out = None,  min_scale = None,  PdfPages = None):
        
        if plot: plot = plot
        else: plot =  plt
        yMin = [0 for i in range(len(yValues))]
        yMax = [0 for i in range(len(yValues))]
        legend_handles = []
        fig, ax = plot.subplots()
        #ax = plot.subplot(posX, 1, posY)
        #fig = plot.gcf()
        ax.set_title(title)
        
        for number, value in enumerate(yValues):
            yMin[number] = min((y for y in value if y is not None),key=lambda x:float(x))
            yMax[number] = max((y for y in value if y is not None),key=lambda x:float(x))
            
            #ax.errorbar(xValues, value, xerr=0.0, yerr=0.0, fmt='o', color='black')  # plot points
            axis_1 = ax.plot(xValues,value,'.-', label = yLabel[number+1])            
            if modules_name[0] == "waehrendTID":
                pass
                # cmap = plt.cm.get_cmap('viridis', 15)               
                # sc = ax.scatter(xValues, value, c=self.calculate_dose(period = xValues), cmap=cmap, s=10)
                # cbar = fig.colorbar(sc, ax=ax, orientation='vertical')
                # cbar.set_label("Dose [Gray]", labelpad=1)                  
                #ax.errorbar(xValues, value, yerr=eyvalues, fmt='o', color = 'black', markerfacecolor='black', markeredgecolor="black")
            legend_handles.append(Line2D([], [], label=yLabel[number + 1]))
            ax.set_ylabel(yLabel[0], rotation=90)
            ax.set_xlabel(xLabel)                
        if ymax:
            #ax.set_yticks(np.arange(ymin, ymax,steps)) 
            ax.set_ylim([ymin, ymax])
        else: 
            #ax.set_yticks(np.arange(min(yMin)-0.05, max(yMax)+0.05,steps)) 
            pass
        if min_scale == "min_scale":  tick_positions = np.arange(0,62,2)
        else: tick_positions = np.arange(0,max(xValues)+2,3)  
        
        if yValues2:
            ax2 = ax.twinx()
            yMin2 = [0 for i in range(len(yValues2))]
            yMax2 = [0 for i in range(len(yValues2))]
            for number, value in enumerate(yValues2):
                yMin2[number] = min((y for y in value if y is not None),key=lambda x:float(x))
                yMax2[number] = max((y for y in value if y is not None),key=lambda x:float(x))
                
                axis_2 = ax2.plot(xValues, value, '-', color=col_row[5], label = yLabel2[number+1])
                legend_handles.append(Line2D([], [], color=col_row[5], label=yLabel2[number + 1]))
                ax2.set_ylabel(yLabel2[0], rotation=90, color=col_row[5]) 
                ax.spines['right'].set_position(('outward', 3))  # adjust the position of the second axis      
                ax2.set_xticks(tick_positions) 
            if ymax:   
                ax2.set_ylim([1.53, 1.55]) 
        ax.set_xticks(tick_positions) 
        if modules_name[0] == "waehrendTID":
            ax1 = ax.twiny()
            ax1.set_xlim(ax.get_xlim())
            # Set the tick positions and labels on both axes to align them
            #tick_positions = np.arange(len(xValues))     
            ax1.set_xticks(tick_positions)
            does_array = self.calculate_dose(period = ax.get_xticks())
            ax1.set_xticklabels(does_array, rotation=90, ha='right')
            #ax1.spines['bottom'].set_position(('outward', 20))  # Adjust the distance as needed
            ax1.set_xlabel("Dose [Gray]")
          
            
        plot.legend(handles=legend_handles, loc='upper left')
        ax.grid(True)
        #plt.xticks(rotation=45, ha='right')
        plot.tight_layout()
        fig.savefig(file_out, bbox_inches='tight')  
        #plot.tight_layout()
        PdfPages.savefig()
        plot.clf() 
        plot.close(fig)  
        return fig, ax

    def plot_ramps(self, root_dir = None, module_name="LTM8067EY-PBF", component_name="rampup", text_enable=True, PdfPages = None):
        file_in_path = root_dir+ "dc_converters/" + module_name +"/" +  component_name + "/"+module_name
        file_out_path = root_dir+ "dc_converters/" + module_name +"/" +  component_name + "/"+module_name
        fig, ax = plt.subplots()
        logger.info(f"Plotting {module_name} {component_name} Data")
        # Read the CSV file into a DataFrame, skipping the header row
        df = pd.read_csv(file_in_path+"_Rampup_results.csv", skiprows=1, header=None)
        # Extract the required columns from the DataFrame
        Usin1   = df.iloc[:, 0].astype(float)
        Tin     = df.iloc[:, 1].astype(float)
        Tout    = df.iloc[:, 2].astype(float)
    
        if text_enable: ax.set_title('Time signals at different ramp-up speeds [' + module_name + ']')
    
        ax.plot(Usin1, Tin,  label="Time of Input [$T_{in}$]")
        ax.plot(Usin1, Tout, label="Time of Output [T$_{out}$]")
            
        ax.errorbar(Usin1, Tin, yerr=0.05*Tin, fmt='D', color = 'black', markerfacecolor='black', markeredgecolor="black")
        ax.errorbar(Usin1, Tout, yerr=0.05*Tout, fmt='o', color = 'black', markerfacecolor='black', markeredgecolor="black")
        
        ax.grid(True)
        plt.xscale('log')
        ax.set_xlabel("Ramp up Voltage rate [V/s]")
        ax.legend(loc="upper right")
        ax.set_ylabel(r'Time [ms]')
        plt.tight_layout()
        plt.savefig(file_out_path +"_Rampup_results.pdf", bbox_inches='tight')
        ax.set_title('Time signals at different ramp-up speeds [' + module_name + ']')
        plt.tight_layout()
        PdfPages.savefig()
        plt.clf() 
        plt.close(fig)
    
    def close(self, PdfPages=False):
            PdfPages.close()