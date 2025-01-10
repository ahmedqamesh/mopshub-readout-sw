########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
import sys
import os
from validators import length
import seaborn as sns
import numpy as np
from scipy.optimize import curve_fit
from matplotlib import gridspec
import matplotlib.cbook as cbook
from matplotlib.ticker import ScalarFormatter
import matplotlib.image as image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from analysis      import Analysis
from logger_main   import Logger
import logging
import pandas as pd
import csv
import matplotlib
import matplotlib.dates as mdates
from celluloid import Camera
from mopshub.plotting   import Plotting
from scipy import interpolate
from scipy.interpolate import interp1d
from matplotlib.patches import FancyBboxPatch
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

def load_data(file_names =None, indices =None, PdfPages =None):
    data_frames = []
    unique_minutes_full = []
    unique_fluence_full = []
    for file in file_names:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file)
        
        # Remove the last row
        df = df.iloc[:-1]  # Assuming the last row is to be removed
        df.columns = df.columns.str.strip()
        df['Times'] = pd.to_datetime(df['Times'], errors='coerce')
        df = df.dropna(subset=['Times'])
        # Append the modified DataFrame to the list
        hours, unique_hours, unique_minutes  = AnalysisUtils().getHours(TimeStamps = df.Times, min_scale ="min_scale", device = "fpga_card", full_minutes = True)   
        if indices == None: index = file_names.index(file)
        else: index = indices[file_names.index(file)]-1
        run_info, df ,unique_fluence,accomulated_fluence_array, shaded_regions = Analysis().get_run_info(data_frame = df , 
                                                                                                         run_index = index, 
                                                                                                         run_minutes = unique_minutes,
                                                                                                         PdfPages = PdfPages,
                                                                                                         data_dir = data_dir)   
        #check available minutes
        #unique_minutes = [minute for minute in unique_minutes if minute is not False]
        unique_minutes_full = np.append(unique_minutes_full, unique_minutes)
        unique_fluence_full = np.append(unique_fluence_full, unique_fluence)
        data_frames.append(df)    
    #Find indices where unique_minutes_full is non-zero
    valid_indices = np.nonzero(unique_minutes_full)
    valid_unique_minutes = unique_minutes_full[valid_indices]
    #data_frames = [pd.read_csv(file_name, skiprows=[1]) for file_name in file_names

    combined_df = pd.concat(data_frames, ignore_index=True) #This parameter ensures that the resulting DataFrame has a new sequential index.
    
    # Method 1: Using df.mean() and df.std()
    mean_values = combined_df.mean()
    std_dev_values = combined_df.std()
    
    logger.report(f"Mean = {mean_values}")
    logger.report(f"SD = {std_dev_values}")
    # Print the headers
    df_headers = combined_df.columns.tolist()
      
    combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = df_headers[-1])   
    return combined_df, df_headers, valid_indices, unique_minutes_full,accomulated_fluence_array, shaded_regions

def extract_data_info(file_names = None,module_name = None, min_scale = None, PdfPages = None):
    data_frame, df_headers, valid_indices, unique_minutes_full,accomulated_fluence_array, shaded_regions = load_data(file_names =file_names, PdfPages = PdfPages) 
    #Source of Limits :https://www.mouser.com/pdfDocs/DCandACSwitchingCharacteristics.pdf

    day, unique_days = AnalysisUtils().getDay(TimeStamps = data_frame.Times, device ="fpga_card")
    hourlyAverageValues = [0 for i in range(len(df_headers))]
    hourlySTDValues = [0 for i in range(len(df_headers))]

    new_headers = []
    for pos,column in enumerate(df_headers):
        if pos > 0 and pos < len(df_headers):
            hourlyAverageValues[pos-1], hourlySTDValues[pos-1], data_frame = AnalysisUtils().get_hourly_average_value(data_frame = data_frame , 
                                                                                                          column = column,
                                                                                                          unique_days = unique_days,
                                                                                                          min_scale = min_scale,
                                                                                                          device = "fpga_card")    
    
    return data_frame, new_headers,hourlyAverageValues, hourlySTDValues,day, unique_days, valid_indices, unique_minutes_full,accomulated_fluence_array, shaded_regions

