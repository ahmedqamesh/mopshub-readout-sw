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
import matplotlib
import math
import random
import re
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from logger_main   import Logger
import analyze_HIT_libc_data
import analyze_vivado_ip_results
import analyze_debug_results
import logging

log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="UHAL Data", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()
config_dir = rootdir+"/config_files/"
output_dir = rootdir+"/output_dir/"

# get curret working path
path = os.path.abspath('') + '/'
logger.info('current working path: '+path)

plot_h, plot_w = 6, 4
text_font, label_font , legend_font, marker_size = 12, 10, 8, 4
col_row = ['black','darkred', 'darkgreen', 'blue', 'indigo', 'olive', 'gray', 'lightsteelblue', 'darkorange', '#a6cee3','darksalmon', "slateblue"]
matplotlib.rcParams['lines.markersize'] = marker_size
# Set plot dimensions 
matplotlib.rcParams['figure.figsize'] = (plot_h, plot_w)  # Adjust the width and height as needed
# Set label font size
matplotlib.rcParams['axes.labelsize'] = label_font

# Set legend font size
matplotlib.rcParams['legend.fontsize'] = legend_font
# Set text font size
matplotlib.rcParams['font.size'] = text_font  # You can adjust the size as needed


def get_color(i):
    col_row = ["#000000", "#3a3487", "#f7e5b2", "b", "g", "r", "y", "c", "m", "lime", "#943ca6", "#df529e", "#f49cae", "tab:blue",
            "tab:orange", "tab:purple", "tab:pink", "#332d58", "#3b337a", "#365a9b", "#2c4172", "#2f3f60", "#3f5d92",
            "#4e7a80", "#60b37e", "darkgoldenrod", "darksalmon", "darkgreen", "#904a5d", "#5d375a", "#4c428d", "#31222c", "#b3daa3","#f4ce9f", "#ecaf83"]
    return col_row[i]

def check_last_row (data_frame = None, file_name = None,column = "status"):
    data_frame_last_row = data_frame.tail(1)
    
    pattern_exists = any(data_frame_last_row[column].astype(str).str.contains("End of Test"))
    if pattern_exists: 
        logger.notice(f"Noticed a Complete test file named: {file_name}") 
        data_frame = data_frame.iloc[:-1]
    else: logger.warning(f"Noticed Incomplete test file")    
    return data_frame

def plot_matches_time(file_name = "Configuration_pattern.csv",test = "test_rx",text_enable = True,output_dir= None):
    fig, ax = plt.subplots()
    data_frame = pd.read_csv(file_name,encoding = 'utf-8', dtype='unicode').fillna(0)
    data_frame["elabsed_time"] = pd.to_numeric(data_frame.elabsed_time)
    data_frame = check_last_row(data_frame = data_frame,file_name = file_name)
    #data_frame["respmsg"] = [float(value)  for value in data_frame["elabsed_time"]]
    match_msg_cond    =(data_frame[test]==str(1)) & (data_frame["reqmsg"]==str(1)) & (data_frame["respmsg"]==str(1))
    mismatch_msg_cond =(data_frame[test]==str(1)) & (data_frame["reqmsg"]==str(1)) & (data_frame["respmsg"]==str(0))
    ax.plot(data_frame.loc[match_msg_cond]["elabsed_time"],data_frame.loc[match_msg_cond]["status"],label="Matches")    
    ax.plot(data_frame.loc[mismatch_msg_cond]["elabsed_time"],data_frame.loc[mismatch_msg_cond]["status"],label="Mismatches") 
    ax.legend(loc="upper left", prop={'size': legend_font})
    ax.set_ylabel('Status',fontsize=label_font)
    ax.set_xlabel('Elapsed Time [S]',fontsize=label_font)
    logger.info(f"Plot Matches during Communications in [{data_frame.shape[0]} Messages]")
    ax.set_ylim([-0.5,1])
    if text_enable: ax.set_title(f"Matches during Communications in [{data_frame.shape[0]} Messages]", fontsize=text_font)
    plt.grid(True)
    plt.tight_layout()
    plt.tick_params(axis='both', which='both', direction="in", bottom=True, top=True)
    plt.savefig( output_dir+"plot_matches_time.png", bbox_inches='tight')
    logger.success("Save Matches plot to " + output_dir+"plot_matches_time.png")
    ax.set_title("Message Matches", fontsize=text_font)
    plt.tight_layout()
    PdfPages.savefig()
    plt.clf() 
    
