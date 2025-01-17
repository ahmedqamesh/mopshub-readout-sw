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
import matplotlib
from matplotlib import gridspec
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.cbook as cbook
import matplotlib.image as image
import matplotlib.pyplot as plt

rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from analysis_utils      import AnalysisUtils
from logger_main   import Logger
import logging
import pandas as pd
import csv
from celluloid import Camera
from scipy import interpolate
import math
from plot_style import *

log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="HIT data", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()
config_dir = rootdir+"/config_files/"
output_dir = rootdir+"/output_dir/"
data_dir = rootdir+"/data_files/"

path = os.path.abspath('') + '/'
logger.info('current working path: '+path)

def calculate_HIT_parameters(segma_litrature =None, pp3_fluence = None,n_bits = None,n_seu = None, exp_fluence = None):#segma_litrature[/cm^2/bit] & pp3_fluence [/cm^2/pp]& n_bits [per device]
    """
    Calculate parameters related to Single-Event Upset (SEU) rates and fluence.

    Args:
        segma_litrature (float): SEU cross-section from literature, given in [/cm^2/bit].
        pp3_fluence (float): Fluence at PP3, given in [/cm^2/pp].
        n_bits (int): Number of bits per device.
        n_seu (int): Number of SEUs.

    Returns:
        list: SEU time in hours for each intensity value.
    """
    logger.report(f"Literature value for SEU cross section = {segma_litrature}") 
    pp3_fluence = pp3_fluence* 40e+6*3.14e+7
    n_seu_expected = segma_litrature * pp3_fluence *n_bits
    logger.report(f"N SEUs expected at PP3 [fluence = {'{:.2e}'.format(pp3_fluence)} /cm^2] = {n_seu_expected}") 
    exp_sigma = n_seu /(exp_fluence * n_bits)
    logger.report(f"Experimental Sigma [fluence = {exp_fluence} in {n_bits} bits SR]= {'{:.2e}'.format(exp_sigma)}/cm^2") 
    
    #Fluence: The number of particles per area, given in [cm^-2].
    needed_fluence = n_seu /(segma_litrature * n_bits)
    logger.report(f"Facility fluence [SEUs = {n_seu} in {n_bits} bits SR]= {'{:.2e}'.format(needed_fluence)}/cm^2") 
    
    # the intensity or flux of radiant energy is the power transferred per unit area (flux = fluence * time)
    intensity = [8.0e+07,1.2e+08 ,2.0e+08 ,3.2e+08 ,4.0e+08, 6.0e+08, 8.0e+08, 1.2e+09 ,2.0e+09 ,3.2e+09 ,4.0e+09 ,6.0e+09, 8.0e+09, 1.2e+10, 2.0e+10]
    seu_time_hr = []
    for i in intensity:
        seu_time = needed_fluence/i
        seu_time_hr = np.append(seu_time_hr,seu_time/(60*60))
        #logger.report(f"Time for {n_seu} SEUs @ intensity {'{:.2e}'.format(i)} P/s ={round(seu_time, 3)} s[{round(seu_time/(60*60), 4)} hrs]")
    #for s in seu_time_hr: print (f" & {round(s, 3)}", end='')
    return seu_time_hr,needed_fluence

    
