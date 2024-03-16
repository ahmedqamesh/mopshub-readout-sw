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
from logger_main   import Logger
import logging
import pandas as pd
import csv
import matplotlib
from celluloid import Camera
from scipy import interpolate
import matplotlib.image as image
import math

log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="HIT data", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()
config_dir = rootdir+"/config_files/"
output_dir = rootdir+"/output_dir/"
data_dir = rootdir+"/data_files/"

path = os.path.abspath('') + '/'
logger.info('current working path: '+path)


col_row = ['red', 'green', 'blue', '#1f78b4', '#33a02c', '#e31a1c', '#ff7f00', '#6a3d9a', '#b15928', '#a6cee3']
# Define the data from the table

plot_h, plot_w = 6,4
text_font, label_font , legend_font, marker_size = 12, 10, 8, 4

matplotlib.rcParams['lines.markersize'] = marker_size
# Set plot dimensions 
matplotlib.rcParams['figure.figsize'] = (plot_h, plot_w)  # Adjust the width and height as needed
# Set label font size
matplotlib.rcParams['axes.labelsize'] = label_font

# Set legend font size
matplotlib.rcParams['legend.fontsize'] = legend_font
# Set text font size
matplotlib.rcParams['font.size'] = text_font  # You can adjust the size as needed

def check_last_row (data_frame = None, file_name = None,column = "status"):
    data_frame_last_row = data_frame.tail(1)
    
    pattern_exists = any(data_frame_last_row[column].astype(str).str.contains("End of Test"))
    if pattern_exists: 
        logger.notice(f"Noticed a Complete test file named: {file_name}") 
        data_frame = data_frame.iloc[:-1]
    else: logger.warning(f"Noticed Incomplete test file")    
    return data_frame

def calculate_HIT_parameters(segma_litrature =None, pp3_fluence = None,n_bits = None ):#segma_litrature[/cm^2/bit] & pp3_fluence [/cm^2/pp]& n_bits [per device]
    logger.report(f"Literature value for SEU cross section = {segma_litrature}") 
    pp3_fluence = pp3_fluence* 40e+6
    n_seu_expected = segma_litrature * pp3_fluence *n_bits
    logger.report(f"Number of expected SEUs based on the PP3 fluence ({pp3_fluence} /cm^2)= {n_seu_expected}") 
    #Fluence: The number of particles per area, given in [cm^-2].
    needed_fluence = 20 /(segma_litrature * n_bits)
    logger.report(f"Facility fluence needed for 20 SEUs  in {n_bits} bits shift register= {'{:.2e}'.format(needed_fluence)}/cm^2") 
    
    # the intensity or flux of radiant energy is the power transferred per unit area (flux = fluence * time)
    intensity = [8.0e+07,1.2e+08 ,2.0e+08 ,3.2e+08 ,4.0e+08, 6.0e+08, 8.0e+08, 1.2e+09 ,2.0e+09 ,3.2e+09 ,4.0e+09 ,6.0e+09, 8.0e+09, 1.2e+10, 2.0e+10]
    seu_time_hr = []
    for i in intensity:
        seu_time = needed_fluence/i
        seu_time_hr = np.append(seu_time_hr,seu_time/(60*60))
        logger.report(f"Time for 20 SEUs @ intensity {'{:.2e}'.format(i)} P/s ={round(seu_time, 3)} s[{round(seu_time/(60*60), 4)} hrs]")
    return seu_time_hr
      