def plot_xadc_data(PdfPages=None, file_names=[], text_enable=False,output_dir = None, average =None,modules_name =None):
    logger.info("Plot combined XADC data")
    if modules_name == "during_Irradiation/xadc": 
        min_scale = "min_scale"
    else: min_scale = "h_scale"       
    data_frame, new_headers,hourlyAverageValues, hourlySTDValues,day, unique_days, valid_indices, unique_minutes_full, accomulated_fluence_array, shaded_regions = extract_data_info(file_names = file_names,
                                                                                                                                                                                     PdfPages = PdfPages,
                                                                                                                                                                                     min_scale = min_scale)
    hours, unique_hours, unique_minutes  = AnalysisUtils().getHours(TimeStamps = data_frame.Times, min_scale =min_scale, device = "fpga_card")
    i = 0
    time_in_min = [36.5, 60.0, 120.0 , 185.0 , 250.0 ,300.0]
    fig, ax = plt.subplots()
    for column in data_frame.columns[1:-8]:#Ignore Flence and Duration Plot
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
        if column == "VCCINT": 
            min_lim, max_lim = -0.5 , 1.1
            label_axis = column + " [V]"
            label_text = "Internal Supply voltage [-0.5, 1.1] V"       
            hourlyAverageValues[i] = hourlyAverageValues[i]*1.02  
             # Get the accumulated fluence over time
        # Plotting().plot_histogram(xValues =  data_frame[column].astype(float), zValues = None, xlabel=column, 
        #                ylabel="Frequency", 
        #                title=f"{column} Histogram", 
        #                bins=20, 
        #                file_out=f"{file_names[0]}")         
        fig1, ax1 = plt.subplots()
        gray_region = (min_lim, max_lim)
        original_length = len(unique_minutes_full)
        hourlyAverageValues_full = np.zeros(original_length)
        hourlySTDValues_full = np.zeros(original_length)
        if min_scale == "min_scale": 
            period = np.arange(len(unique_minutes)) 
            ax1.set_xlabel("Time [Min]")
        else:  
            period = np.arange(len(unique_hours))
            ax1.set_xlabel("Time [h]")
        
        
        if average:
            if modules_name == "during_Irradiation/xadc":
                hourlyAverageValues_full[valid_indices] =hourlyAverageValues[i]
                hourlySTDValues_full[valid_indices] =hourlySTDValues[i]
                # Filter out False (0) values for plotting
                indices_to_plot = [i for i, val in enumerate(hourlyAverageValues_full) if val]
                period =  np.arange(len(indices_to_plot)) 

                j = 0
                for run, start, end in shaded_regions:
                    start_time = pd.to_datetime(start)
                    end_time = pd.to_datetime(end)
                    start_bin = pd.Timedelta(end_time-start_time).total_seconds() // 60
                    ax1.axvspan(time_in_min[j] -start_bin/2, time_in_min[j]+start_bin/2, color='gray', alpha=0.1)
                    ax1.annotate(run, xy=(time_in_min[j], max_lim/2*1.1), xycoords='data',
                                 ha='center', va='center', fontsize=5, bbox= dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'))
                    j = j+1  
                        
                ax1.errorbar(indices_to_plot,[hourlyAverageValues_full[i] for i in indices_to_plot], yerr=hourlySTDValues_full[i], color=col_row[i], fmt='o-' , markerfacecolor='black', markeredgecolor='black')
                ax1.plot(indices_to_plot , [hourlyAverageValues_full[i] for i in indices_to_plot], color=col_row[i], label=column)          
                ax1.fill_between(np.arange(len(hourlyAverageValues_full)) , gray_region[0], gray_region[1], color='gray', alpha=0.1, label='limitation')                    
                if column != "TEMPERATURE":

                    ax.errorbar(indices_to_plot, [hourlyAverageValues_full[i] for i in indices_to_plot], yerr=hourlySTDValues_full[i], color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
                    line, = ax.plot(indices_to_plot , [hourlyAverageValues_full[i] for i in indices_to_plot], color=col_row[i], label=column) 
                    ax.set_xlim(0, max(indices_to_plot)+20)
            else: 
                ax1.errorbar(period, hourlyAverageValues[i], yerr=hourlySTDValues[i], color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
                ax1.plot(period , hourlyAverageValues[i], color=col_row[i], label=column)          
                ax1.fill_between(period, gray_region[0], gray_region[1], color='gray', alpha=0.2, label='limitation') 
                                
                if column != "TEMPERATURE":
                    ax.errorbar(period, hourlyAverageValues[i], yerr=hourlySTDValues[i], color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
                    ax.plot(period , hourlyAverageValues[i], color=col_row[i], label=column) 
            
                else:
                    pass
        else:
            ax1.errorbar(data_frame['Times'], data_frame[column], color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
            ax1.plot(data_frame['Times'] , data_frame[column], color=col_row[i], label=column)
            ax1.fill_between(data_frame['Times'], gray_region[0], gray_region[1], color='gray', alpha=0.1, label='limitation')
            if column != "TEMPERATURE":
                ax.errorbar(data_frame['Times'], data_frame[column], color=col_row[i], fmt='o')
                ax.plot(data_frame['Times'] , data_frame[column], color=col_row[i], label=column)      
            else:
                pass
        i = i + 1
        ax1.grid(True)
        ax1.legend(loc="upper left")    
        ax1.set_ylabel(label_axis)
        plt.axhline(y=gray_region[0], linewidth=1, color='#d62728', linestyle='dashed')
        plt.axhline(y=gray_region[1], linewidth=1, color='#d62728', linestyle='dashed')
        
        ax1.autoscale(enable=True, axis='x', tight=None)
        plt.ylim(min_lim - 5, max_lim + 5)
        if text_enable: ax1.set_title(label_text)
        plt.tight_layout()
        plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
        plt.savefig(f"{file_names[0][:-4]}_{column}.pdf", bbox_inches='tight')
        logger.info("Plot " + column + " in XADC data")
        ax1.set_title(label_text)
        plt.tight_layout()
        PdfPages.savefig()
        plt.clf()
        plt.close(fig1)              
        
    
    j = 0
    for run, start, end in shaded_regions:
        start_time = pd.to_datetime(start)
        end_time = pd.to_datetime(end)
        start_bin = pd.Timedelta(end_time-start_time).total_seconds() // 60
        ax.axvspan(time_in_min[j] -start_bin/2, time_in_min[j]+start_bin/2, color='gray', alpha=0.1)
        ax.annotate(run, xy=(time_in_min[j], 1.5), xycoords='data',
                     ha='center', va='center', fontsize=5, bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'))
        j = j+1            
    # Ensure y-axis has integer ticks only
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    # Create secondary y-axis
    ax2 = ax.twiny()
    # Set secondary x-axis ticks and labels
    xfmt = ScalarFormatter(useMathText=True)
    ax2.set_xticks(time_in_min)
    ax2.set_xlim(ax.get_xlim())
   
    ax2.xaxis.set_major_formatter(xfmt)  # Use scientific notation with exponent
    ax2.set_xticklabels([f'{fluence/1e12:.2f}' for fluence in accomulated_fluence_array[1:]])
    #xfmt.set_useOffset(10)
    ax2.set_xlabel('Accumulated Fluence [Proton/Cm$^2$]')
    ax2.xaxis.set_label_position('bottom')
    ax2.xaxis.tick_bottom()
    ax2.spines['bottom'].set_position(('outward', 30))
     # Add annotation at the edge of the axis for the exponent
    fig.canvas.draw()
    ax2_bounds = ax2.get_position().bounds
    ax2_x_end = ax2_bounds[0] + ax2_bounds[2] + 0.03
    ax2.annotate(r'$\times 10^{12}$', xy=(1, -0.2), xycoords='axes fraction', ha='right', va='center')
       
    ax.grid(True)
    ax.legend(loc="upper left")    
    ax.set_ylabel("Voltage [V]")
    ax.set_xlabel("Time [Min]")
    ax.set_ylim(0,2.5)
    fig.savefig(f"{file_names[0][:-4]}_all.pdf", bbox_inches='tight')
    ax.set_title(label_text)
    PdfPages.savefig()
    plt.close(fig) 
    logger.success("Save XADC data plots to "+output_dir)

def plot_ila_data(PdfPages=None, file_names=None, seu_time_hr=None, text_enable=False,output_dir = None,indices = None):
    combined_df, df_headers, valid_indices, unique_minutes_full,accomulated_fluence_array, shaded_regions = load_data(file_names = file_names,
                                                                                                                       indices = indices, 
                                                                                                                       PdfPages = PdfPages)
    logger.info("Plot combined ILA data")
    pattern = r'status[^,]+'
    simple_headers = []
    for header in df_headers:
        match = re.search(pattern, header)
        if match:
            result = match.group()
            simple_headers = np.append(simple_headers, result)
        else: simple_headers = np.append(simple_headers, header)
    combined_df.columns = simple_headers 
    #combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = "uncorrectable")
    i = 0
    fig, ax = plt.subplots()
    for column in combined_df.columns[6:-4]:
        fig1, ax1 = plt.subplots()
        print(f"{column}[{combined_df[column].count()}]:{combined_df[column].value_counts()}")
        # print(f'Row {index + 1}, I values: {row.iloc[9:].tolist()}')
        # ax1.errorbar(df.iloc[:, 0], df[column], yerr=0.0, color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black', ms=marker_size)
        column_index = combined_df.columns.get_loc(column)
        #ax1.plot(combined_df[column], color=col_row[i], label=column)
        x_values = np.arange(len(combined_df[column]))
        combined_df['Times'] = pd.to_datetime(combined_df['Times'])
        #combined_df['Times'] = combined_df['Times'].dt.strftime('%H:%M')
        ax1.step(x_values, combined_df[column], color=col_row[i], where='post', label=column)
        exclude_columns = ["injection", "classification", "uncorrectable"]
        
        if column  == "uncorrectable" : ax.step(combined_df['Times'], combined_df["uncorrectable"], color=col_row[i] , where='post', label="uncorrectable")
        if column not in exclude_columns : 
            ax.step(combined_df['Times'], combined_df[column]-(i+2)*1.5, color=col_row[i], where='post', label="status_"+ column)
            i = i + 1
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        time_in_min = []
        for run, start, end in shaded_regions:
            start_time = pd.to_datetime(start)
            end_time = pd.to_datetime(end)
            ax.axvspan(start_time, end_time, color='gray', alpha=0.01)
            time_in_min = np.append(time_in_min,start_time + (end_time - start_time) / 2)
            ax.annotate(run, xy=(start_time + (end_time - start_time) / 2, -1.6), xycoords='data',
                         ha='center', va='center', fontsize=5, bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'))

        # Ensure y-axis has integer ticks only
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        # Create secondary y-axis
        ax2 = ax.twiny()
        # Set secondary x-axis ticks and labels
        xfmt = ScalarFormatter(useMathText=True)
        #ax2.set_xticks(ax.get_xticks())
        ax2.set_xlim(ax.get_xlim())
        ax2.set_xticks(time_in_min)
        ax2.xaxis.set_major_formatter(xfmt)  # Use scientific notation with exponent
        ax2.set_xticklabels([f'{fluence/1e12:.2f}' for fluence in accomulated_fluence_array[1:]])
        #xfmt.set_useOffset(10)
        ax2.set_xlabel('Accumulated Fluence [Proton/cm$^2$]' )
        ax2.xaxis.set_label_position('bottom')
        ax2.xaxis.tick_bottom()
        ax2.spines['bottom'].set_position(('outward', 30))
         # Add annotation at the edge of the axis for the exponent
        fig.canvas.draw()
        ax2_bounds = ax2.get_position().bounds
        ax2_x_end = ax2_bounds[0] + ax2_bounds[2] + 0.03
        ax2.annotate(r'$\times 10^{12}$', xy=(1, -0.22), xycoords='axes fraction', ha='right', va='center')

        ax1.grid(True)
        ax1.legend(loc="upper left")
        ax1.set_ylabel("Signal")
        ax1.set_xlabel("Time")
        #plt.xlim(0, 400000)
        #ax1.set_yticks(range(-1, 2))
        # ax1.set_xticklabels(intensities)
        # ax1.autoscale(enable=True, axis='x', tight=None)
        if text_enable: ax1.set_title("SEU Status")
        plt.tight_layout()
        plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
        plt.savefig(f"{file_names[0][:-4]}_{column}.pdf", bbox_inches='tight')
        logger.info("Plot " + column + " ILA data")
        ax1.set_title("SEU Status")
        plt.tight_layout()
        PdfPages.savefig()
        plt.clf() 
        plt.close(fig1)  
    ax.grid(True)
    plt.yticks([])
    ax.legend(loc="upper left")    
    ax.set_ylabel("Signal")
    ax.set_xlabel("Time Stamp")
    fig.savefig(f"{file_names[0][:-4]}_all.pdf", bbox_inches='tight')
    ax.set_title("ILA xilinx Data")
    PdfPages.savefig()
    plt.close(fig)  
    logger.success("Save ILA data plots to "+output_dir)
# Main function
if __name__ == '__main__':    
    PdfPages = PdfPages(output_dir+'mopshub_vivado_ip_test.pdf')
    logger.success("Opening PDF file:"+output_dir+'mopshub_vivado_ip_test.pdf')
    
    xadc_basic_tests = { 
          "data_files/neutron_irradiation":[#top
                {
                "before_irradiation":[#module folder                  
                    {"mopshub_board_xadc_v2_1_neutron_before":[]#files
                     }    
                    ],                
                "after_irradiation":[#module folder                  
                    {"mopshub_board_xadc_v2_1_neutron_after":[]#files
                     }    
                    ],                
                }
            ],               
          "data_files/proton_irradiation_1":[#top
                {
                "during_Irradiation/xadc":[#module folder
                    {"mopshub_board_xadc_v3_2":["2024-07-07_15:48:47_hw_xadc_file.csv",
                                                "2024-07-07_16:05:01_hw_xadc_file.csv",
                                                "2024-07-07_17:57:50_hw_xadc_file.csv",
                                                "2024-07-07_18:14:03_hw_xadc_file.csv",
                                                "2024-07-07_18:55:59_hw_xadc_file.csv",
                                                "2024-07-07_19:03:08_hw_xadc_file.csv"]#files
                    }
                    ],
                "during_Irradiation/ila":[#module folder
                    {"mopshub_board_xadc_v3_2":["2024-07-07_15:29:50_ila_data_file_1.csv",#Run1
                                                "2024-07-07_15:41:52_ila_data_file_1.csv",#Run1
                                                "2024-07-07_15:48:47_ila_data_file_1.csv",#Run1
                                                "2024-07-07_16:05:01_ila_data_file_1.csv",#Run2
                                                "2024-07-07_16:32:13_ila_data_file_1.csv",#Run2
                                                "2024-07-07_16:37:03_ila_data_file_1.csv",#Run2
                                                "2024-07-07_16:37:57_ila_data_file_1.csv",#Run2
                                                "2024-07-07_16:39:14_ila_data_file_1.csv",#Run2
                                                "2024-07-07_17:57:50_ila_data_file_1.csv",#Run3
                                                "2024-07-07_18:05:23_ila_data_file_1.csv",#Run3
                                                "2024-07-07_18:14:03_ila_data_file_1.csv",#Run4
                                                "2024-07-07_18:23:22_ila_data_file_1.csv",#Run5
                                                "2024-07-07_18:55:59_ila_data_file_1.csv"]#Run6
                                                #"2024-07-07_19:03:08_ila_data_file_1.csv"]#Run6
                    }
                    ]                
                },
                {
                "before_Irradiation":[#module folder
                    {"mopshub_board_xadc_v3_2":[]#files
                     },
                    {"mopshub_board_xadc_v3_1":[]#files
                     }   
                    ]                                 
                
                }
            ] 
          
        } 

    min_scale = None
    if len(sys.argv) > 1:
       logger.notice(f"Processing Data files...")                 
       files_arg =  [f for f in range(len(sys.argv))]
       for number, file in enumerate(sys.argv[1:]):
            logger.notice(f"Opening {file}")
            file_directory = os.path.dirname(file)
            # Get file name
            file_name = os.path.basename(file)    
            plot_xadc_data(file_names=[file],
                           PdfPages=PdfPages,text_enable =True,average =True,
                           output_dir = file_directory) 
    else: 
        # AnalysisUtils().combine_csv_files("/home/dcs/git/mopshub-sw-kcu102/data_files/neutron_irradiation/after_irradiation/2024-08-03_10_34_33_hw_xadc_file.csv",
        #                                   "/home/dcs/git/mopshub-sw-kcu102/data_files/neutron_irradiation/after_irradiation/2024-08-03_11_52_26_hw_xadc_file.csv",
        #                                   "/home/dcs/git/mopshub-sw-kcu102/data_files/neutron_irradiation/after_irradiation/2024-08-04_09_41_44_hw_xadc_file.csv")
        
        proton_tests_top = "data_files/proton_irradiation_1"#next(iter(xadc_basic_tests))#get top 
        modules_name = []
        #for ic in xadc_basic_tests[proton_tests_top]: modules_name.extend(list(ic.keys()))   
        for ic in xadc_basic_tests[proton_tests_top]:
            for m in ic:# get module folder
                for t in ic[m]:
                    for p in t: #get files
        
                        if len(t[p])<1:
                            file_names = [f"{rootdir}/{proton_tests_top}/{m}/{p}.csv"]
                            file_directory = os.path.dirname(file_names[0])
                            file_name = os.path.basename(file_names[0])         
                        else:
                            file_names = [f"{rootdir}/{proton_tests_top}/{m}/{f}" for f in t[p]]
                            file_directory = os.path.dirname(f"{file_names[0]}")
                            file_name = os.path.basename(f"{rootdir}/{proton_tests_top}/{m}/{file_names[0]}")
        
                        if m =='during_Irradiation/ila':
                            plot_ila_data(file_names=file_names,
                                           PdfPages=PdfPages,
                                           text_enable =True,
                                           indices = [1,1,1,2,2,2,2,3,3,4,4,5,6],
                                           output_dir = f"{file_directory}")  
                        else:
        
                            plot_xadc_data(file_names=file_names,
                                           modules_name=m,
                                           PdfPages=PdfPages,
                                           text_enable =True,
                                           average =True,
                                           output_dir = f"{file_directory}")  
        neutron_tests_top = "data_files/neutron_irradiation"#next(iter(xadc_basic_tests))#get top 
        modules_name = []
        for ic in xadc_basic_tests[neutron_tests_top]: modules_name.extend(list(ic.keys()))   
        for ic in xadc_basic_tests[neutron_tests_top]:
             for m in ic:# get module folder
                for t in ic[m]:
                    for p in t: #get files
                        file = f"{neutron_tests_top}/{m}/{p}.csv"
                        file_directory = os.path.dirname(file)
                        file_name = os.path.basename(file)         
                        plot_xadc_data(file_names=[f"{rootdir}/{file}"],
                                       PdfPages=PdfPages,text_enable =True,
                                       average =True,
                                       output_dir = f"{rootdir}/{file_directory}")                        
        #


    PdfPages.close()
    