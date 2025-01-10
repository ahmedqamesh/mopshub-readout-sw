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
from matplotlib import gridspec
import matplotlib.cbook as cbook
import matplotlib.image as image
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import ScalarFormatter
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from analysis      import Analysis
from logger_main   import Logger
from scipy.stats import expon
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

    
def load_data(file_names =None, indices =None):
    
    data_frames = []
    unique_minutes_full = []
    unique_fluence_full = []
    for file in file_names:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file)
        
        # Remove the last row
        df = df.iloc[:-1]  # Assuming the last row is to be removed
        df.columns = df.columns.str.strip() 
        df['Times'] = pd.to_datetime(df['Times'], format='%Y-%m-%d_%H:%M:%S', errors='coerce')
        df["rst_counter"] = pd.to_numeric(df["rst_counter"], errors='coerce')
        df['rst_diff'] = df["rst_counter"].diff()
        df = df.dropna(subset=['Times'])
        
        # Append the modified DataFrame to the list
        hours, unique_hours, unique_minutes  = AnalysisUtils().getHours(TimeStamps = df.Times, min_scale ="min_scale", device = "fpga_card", full_minutes = True)
        
        if indices == None: index = file_names.index(file)
        else: index = indices[file_names.index(file)]-1
        run_info, df ,unique_fluence,accomulated_fluence_array, shaded_regions = Analysis().get_run_info(data_frame = df , 
                                                                                                         run_index = index, 
                                                                                                         data_dir = data_dir,
                                                                                                         PdfPages = PdfPages,
                                                                                                         run_minutes = unique_minutes) 
          
        #check available minutes
        #unique_minutes = [minute for minute in unique_minutes if minute is not False]
        unique_minutes_full = np.append(unique_minutes_full, unique_minutes)
        unique_fluence_full = np.append(unique_fluence_full, unique_fluence)
        data_frames.append(df)    
    #Find indices where unique_minutes_full is non-zero
    valid_indices = np.nonzero(unique_minutes_full)
    valid_unique_minutes = unique_minutes_full[valid_indices]
    

    combined_df = pd.concat(data_frames, ignore_index=True) #This parameter ensures that the resulting DataFrame has a new sequential index.
    # # Filter rows where rst_diff == 1
    # filtered_df = combined_df[combined_df['rst_diff'] == 1]
    # filtered_df['Time_Interval'] = filtered_df['Times'].diff().dt.total_seconds() / 60  # Convert to minutes
    #
    # filtered_df = filtered_df.dropna()  # Drop the first row with NaN value in Time_Interval
    # # # Extract time intervals
    # time_intervals = filtered_df['Time_Interval'].values
    # print(filtered_df)
    # print(time_intervals)
    #
    # # Fit the exponential distribution
    # params = expon.fit(time_intervals, floc=0)  # Fix location to 0
    # rate = params[1]
    #
    #
    # # Plotting
    # plt.figure(figsize=(10, 6))
    # plt.hist(time_intervals, bins=10, density=True, alpha=0.6, color='g', edgecolor='black')
    #
    # # Plot the PDF of the fitted distribution
    # xmin, xmax = plt.xlim()
    # x = np.linspace(xmin, xmax, 100)
    # p = expon.pdf(x, loc=0, scale=1/rate)
    # plt.plot(x, p, 'k', linewidth=2)
    #
    # plt.xlabel('Time between resets (minutes)')
    # plt.ylabel('Probability Density')
    # plt.title('Histogram of Time Between Resets with Fitted Exponential Distribution')              
    # Print the headers
    df_headers = combined_df.columns.tolist()
      
    combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = df_headers[-1])   

    return combined_df, df_headers, valid_indices, unique_minutes_full,accomulated_fluence_array, shaded_regions

def extract_data_info(file_names = None,module_name = None, min_scale = None, indices = None):
    data_frame, df_headers, valid_indices, unique_minutes_full,accomulated_fluence_array, shaded_regions = load_data(file_names =file_names, indices = indices) 
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
                                                                                                          counts = True,
                                                                                                          device = "fpga_card")    
    
    
    return data_frame, new_headers,hourlyAverageValues, hourlySTDValues,day, unique_days, valid_indices, unique_minutes_full,accomulated_fluence_array, shaded_regions