def plot_adc(file_name = None, nodeId = [0], bus_id = [1], xlimit = 200, ylimit = 1,text_enable = True,output_dir =None):
    data_frame = pd.read_csv( file_name, delimiter=",", header=0,encoding = 'utf-8',low_memory=False)
    n_channels = 32
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
                #plt.suptitle('MOPS (NodeId = %i & bus = %i]'%(node,bus) ,fontsize=label_font)
                # plt.errorbar(respondant[respondant["nodeId" ]== node]["elabsed_time"],
                #              respondant[respondant["nodeId" ]== node]["adc_data_converted"]*1000,
                #              ms=marker_size,
                #              color =get_color(target),
                #              fmt='.k')
                ax.plot(respondant[respondant["nodeId" ]== node]["elabsed_time"],respondant[respondant["nodeId" ]== node]["adc_data_converted"]*1000, 
                        label="ADC channel No.%i"%target, color =get_color(target), ms=marker_size)
                ax.ticklabel_format(useOffset=False)
                ax.legend(loc="upper left", prop={'size': legend_font})
                ax.autoscale(enable=True, axis='x', tight=None)
                ax.grid(True)
                ax.set_ylabel(r'ADC value [mV]',fontsize=label_font)
                ax.set_xlabel("Elapsed Time [s]",fontsize=label_font)
                if text_enable: ax.set_title('MOPS (NodeId = %i & bus = %i]'%(node,bus) , fontsize=text_font)
                plt.tight_layout()
                plt.savefig(output_dir+'/mopshub_buses_test_bus%i_node%i_channel%s.png'%(bus,node,target), bbox_inches='tight')
                if xlimit: ax.set_xlim([0,xlimit])
                logger.info("Plot data from channel %i for node %i[Max time = %d s]"%(target, node,ax.get_xlim()[1]))
                if ylimit: ax.set_ylim([0,ylimit])
                ax.set_title('MOPS (NodeId = %i & bus = %i]'%(node,bus) , fontsize=text_font)
                plt.tight_layout()
                PdfPages.savefig()
                plt.clf() 
                plt.close(fig)
    logger.success("Save MOPSHUB Data plots to " + output_dir)


def plot_can_compare_bar(file_name = "Configuration_pattern.csv",test = "test_rx",text_enable = True,output_dir = None):
    num = re.findall(r'\d+', file_name) 
    fig, ax = plt.subplots()
    reqmsg_append = []
    respmsg_append=[]
    status_array = []
    data_frame = pd.read_csv(file_name,encoding = 'utf-8', dtype='unicode').fillna(0)
    data_frame = check_last_row(data_frame = data_frame, file_name = file_name)
    
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
    ax.bar(np.arange(-0.25, len(bus_array)-0.25), reqmsg_append,color = col_row[7],  width = 0.5, label="Responded Messages (RX)")
    ax.bar(x_bins , respmsg_append , color = col_row[11], width = 0.4,label="Requested Messages (TX)")
    bbox_props = dict(boxstyle="round", facecolor="wheat", alpha=0.95)
    ax.text(0.60, 0.85, f"Run Duration={round(time_stamp,5)} Sec\n No. of Buses={len(bus_array)},\n No. of Messages ={n_messages[0]}", size=legend_font,                  
            ha='left', va='center', transform=ax.transAxes, bbox=bbox_props)
    ax.set_xticks(x_bins)
    ax.set_xticklabels([],fontsize=label_font,rotation=60)
    ax.set_ylabel('# Messages',fontsize=label_font)
    ax.set_xlabel('Bus ID',fontsize=label_font)
    
    ax.legend(loc="upper left", prop={'size': legend_font})
    colors = ["r" for i in x_bins]
    for c in np.arange(0, len(status_array)):
        if bus_array[c] == 1: colors[c] = "r"
        else: colors[c] = "g"    
    # ax2.errorbar(x_bins, eff, yerr=0.0, fmt='o-', color=col_row[7], label='Communication Efficiency')
    # ax2.spines['right'].set_position(('outward', 1))
    # ax2.set_xticks(x_bins)
    ax.set_xticklabels(["Bus"+x for x in bus_array],fontsize=label_font)
    # ax2.set_ylabel('Efficiency',fontsize=label_font)
    # ax2.grid()
    colorax = ax.twiny()
    colorax.xaxis.set_ticks_position('bottom') # set the position of the second x-axis to bottom
    colorax.xaxis.set_label_position('bottom') # set the position of the second x-axis to bottom
    colorax.spines['bottom'].set_position(('outward', 50))
    colorax.set_xticks(x_bins)
    symbolsx = ["⚫" for i in x_bins]
    colorax.set_xticklabels(symbolsx,fontsize=label_font)
    colorax.set_xlim(ax.get_xlim())
    for tick, color in zip(colorax.get_xticklabels(), colors): tick.set_color(color)  
    if text_enable: ax.set_title(f'MOPSHUB messages Statistics [{n_messages[0]} Messages]', fontsize=text_font)
    plt.tight_layout()
    plt.savefig((output_dir+f'mopshub_%s_messages_matches_bus_activity.png'%num[6]))
    ax.set_title(f'MOPSHUB messages Statistics [{n_messages[0]} Messages]', fontsize=text_font)
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
    if text_enable: ax.set_title(f'plt_mopshub_grid', fontsize=text_font)
    plt.tight_layout()
    plt.savefig((output_dir+f'/%s.png'%file_name))
    
    PdfPages.savefig()
    plt.close(fig)

