import sys
import os
from validators import length
import seaborn as sns
import numpy as np
from scipy.optimize import curve_fit
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
def plot_histogram(xValues =  None, zValues = None, xlabel="Value", ylabel="Frequency", title="Histogram", bins=10, file_out=None):
    xValues = np.array(xValues)
    # Calculate the differences
    #xValues = np.diff(xValues)
    cmap = plt.cm.get_cmap('viridis')   # Choose a colormap          

    fig, ax = plt.subplots()
    #get the dose              
    #zValues = self.calculate_dose(zValues)
    start_index = 0
    max_voltage = max(xValues)
    min_voltage = min(xValues)
    ctick_size = (max_voltage - min_voltage) / float(bins)  
    plot_range = np.round(np.arange(min_voltage, max_voltage, ctick_size),3)
    tick_size = 1
    hist, bin_edges = np.histogram(xValues, bins=bins)
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
    ax.bar(bin_centres, hist,width=np.diff(bin_edges), edgecolor='black')#, alpha=0.7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    #ax.set_xticks(np.arange(0,len(bin_edges)))
    #ax.set_xticklabels(bin_edges, rotation = 90)
    if coeff is not None:
        pass #ax.plot(bin_centres, gau, "r-", label='Normal distribution')
    ax.grid(True)
    fig.savefig(file_out[:-4]+"_gaus.pdf", bbox_inches='tight')  
    PdfPages.savefig()
    return None
    
def load_data(file_names =None ):
    data_frames = [pd.read_csv(file_name, skiprows=[1]) for file_name in file_names]
    combined_df = pd.concat(data_frames, ignore_index=True) 
    # Print the headers
    df_headers = combined_df.columns.tolist()
   # print("Headers:", df_headers)
    #combined_df = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = "VCCINT")
    data_frame = AnalysisUtils().check_last_row(data_frame = combined_df, file_name = file_names, column = df_headers[-1])
    return data_frame, df_headers

def plot_xadc_data(PdfPages=None, file_names=[], text_enable=False,output_dir = None, average =None):
    logger.info("Plot combined XADC data")
    data_frame, df_headers = load_data(file_names =file_names) 
    #Source of Limits :https://www.mouser.com/pdfDocs/DCandACSwitchingCharacteristics.pdf
    data_frame['Times'] = pd.to_datetime(data_frame['Times'])
    data_frame['Seconds'] = (data_frame['Times'] - data_frame['Times'].min()).dt.total_seconds()
    hours, unique_hours = AnalysisUtils().getHours(TimeStamps = data_frame.Times, device = "fpga_card")
    day, unique_days = AnalysisUtils().getDay(TimeStamps = data_frame.Times, device ="fpga_card")
    
    hourlyAverageValues = [0 for i in range(len(df_headers))]
    hourlySTDValues = [0 for i in range(len(df_headers))]
    new_headers = []
    n_points = 1
    for pos,column in enumerate(df_headers):
        if pos > 0 and pos < len(df_headers):
            hourlyAverageValues[pos-1], hourlySTDValues[pos-1] = AnalysisUtils().get_hourly_average_value(data_frame = data_frame , 
                                                                                                          column = column,
                                                                                                          unique_days = unique_days,
                                                                                                          n_points= n_points,
                                                                                                          device = "fpga_card")
    period = np.arange(len(unique_hours)*n_points)
    i = 0
    for column in data_frame.columns[1:-1]:
        
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
        plot_histogram(xValues =  data_frame[column].astype(float), zValues = None, xlabel=column, 
                       ylabel="Frequency", 
                       title=f"{column} Histogram", 
                       bins=20, 
                       file_out=f"{file_names[0]}")
                    
        fig1, ax1 = plt.subplots()
        gray_region = (min_lim, max_lim)
        if average:
            ax1.errorbar(period, hourlyAverageValues[i], yerr=hourlySTDValues[i], color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
            ax1.plot(period , hourlyAverageValues[i], color=col_row[i], label=column)          
            ax1.fill_between(period, gray_region[0], gray_region[1], color='gray', alpha=0.2, label='limitation')  
        else:
            ax1.errorbar(data_frame['Seconds'], data_frame[column], yerr=0.0, color=col_row[i], fmt='o' , markerfacecolor='black', markeredgecolor='black')
            ax1.plot(data_frame['Seconds'] , data_frame[column], color=col_row[i], label=column)
            ax1.fill_between(data_frame['Seconds'], gray_region[0], gray_region[1], color='gray', alpha=0.2, label='limitation')
        ax1.grid(True)
        ax1.legend(loc="upper left")

        ax1.set_ylabel(label_axis)
        plt.axhline(y=gray_region[0], linewidth=1, color='#d62728', linestyle='dashed')
        plt.axhline(y=gray_region[1], linewidth=1, color='#d62728', linestyle='dashed')

        ax1.set_xlabel("Elapsed Time [S]")
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
        i = i + 1
        plt.close(fig1)              
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
    basic_tests = { 
          "data_files/neutron_irradiation":[#top
                {
                "before_Irradiation":[#module folder
                    {"mopshub_board_xadc_v3_1":[]#files
                     },
                    {"mopshub_board_xadc_v3_2":[]#files
                     },                  
                    {"mopshub_board_xadc_v2_1":[]#files
                     }    
                    ]                
                
                }
            ]               
        } 
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
        neutron_tests_top = "data_files/neutron_irradiation"#next(iter(basic_tests))#get top 
        modules_name = []
        for ic in basic_tests[neutron_tests_top]: modules_name.extend(list(ic.keys()))   
        for ic in basic_tests[neutron_tests_top]:
             for m in ic:# get module folder
                for t in ic[m]:
                    for p in t: #get files
                        file = f"{neutron_tests_top}/{m}/{p}.csv"
                        file_directory = os.path.dirname(file)
                        file_name = os.path.basename(file)         
                        plot_xadc_data(file_names=[f"{rootdir}/{file}"],
                                       PdfPages=PdfPages,text_enable =True,average =True,
                                       output_dir = f"{rootdir}/{file_directory}")                        
                            
    
    file_vivado_date = "2024-04-08_17:40:09"#"2024-02-14_15:57:28"
    ila_files = [output_dir+file_vivado_date+"_vivado/"+file_vivado_date+"_ila_data_file.csv"]
    #plot_ila_data(file_names=ila_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_vivado_date+"_vivado/")
    PdfPages.close()
    