########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
import numpy as np
import os
import sys, getopt
from matplotlib import gridspec
import matplotlib.cbook as cbook
import matplotlib.image as image
from matplotlib.ticker import ScalarFormatter
from scipy import interpolate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import pandas as pd
import csv
import glob
import matplotlib
import math
import random
import re
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from logger_main   import Logger
from analysis_utils      import AnalysisUtils
import analyze_HIT_libc_data
import analyze_vivado_ip_results
import analyze_debug_results
import logging
from plot_style import *

log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="Analyzer", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()
config_dir = rootdir+"/config_files/"
output_dir = rootdir+"/output_dir/"

# get curret working path
path = os.path.abspath('') + '/'
logger.info('current working path: '+path)

def extract_last_directory(folder_path):
    folders = next(os.walk(folder_path))[1]
    last_folder = folders[-1] if folders else None
    logger.info("The last directory is "+str(last_folder))
    return last_folder

def find_csv_files_in_folder(folder_path):
    # Construct the search pattern
    #all_files = os.listdir(folder_path)    
    #csv_files = list(filter(lambda f: f.endswith('.csv'), all_files))
   
    search_pattern = os.path.join(folder_path, "*.csv")
    # Use glob to find files matching the search pattern
    csv_files = glob.glob(search_pattern)
    return csv_files

def plot_matches_time(file_name = "Configuration_pattern.csv",test = "test_rx",text_enable = True,output_dir= None):
    fig, ax = plt.subplots()
    data_frame = pd.read_csv(file_name,encoding = 'utf-8', dtype='unicode').fillna(0)
    data_frame["elabsed_time"] = pd.to_numeric(data_frame.elabsed_time)
    data_frame = AnalysisUtils().check_last_row(data_frame = data_frame,file_name = file_name)
    #data_frame["respmsg"] = [float(value)  for value in data_frame["elabsed_time"]]
    match_msg_cond    =(data_frame[test]==str(1)) & (data_frame["reqmsg"]==str(1)) & (data_frame["respmsg"]==str(1))
    mismatch_msg_cond =(data_frame[test]==str(1)) & (data_frame["reqmsg"]==str(1)) & (data_frame["respmsg"]==str(0))
    ax.plot(data_frame.loc[match_msg_cond]["elabsed_time"],data_frame.loc[match_msg_cond]["status"],label="Matches")    
    ax.plot(data_frame.loc[mismatch_msg_cond]["elabsed_time"],data_frame.loc[mismatch_msg_cond]["status"],label="Mismatches") 
    ax.legend(loc="upper left")
    ax.set_ylabel('Status')
    ax.set_xlabel('Elapsed Time [S]')
    logger.info(f"Plot Matches during Communications in [{data_frame.shape[0]} Messages]")
    ax.set_ylim([-0.5,1])
    if text_enable: ax.set_title(f"Matches during Communications in [{data_frame.shape[0]} Messages]")
    plt.grid(True)
    plt.tight_layout()
    plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
    plt.savefig( output_dir+"plot_matches_time.pdf", bbox_inches='tight')
    logger.success("Save Matches plot to " + output_dir+"plot_matches_time.pdf")
    ax.set_title("Message Matches")
    plt.tight_layout()
    PdfPages.savefig()
    plt.clf() 
    