def plot_debug_time(PdfPages=None, file_names=[], text_enable=False, xlim =500,output_dir = None,average =None, min_scale = "min_scale",indices = None):
    #data_frames = [pd.read_csv(file_name, skiprows=[1]) for file_name in file_names]
    #combined_df = pd.concat(data_frames, ignore_index=True)
    
    logger.info("Plot UART Debug Data")
   #  # logger.info the headers
   #  df_headers = combined_df.columns.tolist()
   # # logger.info("Headers:", df_headers)
   #  #combined_df['Times'] = pd.to_datetime(combined_df['Times'])
   #  combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = "enc10b_counter")
    #combined_df['Seconds'] = (combined_df['Times'] - combined_df['Times'].min()).dt.total_seconds()
    combined_df, new_headers,hourlyAverageValues, hourlySTDValues,day, unique_days, valid_indices, unique_minutes_full, accomulated_fluence_array, shaded_regions = extract_data_info(file_names = file_names,min_scale = min_scale, indices =indices)
    hours, unique_hours, unique_minutes  = AnalysisUtils().getHours(TimeStamps = combined_df.Times, min_scale =min_scale, device = "fpga_card",full_minutes = False)

    i = 0
    fig, ax = plt.subplots()
    for column in combined_df.columns[2:-8]:
        i = i + 1
        fig, ax = plt.subplots()
        if min_scale == "min_scale": 
            period = np.arange(len(hourlyAverageValues[i])) 
            ax.set_xlabel("Time [Min]")
        else:  
            period = np.arange(len(unique_hours))
            ax.set_xlabel("Time [h]")           
        combined_df.at[combined_df.index[0], 'data'] = combined_df.at[combined_df.index[0], column]
        combined_df[column] = pd.to_numeric(combined_df[column], errors='coerce')
        combined_df['data'] = combined_df[column]#.diff()
        # Set the difference of the first row to be the same as the value in the first row
        
        #print(combined_df[column])
        #ax.bar(combined_df['Times'] , combined_df['data'] , color = cmap_colors[i], width = 20,edgecolor='black',label=column)
        
        if average:

            #ax.errorbar(combined_df['Times'], hourlyAverageValues[i], yerr=0.0, color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
            ax.plot(combined_df['Times'], hourlyAverageValues[i],'*', label=column)  
        else: 
            ax.errorbar(combined_df['Times'], combined_df['data'], yerr=0.0, color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
            ax.plot(combined_df['Times'] , combined_df['data'], color=col_row[i], label=column)      
        #ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        time_in_min = []
        for run, start, end in shaded_regions:
            start_time = pd.to_datetime(start)
            end_time = pd.to_datetime(end)
            time_in_min = np.append(time_in_min,start_time + (end_time - start_time) / 2)
            ax.axvspan(start_time, end_time, color='gray', alpha=0.1)
            ax.annotate(run, xy=(start_time + (end_time - start_time) / 2, 1.5), xycoords='data',
                         ha='center', va='center', fontsize=5, bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'))

        # Ensure y-axis has integer ticks only
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
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
        ax2.set_xlabel('Accumulated Fluence [Proton/cm$^2$]')
        ax2.xaxis.set_label_position('bottom')
        ax2.xaxis.tick_bottom()
        ax2.spines['bottom'].set_position(('outward', 30))
         # Add annotation at the edge of the axis for the exponent
        fig.canvas.draw()
        ax2_bounds = ax2.get_position().bounds
        ax2_x_end = ax2_bounds[0] + ax2_bounds[2] + 0.03
        ax2.annotate(r'$\times 10^{12}$', xy=(1, -0.22), xycoords='axes fraction', ha='right', va='center')
        
        ax.grid(True)
        ax.legend(loc="upper left")
        label_axis = "Count rate [#/min]"
        label_text = column
        ax.set_ylabel(label_axis)
        
        #ax.autoscale(enable=True, axis='x', tight=None)
        # Set the y-axis ticks to be integers
        #plt.yticks(np.arange(int(combined_df[column].min()), int(combined_df[column].max()) + 1,10))

        if text_enable: ax.set_title(label_text)
        #plt.tight_layout()
        plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
        plt.savefig(f"{file_names[0][:-4]}_{column}.pdf", bbox_inches='tight')
        logger.info("Plot " + column + " in UART Debug")
        ax.set_title(label_text)
        #plt.tight_layout()
        PdfPages.savefig()
        plt.clf()
        plt.close(fig)      
    logger.success("Save UART Debug Data plots to " + output_dir)
# Main function
if __name__ == '__main__':    
    PdfPages = PdfPages(output_dir+'mopshub_debug_test.pdf')
    logger.success("Opening PDF file:"+output_dir+'mopshub_debug_test.pdf')
    uart_basic_tests = {             
          "data_files/proton_irradiation_1":[#top
                {
                "during_Irradiation/uart":[#module folder
                    {"mopshub_readout_16bus":["2024-07-07_15:25:05_mopshub_readout_16bus_debug.csv",#Run1
                                              "2024-07-07_15:33:47_mopshub_readout_16bus_debug.csv",#,#Run1
                                              "2024-07-07_16:04:47_mopshub_readout_16bus_debug.csv",#,#Run2
                                              "2024-07-07_17:57:37_mopshub_readout_16bus_debug.csv",#,#Run2
                                              "2024-07-07_18:01:54_mopshub_readout_16bus_debug.csv",#Run3
                                              "2024-07-07_18:02:11_mopshub_readout_16bus_debug.csv",#Run3
                                              "2024-07-07_18:13:51_mopshub_readout_16bus_debug.csv",#Run4
                                              "2024-07-07_18:29:48_mopshub_readout_16bus_debug.csv",#Run5
                                              "2024-07-07_18:49:10_mopshub_readout_16bus_debug.csv",#Pause
                                              "2024-07-07_18:51:56_mopshub_readout_16bus_debug.csv",#Run6
                                              "2024-07-07_18:57:43_mopshub_readout_16bus_debug.csv"]#Run6
                                                #"2024-07-07_19:03:08_ila_data_file_1.csv"]#Run6
                    }
                    ]                
                }
            ] 
          
        } 
    proton_tests_top = "data_files/proton_irradiation_1"#next(iter(xadc_basic_tests))#get top 
    modules_name = []
    #for ic in xadc_basic_tests[proton_tests_top]: modules_name.extend(list(ic.keys()))   
    for ic in uart_basic_tests[proton_tests_top]:
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
                    
                    plot_debug_time(file_names=file_names,
                                    PdfPages=PdfPages,
                                    text_enable =False,
                                    average = True,
                                    indices = [1,1,2,2,3,3,4,5,0,6,6],
                                    output_dir =  f"{file_directory}")
    
    PdfPages.close()
    