def plot_HIT_parameters(data_name=None, file_name=None,seu_time_hr= None, ylim=4000, text_enable=True,PdfPages =None):
    data_frame = pd.read_csv(data_dir + data_name + "/LIBC HIT Version " + file_name + ".txt", delimiter='\s+', skiprows=1, header=None)
    data_frame.columns = ['E', 'E_MeV_u'] + [f'FWHM_{i}' for i in range(0, 6)] + [f'I_{i}' for i in range(0, 15)]     
    data_frame = check_last_row(data_frame = data_frame,file_name = file_name,column = f'I_0')
    logger.info("Plot Beam Intensities data at HIT")
    fig, ax1 = plt.subplots()
    #plt.hist(data['E_MeV_u'], bins=20, color='blue', edgecolor='black') 
    # Access and print FWHM values for each row
    # Print FWHM values for each row
    for index, row in data_frame.iterrows():
        #print(f'Row {index + 1}, I values: {row.iloc[9:].tolist()}')
        ax1.errorbar(range(0, len(row.iloc[8:])), row.iloc[8:], yerr=0.0, color=col_row[0], fmt='o' , markerfacecolor='black', markeredgecolor='black', ms=marker_size)
        ax1.plot(range(0, len(row.iloc[8:])), row.iloc[8:], color=col_row[1])
    ax1.ticklabel_format(useOffset=False)
    ax1.grid(True)
    #ax1.legend(loc="upper left", prop={'size': legend_font})
    intensities = ["I"+f'${i}$' for i in range(0, 15)]
    ax1.set_ylabel("Beam Intensity (Proton/s)", fontsize=label_font)
    ax1.set_xlabel("Category)", fontsize=label_font)
    ax1.set_xticks(range(len(intensities)))
    ax1.set_xticklabels(intensities)
    ax1.autoscale(enable=True, axis='x', tight=None)
    if text_enable: ax1.set_title("Beam Intensities at HIT (proton beam)", fontsize=text_font)
    plt.tight_layout()
    plt.yscale('log')
    plt.savefig(output_dir +data_name + "/9.LIBC HIT Version " + file_name + "_Intensity.png", bbox_inches='tight')  
    
    ax1.set_title("Beam Intensities at HIT (proton beam)", fontsize=text_font)
    plt.tight_layout()
    PdfPages.savefig()
    plt.clf()    
    #
    logger.info("Plot Beam FWHM data at HIT")
    fig2, ax2 = plt.subplots()
     # ax2 = plt.subplot(gs[1])   
    # Print FWHM values for each row
    for i in range(0, 5):
        ax2.errorbar(data_frame['E_MeV_u'], data_frame[f'FWHM_{i}'] , yerr=0.0 , color=col_row[i], fmt='-', markerfacecolor='black', markeredgecolor="black", ms=marker_size)
        ax2.plot(data_frame['E_MeV_u'], data_frame[f'FWHM_{i}'] , color=col_row[i], ms=marker_size, label=f'FWHM_{i}')
    ax2.ticklabel_format(useOffset=False)
    ax2.grid(True)
    ax2.legend(loc="upper left", prop={'size': legend_font})
    ax2.set_ylabel("Beam spot size FWHM (mm)", fontsize=label_font)
    ax2.set_xlabel("Energy (MeV/u)", fontsize=label_font)
    #ax2.set_xlim([0, 260])
    if text_enable: ax2.set_title("FWHM for 255 Energies at HIT (proton beam)", fontsize=text_font)   
    plt.tight_layout()
    plt.savefig(output_dir+data_name + "/9.LIBC HIT Version " + file_name + "_FWHM.png", bbox_inches='tight')
    ax2.set_title("FWHM for 255 Energies at HIT (proton beam)", fontsize=text_font) 
       
    plt.tight_layout()
    PdfPages.savefig()
    plt.clf()    
    #
    logger.info("Plot Time vs Intensity data at HIT")
    fig3, ax3 = plt.subplots()
     # ax3 = plt.subplot(gs[1])   
    # Print FWHM values for each row
    for index, row in data_frame.iterrows():
        ax3.errorbar(row.iloc[8:] ,seu_time_hr, yerr=0.0 , color=col_row[2], fmt='o', markerfacecolor='black', markeredgecolor="black", ms=marker_size)
        ax3.plot(row.iloc[8:] ,seu_time_hr, color=col_row[2], ms=marker_size)
    ax3.ticklabel_format(useOffset=False)
    ax3.grid(True)
    #ax3.legend(loc="upper left", prop={'size': legend_font})
    ax3.set_ylabel("Time needed (hr)", fontsize=label_font)
    ax3.set_xlabel("Beam Intensity (Proton/s)", fontsize=label_font)
    #ax3.set_xlim([0, 260])
    if text_enable: ax3.set_title("Time Needed for 20 SEUs at different intensities (proton beam)", fontsize=text_font)   
    plt.tight_layout()
    plt.xscale('log')
    plt.savefig(output_dir +data_name + "/9.LIBC HIT Version " + file_name + "_seu_time_intensity.png", bbox_inches='tight')
    logger.success("Saving information to "+output_dir+data_name + "/9.LIBC HIT Version ")   
    ax3.set_title("Time Needed for 20 SEUs at different intensities (proton beam)", fontsize=text_font) 
    plt.tight_layout()  
    PdfPages.savefig()
    plt.clf()    

# Main function
if __name__ == '__main__':    
    PdfPages = PdfPages(output_dir+'HIT_libc_data.pdf')
    logger.success("Opening PDF file:"+output_dir+'HIT_libc_data.pdf')
    basic_tests = ["1.4 p V11"]     
    for t in basic_tests:
        seu_time_hr = calculate_HIT_parameters(segma_litrature =6.99e-15, pp3_fluence = 2e-7,n_bits = 3e+3)
        logging.info("Plot HIT-libc_data", t)
        plot_HIT_parameters(data_name="HIT_libc_data",
                            file_name=t,
                            seu_time_hr = seu_time_hr,
                            PdfPages = PdfPages,
                            text_enable=False)
        
    PdfPages.close()
    