def plot_adc(file_name = None, nodeId = [0], bus_id = [1], xlimit = 200, ylimit = 1,text_enable = True,output_dir =None, n_channels = 32):
    data_frame = pd.read_csv( file_name, delimiter=",", header=0,encoding = 'utf-8',low_memory=False)
    _start_a = 3  # to ignore the first subindex it is not ADC
    data_frame['Times'] = pd.to_datetime(data_frame['Times'])
    data_frame = check_last_row(data_frame = data_frame, file_name = file_name)
    #data_frame['Seconds'] = (data_frame['Times'] - data_frame['Times'].min()).dt.total_seconds()
    
    for bus in bus_id:
        for node in nodeId:
            for target in np.arange(_start_a,n_channels+_start_a):
                fig, ax = plt.subplots()
                condition = (data_frame["adc_ch"] == target)  & (data_frame["bus_id"] == bus)
                respondant = data_frame[condition]
                #plt.suptitle('MOPS (NodeId = %i & bus = %i]'%(node,bus) )
                # plt.errorbar(respondant[respondant["nodeId" ]== node]["elabsed_time"],
                #              respondant[respondant["nodeId" ]== node]["adc_data_converted"]*1000,
                #              ms=marker_size,
                #              fmt='.k')
                ax.plot(respondant[respondant["nodeId" ]== node]["elabsed_time"],respondant[respondant["nodeId" ]== node]["adc_data_converted"]*1000, 
                        label="ADC channel No.%i"%target)
                ax.ticklabel_format(useOffset=False)
                ax.legend(loc="upper left")
                ax.autoscale(enable=True, axis='x', tight=None)
                ax.grid(True)
                ax.set_ylabel(r'ADC value [mV]')
                ax.set_xlabel("Elapsed Time [s]")
                if text_enable: ax.set_title('MOPS (NodeId = %i & bus = %i]'%(node,bus) )
                plt.tight_layout()
                plt.savefig(output_dir+'/mopshub_buses_test_bus%i_node%i_channel%s.pdf'%(bus,node,target), bbox_inches='tight')
                if xlimit: ax.set_xlim([0,xlimit])
                logger.info("Plot data from channel %i for node %i[Max time = %d s]"%(target, node,ax.get_xlim()[1]))
                if ylimit: ax.set_ylim([0,ylimit])
                ax.set_title('MOPS (NodeId = %i & bus = %i]'%(node,bus) )
                plt.tight_layout()
                PdfPages.savefig()
                plt.clf() 
                plt.close(fig)
    logger.success("Save MOPS-Hub Data plots to " + output_dir)


