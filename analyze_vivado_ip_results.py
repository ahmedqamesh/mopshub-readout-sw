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
import matplotlib
from celluloid import Camera
from scipy import interpolate
import math
import re
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="Vivado IP data", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()
config_dir = rootdir+"/config_files/"
output_dir = rootdir+"/output_dir/"
data_dir = rootdir+"/data_files/"
from plot_style import *
path = os.path.abspath('') + '/'
logger.info('current working path: '+path)

def plot_xadc_data(PdfPages=None, file_names=[], text_enable=False,output_dir = None):
    #Source of Limits :https://www.mouser.com/pdfDocs/DCandACSwitchingCharacteristics.pdf
    data_frames = [pd.read_csv(file_name, skiprows=[1]) for file_name in file_names]
    combined_df = pd.concat(data_frames, ignore_index=True)
    logger.info("Plot combined XADC data")
    # Print the headers
    df_headers = combined_df.columns.tolist()
   # print("Headers:", df_headers)
    combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = "Times")
   
    pattern = r'status[^,]+'
    simple_headers = []
    for header in df_headers:
        match = re.search(pattern, header)
        if match:
            result = match.group()
            simple_headers = np.append(simple_headers, result)
        else: simple_headers = np.append(simple_headers, header)
    combined_df.columns = simple_headers
    combined_df['Times'] = pd.to_datetime(combined_df['Times'])
    combined_df['Seconds'] = (combined_df['Times'] - combined_df['Times'].min()).dt.total_seconds()
    i = 0
    for column in combined_df.columns[1:-1]:
        i = i + 1
        fig, ax1 = plt.subplots()
        ax1.errorbar(combined_df['Seconds'], combined_df[column], yerr=0.0, color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black', ms=marker_size)
        ax1.plot(combined_df['Seconds'] , combined_df[column], color=col_row[i], label=column)
        ax1.grid(True)
        ax1.legend(loc="upper left")
        if column == "TEMPERATURE": 
            min_lim, max_lim = 0.0 , 85
            label_axis = column + " [°C]"
            label_text = "Temperature in C [0, 85] °C"
        if column == "VCCAUX": 
            min_lim, max_lim = -0.5 , 2.0
            label_axis = column + " [V]"
            label_text = "Auxiliary Supply voltage [-0.5, 2.0] V"
        if column == "VCCBRAM": 
            min_lim, max_lim = -0.5 , 1.1
            label_axis = column + " [V]"
            label_text = "Supply voltage for the block RAM memories [-0.5, 1.1] V"
        if column == "VCCINT ": 
            min_lim, max_lim = -0.5 , 1.1
            label_axis = column + " [V]"
            label_text = "Internal Supply voltage [-0.5, 1.1] V"

        ax1.set_ylabel(label_axis)
        gray_region = (min_lim, max_lim)
        ax1.fill_between(combined_df['Seconds'], gray_region[0], gray_region[1], color='gray', alpha=0.2, label='limitation')
        plt.axhline(y=gray_region[0], linewidth=1, color='#d62728', linestyle='dashed')
        plt.axhline(y=gray_region[1], linewidth=1, color='#d62728', linestyle='dashed')
        ax1.set_xlabel("Elapsed Time [S]")
        ax1.autoscale(enable=True, axis='x', tight=None)
        plt.ylim(min_lim - 5, max_lim + 5)
        if text_enable: ax1.set_title(label_text)
        plt.tight_layout()
        plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
        plt.savefig(output_dir+ "plot_xadc_data_" + column + ".pdf", bbox_inches='tight')
        logger.info("Plot " + column + "in XADC data")
        ax1.set_title(label_text)
        plt.tight_layout()
        PdfPages.savefig()
        plt.clf()
        plt.close(fig)              
    logger.success("Save XADC data plots to "+output_dir)
    
def plot_ila_data(PdfPages=None, file_names=None, seu_time_hr=None, text_enable=False,output_dir = None):
    data_frames = [pd.read_csv(file_name, skiprows=[1]) for file_name in file_names]
    combined_df = pd.concat(data_frames, ignore_index=True)
    
    logger.info("Plot combined ILA data")
    # print(df)
    # Print the headers
    df_headers = combined_df.columns.tolist()
    #print("Headers:", df_headers)
   
    pattern = r'status[^,]+'
    simple_headers = []
    for header in df_headers:
        match = re.search(pattern, header)
        if match:
            result = match.group()
            simple_headers = np.append(simple_headers, result)
        else: simple_headers = np.append(simple_headers, header)
    combined_df.columns = simple_headers 
    combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = "TRIGGER")
    
    i = 0
    for column in combined_df.columns[2:]:
        fig, ax1 = plt.subplots()
        i = i + 1
        # print(f'Row {index + 1}, I values: {row.iloc[9:].tolist()}')
        # ax1.errorbar(df.iloc[:, 0], df[column], yerr=0.0, color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black', ms=marker_size)
        column_index = combined_df.columns.get_loc(column)
        ax1.plot(combined_df[column], color=col_row[i], label=column)
        #plt.step(combined_df.iloc[:, 1], combined_df[column], color=col_row[0], where='post', label=column)
        #plt.step(combined_df.iloc[:, 0], combined_df[column], color=col_row[1], where='post', label=column)
        # plt.step(df.iloc[:, 0],df["status_correction"], color=col_row[2], where='post', label="status_correction")
        # ax1.ticklabel_format(useOffset=False)
        ax1.grid(True)
        ax1.legend(loc="upper left")
        # intensities = ["I"+f'${i}$' for i in range(0, 15)]
        ax1.set_ylabel("Signal")
        ax1.set_xlabel("Trigger")
        plt.ylim(0, 2)
        # plt.xlim(0, 50)
        #ax1.set_yticks(range(-1, 2))
        # ax1.set_xticklabels(intensities)
        # ax1.autoscale(enable=True, axis='x', tight=None)
        if text_enable: ax1.set_title("SEU Status")
        plt.tight_layout()
        plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
        plt.savefig(output_dir+ "plot_ila_data_" + column + ".pdf", bbox_inches='tight')
        logger.info("Plot " + column + " ILA data")
        ax1.set_title("SEU Status")
        plt.tight_layout()
        PdfPages.savefig()
        plt.clf() 
        plt.close(fig)   
    logger.success("Save ILA data plots to "+output_dir)
# Main function
if __name__ == '__main__':    
    PdfPages = PdfPages(output_dir+'mopshub_vivado_ip_test.pdf')
    logger.success("Opening PDF file:"+output_dir+'mopshub_vivado_ip_test.pdf')
    file_vivado_date = "2024-04-08_17:40:09"#"2024-02-14_15:57:28"
    xadc_files = [output_dir+file_vivado_date+"_vivado/"+file_vivado_date+"_hw_xadc_data_file.csv"]
    ila_files = [output_dir+file_vivado_date+"_vivado/"+file_vivado_date+"_ila_data_file.csv"]
    #plot_xadc_data(file_names=xadc_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_vivado_date+"_vivado/")
    plot_ila_data(file_names=ila_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_vivado_date+"_vivado/")
    PdfPages.close()
    