###############################################################################################
def parameterhelp():
    ##
    # print help text for program
    print ("Usage: python Analyse_mopshub_results.py [-h] <Folder/to/data>")
    print ("-h : help")
    print ("-v : Analyze chip voltages")
    print ("-r : Analyze PSPP registers and ADCs (not valid for MOPSHUB)")
    print ("--all : perform all analysis")
    print ("Argument: path to folder with data")
     
# Main function
if __name__ == '__main__':
    # get program arguments
    PdfPages = PdfPages(output_dir+'mopshub_uhal_test.pdf')
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
        file_date = "2024-02-01_17:36:35"
        file_debug_date = "2024-02-05_19:23:59"
        file_vivado_date = "2024-02-01_17:36:35"
        xadc_files = [output_dir+file_vivado_date+"_vivado/"+file_vivado_date+"_hw_xadc_data_file.csv"]
        ila_files = [output_dir+file_vivado_date+"_vivado/"+file_vivado_date+"_hw_ila_data_file.csv"]
        debug_files =[output_dir+file_debug_date+"_debug/"+file_debug_date+"_mopshub_top_16bus_debug.csv"]
        file_uhal =output_dir+file_date+"_uhal/"+file_date+"_mopshub_top_16bus_seu_test.csv"
        print('------------------------------------------------------------')    
        analyze_debug_results.plot_debug_time(file_names=debug_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_debug_date+"_debug/")
        print('------------------------------------------------------------')
        plot_can_compare_bar(file_name=file_uhal,test = "test_tx",output_dir = output_dir+"/"+file_date+"_uhal/")
        plot_matches_time(file_name=file_uhal,test = "test_tx",output_dir = output_dir+file_date+"_uhal/")
        #plot_adc(file_name =file_uhal, bus_id= [0], nodeId = [0], xlimit = False,ylimit = False,output_dir = output_dir+file_date+"_uhal/")
        print('------------------------------------------------------------')
        basic_tests = ["1.4 p V11"]     
        for t in basic_tests:
            seu_time_hr = analyze_HIT_libc_data.calculate_HIT_parameters(segma_litrature =6.99e-15, pp3_fluence = 2e-7,n_bits = 3e+3)
            analyze_HIT_libc_data.plot_HIT_parameters(data_name="HIT_libc_data",
                                file_name=t,
                                seu_time_hr = seu_time_hr,
                                PdfPages=PdfPages,
                                text_enable=False)
        
        print('------------------------------------------------------------')
        analyze_vivado_ip_results.plot_xadc_data(file_names=xadc_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_vivado_date+"_vivado/")
        analyze_vivado_ip_results.plot_ila_data(file_names=ila_files,PdfPages=PdfPages,text_enable =True,output_dir = output_dir+file_vivado_date+"_vivado/")
    else: 
        pass    
        
    PdfPages.close()