def plot_can_compare_bar(file_name = "Configuration_pattern.csv",test = "test_rx",text_enable = None,output_dir = None):
    num = re.findall(r'\d+', file_name) 
    fig, ax = plt.subplots()
    reqmsg_append = []
    respmsg_append=[]
    status_array = []
    data_frame = pd.read_csv(file_name,encoding = 'utf-8', dtype='unicode').fillna(0)
    data_frame = AnalysisUtils().check_last_row(data_frame = data_frame, file_name = file_name)
    
    data_frame["elabsed_time"] = pd.to_numeric(data_frame.elabsed_time)
    n_buses = (data_frame[data_frame["bus_id"].duplicated() ==False])
    n_messages= data_frame["reqmsg" ].value_counts()
    logger.info(f'analyze messages Statistics [{n_messages[0]} Messages]')
    bus_array = [str(x) for x in n_buses["bus_id"]] 
    x_bins = np.arange(0, len(bus_array))
    time_stamp  = (data_frame["elabsed_time"].max()- data_frame["elabsed_time"].min()) *10**-9 

    for i in n_buses["bus_id"]:    
        # pick condition fro req and resp
        req_msg_cond    = np.where((data_frame["bus_id"]==str(i)) & (data_frame[test]==str(1)) & (data_frame["reqmsg"]==str(1)))
        resp_msg_cond   = np.where((data_frame["bus_id"]==str(i)) & (data_frame[test]==str(1)) & (data_frame["respmsg"]==str(1)))
        status_cond     = np.where((data_frame["bus_id"]==i) & (data_frame[test]==str(1)))
        cond_bus_reqmsg  = (data_frame.loc[req_msg_cond ]["reqmsg" ].value_counts())
        cond_bus_respmsg = (data_frame.loc[resp_msg_cond]["respmsg"].value_counts())            
        cond_bus_status  = (data_frame.loc[status_cond  ]["status" ].value_counts())            
        #append the results
        reqmsg_append = np.append(reqmsg_append,cond_bus_reqmsg) 
        respmsg_append = np.append(respmsg_append,cond_bus_respmsg)   
                  
        if (cond_bus_reqmsg.tolist() == cond_bus_respmsg.tolist()): status_array = np.append(status_array,1) 
        else: status_array = np.append(status_array,0) 
        eff = np.divide(respmsg_append, reqmsg_append) *100
        logger.report(f"Bus:[{i}]: Request Msg[{reqmsg_append[0]}]- Response Msg[{respmsg_append[0]}]- Efficiency[{eff[0]}]")
    
    logger.report(f'Total Passed Msg:{data_frame[data_frame["status"]==str(1)].shape[0]}- Total Failed Msg:{data_frame[data_frame["status"]==str(0)].shape[0]}')
    ax.grid()
    ax.bar(np.arange(-0.25, len(bus_array)-0.25), reqmsg_append, edgecolor = 'black', color ="xkcd:lavender",  width = 0.5, label="Responded Messages (RX)")
    ax.bar(x_bins , respmsg_append , width = 0.4, edgecolor = 'black', color ="lavender",label="Requested Messages (TX)")
    
    bbox_props = dict(boxstyle="round", facecolor="wheat", alpha=0.75)
    ax.text(0.60, 0.75, f"No. of Buses={len(bus_array)}\n No. of Messages ={n_messages[0]}",    #Run Duration={round(time_stamp,5)} Sec\n               
            ha='left', va='center', transform=ax.transAxes, bbox=bbox_props)
    ax.set_xticks(x_bins)
    ax.set_xticklabels([],rotation=60)
    ax.set_ylabel('# Messages')
    ax.set_xlabel('Bus ID')
    
    ax.legend(loc="upper left")
    colors = ["r" for i in x_bins]
    for c in np.arange(0, len(status_array)):
        if bus_array[c] == 1: colors[c] = "r"
        else: colors[c] = "g"    
    # ax2.errorbar(x_bins, eff, yerr=0.0, fmt='o-', color=col_row[7], label='Communication Efficiency')
    # ax2.spines['right'].set_position(('outward', 1))
    # ax2.set_xticks(x_bins)
    ax.set_xticklabels(["Bus"+x for x in bus_array])
    # ax2.set_ylabel('Efficiency')
    # ax2.grid()
    colorax = ax.twiny()
    colorax.xaxis.set_ticks_position('bottom') # set the position of the second x-axis to bottom
    colorax.xaxis.set_label_position('bottom') # set the position of the second x-axis to bottom
    colorax.spines['bottom'].set_position(('outward', 60))
    colorax.set_xticks(x_bins)
    symbolsx = ["⚫" for i in x_bins]
    colorax.set_xticklabels(symbolsx)
    colorax.set_xlim(ax.get_xlim())
    for tick, color in zip(colorax.get_xticklabels(), colors): tick.set_color(color)  
    if text_enable: ax.set_title(f'MOPS-Hub messages Statistics [{n_messages[0]} Messages]')
    plt.tight_layout()
    plt.savefig((output_dir+f'mopshub_%s_messages_matches_bus_activity.pdf'%num[6]))
    ax.set_title(f'MOPS-Hub messages Statistics [{n_messages[0]} Messages]')
    plt.tight_layout()
    PdfPages.savefig()
    plt.close(fig)

def plt_mopshub_grid(file_name = "file_name",text_enable = True,output_dir =None):
    fig = plt.figure()
    logger.info("Plot Grid iNFO")
    ax = fig.add_subplot(111)
    data2D = np.random.random((50, 50))
    im = plt.imshow(data2D, cmap=plt.cm.get_cmap('viridis', 6))
    plt.colorbar(im)
    if text_enable: ax.set_title(f'plt_mopshub_grid')
    plt.tight_layout()
    plt.savefig((output_dir+f'/%s.pdf'%file_name))
    
    PdfPages.savefig()
    plt.close(fig)

###############################################################################################
def parameterhelp():
    ##
    # print help text for program
    print ("Usage: python Analyse_mopshub_results.py [-h] <Folder/to/data>")
    print ("-h : help")
    print ("-v : Analyze chip voltages")
    print ("-r : Analyze PSPP registers and ADCs (not valid for MOPS-Hub)")
    print ("--all : perform all analysis")
    print ("Argument: path to folder with data")
     
