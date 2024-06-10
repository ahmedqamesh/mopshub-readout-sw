import sys
import os
from validators import length
import seaborn as sns
import numpy as np
from matplotlib import gridspec
import matplotlib.cbook as cbook
import matplotlib.image as image
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from logger_main   import Logger
import logging
import pandas as pd
import csv
from plot_style import *
import matplotlib
from celluloid import Camera
from scipy import interpolate
import math
import re
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="Debug data", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()
config_dir = rootdir+"/config_files/"
output_dir = rootdir+"/output_dir/"
data_dir = rootdir+"/data_files/"

path = os.path.abspath('') + '/'
logger.info('current working path: '+path)


def plot_debug_time(PdfPages=None, file_names=[], text_enable=False, xlim =500,output_dir = None):
    data_frames = [pd.read_csv(file_name, skiprows=[1]) for file_name in file_names]
    combined_df = pd.concat(data_frames, ignore_index=True)
    logger.info("Plot UART Debug Data")
    # logger.info the headers
    df_headers = combined_df.columns.tolist()
   # logger.info("Headers:", df_headers)
    #combined_df['Times'] = pd.to_datetime(combined_df['Times'])
    combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = "enc10b_counter")
    #combined_df['Seconds'] = (combined_df['Times'] - combined_df['Times'].min()).dt.total_seconds()
    i = 0
    fig1, ax1 = plt.subplots()
    for column in combined_df.columns[2:]:
        i = i + 1
        fig, ax1 = plt.subplots()
        combined_df[column] = pd.to_numeric(combined_df[column], errors='coerce')
        
        combined_df['data'] = combined_df[column]#.diff()
        # Set the difference of the first row to be the same as the value in the first row
        combined_df.at[combined_df.index[0], 'data'] = combined_df.at[combined_df.index[0], column]
        ax1.bar(combined_df['elabsed_time'] , combined_df['data'] , color = cmap_colors[i], width = 20,edgecolor='black',label=column)
        #ax1.errorbar(combined_df['elabsed_time'], combined_df['data'], yerr=0.0, color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black', ms=marker_size)
        #ax1.plot(combined_df['elabsed_time'] , combined_df[column], color=col_row[i], ms=marker_size, label=column)
        ax1.grid(True)
        
        ax1.legend(loc="upper left")
        label_axis = "# Counts"
        label_text = column
        ax1.set_ylabel(label_axis)
        ax1.set_xlabel("Elapsed Time [S]")
        ax1.autoscale(enable=True, axis='x', tight=None)
        # Set the y-axis ticks to be integers
        #plt.yticks(np.arange(int(combined_df[column].min()), int(combined_df[column].max()) + 1,10))
        plt.xlim(-0.5, xlim)
        #plt.ylim(bottom=0)  # Set the minimum y-value to 5
        if text_enable: ax1.set_title(label_text)
        plt.tight_layout()
        plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
        plt.savefig(output_dir+ "plot_debug_time_" + column + ".pdf", bbox_inches='tight')
        logger.info("Plot " + column + " in UART Debug")
        ax1.set_title(label_text)
        plt.tight_layout()
        PdfPages.savefig()
        plt.clf()
        plt.close(fig)      
    logger.success("Save UART Debug Data plots to " + output_dir)
# Main function
if __name__ == '__main__':    
    PdfPages = PdfPages(output_dir+'mopshub_debug_test.pdf')
    logger.success("Opening PDF file:"+output_dir+'mopshub_debug_test.pdf')
    file_debug_date = "2024-02-05_19:23:59"
    debug_files =[output_dir+file_debug_date+"_debug/"+file_debug_date+"_mopshub_top_16bus_debug.csv"]
    plot_debug_time(file_names=debug_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_debug_date+"_debug/")
    PdfPages.close()
    