def plot_HIT_parameters(file_path=None, ylim=4000, text_enable=True,PdfPages =None):
    data_frame = pd.read_csv(file_path, delimiter='\s+', skiprows=1, header=None)
    file_name = os.path.basename(file_path)
    file_directory = os.path.dirname(file_path)
    data_frame.columns = ['E', 'E_MeV_u'] + [f'FWHM_{i}' for i in range(0, 6)] + [f'I_{i}' for i in range(0, 15)]     
    data_frame = AnalysisUtils().check_last_row(data_frame = data_frame,file_name = file_name,column = f'I_0')
    logger.info("Plot Beam Intensities data at HIT")
    fig, ax1 = plt.subplots()
    #plt.hist(data['E_MeV_u'], bins=20, color='blue', edgecolor='black') 
    # Access and print FWHM values for each row
    # Print FWHM values for each row
    for index, row in data_frame.iterrows():
        #print(f'Row {index + 1}, I values: {row.iloc[9:].tolist()}')
        I_category = range(0, len(row.iloc[8:]))
        
        spline = interpolate.splrep(I_category, row.iloc[8:], s=None, k=2)  # create spline interpolation
        xnew = np.linspace(np.min(I_category), np.max(I_category), num=50, endpoint=True)
        spline_eval = interpolate.splev(xnew, spline)  # evaluate spline
        
        ax1.errorbar(I_category, row.iloc[8:], yerr=0.0, color=col_row[0], fmt='o' , markerfacecolor='black', markeredgecolor='black')
        ax1.plot(xnew, spline_eval)
        
    ax1.ticklabel_format(useOffset=False)
    ax1.grid(True)
    #ax1.legend(loc="upper left")
    intensities = ["I"+f'${i}$' for i in range(0, 15)]
    ax1.set_ylabel("Beam Intensity (Proton/s)")
    ax1.set_xlabel("Category")
    ax1.set_xticks(range(len(intensities)))
    ax1.set_xticklabels(intensities)
    ax1.autoscale(enable=True, axis='x', tight=None)
    if text_enable: ax1.set_title("Beam Intensities at HIT (proton beam)", fontsize=text_font)
    plt.tight_layout()
    #plt.yscale('log')
    plt.savefig(file_path[:-4]+"_Intensity.pdf", bbox_inches='tight')  
    
    ax1.set_title("Beam Intensities at HIT (proton beam)")
    plt.tight_layout()
    PdfPages.savefig()
    plt.clf()    
    #
    logger.info("Plot Beam FWHM data at HIT")
    fig2, ax2 = plt.subplots()
     # ax2 = plt.subplot(gs[1])   
    # Print FWHM values for each row
    for i in range(0, 5):
        spline = interpolate.splrep(data_frame['E_MeV_u'], data_frame[f'FWHM_{i}'], s=10, k=2)  # create spline interpolation
        xnew = np.linspace(np.min(data_frame['E_MeV_u']), np.max(data_frame['E_MeV_u']), num=50, endpoint=True)
        spline_eval = interpolate.splev(xnew, spline)  # evaluate spline
        #ax2.errorbar(data_frame['E_MeV_u'], data_frame[f'FWHM_{i}'] , yerr=0.0, fmt='o', markerfacecolor='black', markeredgecolor="black")
        ax2.plot(xnew, spline_eval, "-", label=f'FWHM_{i}')
    ax2.ticklabel_format(useOffset=False)
    ax2.grid(True)
    ax2.legend(loc="upper left")
    ax2.set_ylabel("Beam spot size FWHM ([mm])")
    ax2.set_xlabel("Energy ([MeV/u])")
    #ax2.set_xlim([0, 260])
    if text_enable: ax2.set_title("FWHM for 255 Energies at HIT (proton beam)")  
    plt.tight_layout()
    plt.savefig(file_path[:-4]+"_FWHM.pdf", bbox_inches='tight')
    ax2.set_title("FWHM for 255 Energies at HIT (proton beam)")
       
    plt.tight_layout()
    PdfPages.savefig()
    plt.clf()    
    #
    logger.info("Plot Time vs Intensity data at HIT")
    fig3, ax3 = plt.subplots()
    for index, row in data_frame.iterrows():
        Intensity = row.iloc[8:]
    n_seu_array = np.arange(10,110,10)
    needed_fluence = []
    for seu in n_seu_array:
        seu_time_hr_array,_fluence  = calculate_HIT_parameters(segma_litrature =3.75e-15, pp3_fluence = 2e-7,n_bits = 3e+3,n_seu = seu, exp_fluence = 2e-7)
        needed_fluence = np.append(needed_fluence, _fluence)
        spline = interpolate.splrep(Intensity, seu_time_hr_array, s=10, k=2)  # create spline interpolation
        xnew = np.linspace(np.min(Intensity), np.max(Intensity), num=50, endpoint=True)
        spline_eval = interpolate.splev(xnew, spline)  # evaluate spline
        
        ax3.errorbar(Intensity,seu_time_hr_array, yerr=0.0, fmt='o', markerfacecolor='black', markeredgecolor="black")
        ax3.plot(Intensity,seu_time_hr_array,label=f'{seu} SEUs')

    ax3.ticklabel_format(useOffset=False)
    ax3.grid(True)
    ax3.legend(loc="upper right")
    ax3.set_ylabel("Time needed [h]")
    ax3.set_xlabel("Beam Intensity [Proton/s]")
    #ax3.set_xlim([0, 260])
    if text_enable: ax3.set_title("Time Needed for N SEUs at different intensities (proton beam)")  
    plt.tight_layout()
    ax3.set_xscale('log')
    fig3.savefig(file_path[:-4]+"_seu_time_intensity.pdf", bbox_inches='tight')
    logger.success("Saving information to "+file_directory)   
    ax3.set_title("Time Needed for N SEUs at different intensities (proton beam)")
    plt.tight_layout()  
    PdfPages.savefig()
    plt.clf()    
    
    logger.info("Plot SEU vs Expected Fluence at HIT")
    fig4, ax4 = plt.subplots()
    ax4.errorbar(n_seu_array,needed_fluence, yerr=0.0, fmt='o', markerfacecolor='black', markeredgecolor="black")
    ax4.plot(n_seu_array,needed_fluence,label=f'SEUs')
    ax4.ticklabel_format(useOffset=False)
    ax4.grid(True)
    ax4.legend(loc="upper left")
    ax4.set_xlabel("N. SEUs")
    ax4.set_ylabel("Needed Fluence [/cm^2]")
    #ax4.set_xlim([0, 260])
    if text_enable: ax4.set_title("Time Needed for N SEUs at different intensities (proton beam)")  
    plt.tight_layout()
    #ax4.set_xscale('log')
    fig4.savefig(file_path[:-4]+"_seu_expected_fluence.pdf", bbox_inches='tight')
    logger.success("Saving information to "+file_directory)   
    ax4.set_title("Time Needed for N SEUs at different intensities (proton beam)")
    plt.tight_layout()  
    PdfPages.savefig()
    plt.clf()    
            
# Main function
if __name__ == '__main__':    
    PdfPages = PdfPages(output_dir+'HIT_libc_data.pdf')
    logger.success("Opening PDF file:"+output_dir+'HIT_libc_data.pdf')
    basic_tests = ["1.4 p V11"]    
    seu_time_hr,needed_fluence = calculate_HIT_parameters(segma_litrature =6.99e-15, pp3_fluence = 2e-7,n_bits =  3e+3,n_seu = 4, exp_fluence =  4e11) 
    for t in basic_tests:
        seu_time_hr,needed_fluence = calculate_HIT_parameters(segma_litrature =6.99e-15, pp3_fluence = 2e-7,n_bits = 3e+3,n_seu = 100, exp_fluence = 2e-7)
        logging.info("Plot HIT-libc_data", t)
        file_path = data_dir + "HIT_libc_data/LIBC HIT Version " + t + ".txt"
        plot_HIT_parameters(file_path=file_path,
                            PdfPages = PdfPages,
                            text_enable=False)
        
    PdfPages.close()
    