# Main function
if __name__ == '__main__':
    # get program arguments
    PdfPages = PdfPages(output_dir+'mopshub_campaign_test.pdf')
    logger.success("Opening PDF file:"+output_dir+'mopshub_uhal_test.pdf')
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hdrvt",["help","all"])
    except getopt.GetoptError:
        logger.warning("Wrong parameter given")
        parameterhelp()
        exit()
        
    analyzeHit = False
    analyzeDebug = False
    analyzeUhal = False
    analyzedefined = False
    # parse arguments
    for opt,arg in opts:
        if opt in ("-h","--help"):
            parameterhelp()
            exit()
        if opt in ("-d"):
            analyzeDebug = True
            logger.notice("Debug Data analysis is active")
        if opt in ("-u"):
            analyzeUhal = True
            logger.notice("UHAL Data analysis is active")
        if opt in ("-hit"):
            analyzeHit = True
            logger.notice("HIT Data analysis is active")
        if opt in ("-t"):
            analyzeTest = True
            logger.notice("Debug active")
        if opt in ("--all"):
            logger.notice("Full Data analysis is active")
            analyzeDebug = True
            analyzeUhal  = True
            analyzeHit   = True
            analyzeTest  = True
    if len(args) < 1:
        logger.error("No argument given! Need path to data folder")
        logger.info("GO with the predefined settings")
        analyzedefined = True
    logger.info("checking test directory"+str(args))
       
    if analyzedefined == True:
        last_test_directory = extract_last_directory(output_dir)
        #file_uhal_date = last_test_directory     
        file_uhal_date = "2024-02-01_17:36:35"
        file_debug_date = "2024-02-05_19:23:59"
        file_vivado_date = "2024-02-01_17:36:35"
        xadc_files = [output_dir+file_vivado_date+"_vivado/"+file_vivado_date+"_hw_xadc_data_file.csv"]
        ila_files = [output_dir+file_vivado_date+"_vivado/"+file_vivado_date+"_hw_ila_data_file.csv"]
        debug_files =[output_dir+file_debug_date+"_debug/"+file_debug_date+"_mopshub_top_16bus_debug.csv"]
        
        #file_uhal =output_dir+file_uhal_date+"_uhal/"+file_uhal_date+"_mopshub_top_16bus.csv"
        file_uhal =output_dir+file_uhal_date+"_uhal/"+file_uhal_date+"_mopshub_top_16bus_seu_test.csv"
        #file_uhal = find_csv_files_in_folder(output_dir+last_test_directory)[0]
        print('------------------------------------------------------------')    
        analyze_debug_results.plot_debug_time(file_names=debug_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_debug_date+"_debug/")
        print('------------------------------------------------------------')
        plot_can_compare_bar(file_name=file_uhal,test = "test_tx",output_dir = output_dir+"/"+file_uhal_date+"_uhal/")
        plot_matches_time(file_name=file_uhal,test = "test_tx",output_dir = output_dir+file_uhal_date+"_uhal/")
        plot_adc(file_name ="file_uhal", bus_id= [0], nodeId = [0], xlimit = False,ylimit = False,output_dir = output_dir+file_uhal_date+"_uhal/",n_channels = 2)
        print('------------------------------------------------------------')
        basic_tests = ["1.4 p V11"]     
        for t in basic_tests:
            seu_time_hr = analyze_HIT_libc_data.calculate_HIT_parameters(segma_litrature =6.99e-15, pp3_fluence = 2e-7,n_bits = 3e+3,n_seu = 20)
            analyze_HIT_libc_data.plot_HIT_parameters(data_name="HIT_libc_data",
                                file_name=t,
                                PdfPages=PdfPages,
                                text_enable=False)
        
        print('------------------------------------------------------------')
        #analyze_vivado_ip_results.plot_xadc_data(file_names=xadc_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_vivado_date+"_vivado/")
        #analyze_vivado_ip_results.plot_ila_data(file_names=ila_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_vivado_date+"_vivado/")
    else: 
        pass    
        
    PdfPages.close()


