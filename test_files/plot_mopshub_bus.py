import numpy as np
import logging
import os
from matplotlib import gridspec
import matplotlib.cbook as cbook
import matplotlib.image as image
from scipy import interpolate
#%matplotlib inline
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - [%(levelname)-8s] (%(threadName)-10s) %(message)s")
logger = logging.getLogger(__name__)
import pandas as pd
import csv
import matplotlib
import math
import random
import re
import matplotlib.patches as mpatches
from matplotlib.offsetbox import (DrawingArea, OffsetImage,AnnotationBbox)
rootdir = os.path.dirname(os.path.abspath(__file__)) 
#sys.path.insert(0, rootdir+'/mopshub')
#plt.style.use('ggplot')
PdfPages = PdfPages('../output_data/mopshub_buses_test' + '.pdf')

def get_color(i):
    col_row = ["#000000", "#3a3487", "#f7e5b2", "b", "g", "r", "y", "c", "m", "lime", "#943ca6", "#df529e", "#f49cae", "tab:blue",
            "tab:orange", "tab:purple", "tab:pink", "#332d58", "#3b337a", "#365a9b", "#2c4172", "#2f3f60", "#3f5d92",
            "#4e7a80", "#60b37e", "darkgoldenrod", "darksalmon", "darkgreen", "#904a5d", "#5d375a", "#4c428d", "#31222c", "#b3daa3","#f4ce9f", "#ecaf83"]
    return col_row[i]

def plot_adc(file = None, nodeId = 0, bus_id = 1):
    data = pd.read_csv( file, delimiter=",", header=0)
    n_channels = 32
    _start_a = 3  # to ignore the first subindex it is not ADC
    for target in np.arange(_start_a,n_channels+_start_a):
        print("Plotting data from channel %i"%target)
        fig, ax = plt.subplots()
        condition = (data["adc_ch"] == target)
        respondant = data[condition]
        plt.suptitle('MOPS (NodeId = %i & bus = %i]'%(nodeId,bus_id) ,fontsize=9)
        ax.plot(respondant[respondant["nodeId" ]== nodeId]["time"],respondant[respondant["nodeId" ]== nodeId]["adc_data_converted"], label="ADC channel No.%i"%target, color =get_color(target))
        ax.ticklabel_format(useOffset=False)
        ax.legend(loc="upper left", prop={'size': 8})
        ax.autoscale(enable=True, axis='x', tight=None)
        ax.grid(True)
        ax.set_ylabel(r'ADC value [mV]')
        ax.set_xlabel("time [s]")
        plt.tight_layout()    
        PdfPages.savefig()
        plt.close(fig)




def plot_CANCompare_Bar(file = "Configuration_pattern.csv",test = "test_rx"):
        num = re.findall(r'\d+', file) 
        print("=======================================Plotting Values [%s buses]=================================================="%num[0])
        col_row = plt.cm.BuPu(np.linspace(0.3, 0.9, 10))
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        gs = gridspec.GridSpec(2, 1, height_ratios=[2.8, 1.2])
        #ax = plt.subplot(gs[0])
        #ax2 = plt.subplot(gs[1])
        plt.suptitle('MOPS-HUB CAN bus Simulation Statistics [%s buses]'%num[0],fontsize=9)
        reqmsg_append = []
        respmsg_append=[]
        status_array = []
        data_file = pd.read_csv(file,encoding = 'utf-8').fillna(0)
        data_file["time"] = pd.to_numeric(data_file.time)
        n_buses = (data_file[data_file["bus_id"].duplicated() ==False])
        bus_array = [str(x) for x in n_buses["bus_id"]]  
        x_bins = np.arange(0, len(bus_array))
        time_stamp  = (data_file["time"].max()- data_file["time"].min()) *10**-9 
        for i in n_buses["bus_id"]:           
            # pick condition fro req and resp
            req_msg_cond = np.where((data_file["bus_id"]==i) & (data_file["reqmsg"]==1) & (data_file[test]==1))
            resp_msg_cond = np.where((data_file["bus_id"]==i) & (data_file["respmsg"]==1) & (data_file[test]==1) & (data_file["status"]==1))
            #cond_bus_reqmsg = (data_file[data_file["bus_id"]==i].loc[lambda x:x[test]==1]["reqmsg"].value_counts())
            #cond_bus_respmsg = (data_file[data_file["bus_id"]==i].loc[lambda x:x[test]==1]["respmsg"].value_counts())
            
            cond_bus_reqmsg = (data_file.loc[req_msg_cond]["reqmsg"].value_counts())
            cond_bus_respmsg = (data_file.loc[resp_msg_cond]["respmsg"].value_counts())            
            #append the results
            reqmsg_append = np.append(reqmsg_append,cond_bus_reqmsg) 
            respmsg_append = np.append(respmsg_append,cond_bus_respmsg) 
            
            if (cond_bus_reqmsg.tolist() == cond_bus_respmsg.tolist()): status_array = np.append(status_array,1) 
            else: status_array = np.append(status_array,0) 
        eff = np.divide(respmsg_append, reqmsg_append) *100
        ax.grid()
        ax.bar(np.arange(-0.25, len(bus_array)-0.25), reqmsg_append,color = col_row[0],  width = 0.5)
        ax.bar(x_bins , respmsg_append , color = col_row[4], width = 0.4)
        ax.text(0.90, 0.50, "Run Duration=%.3f Sec\n  No. of CAN Buses=%.2i"%(time_stamp,len(bus_array)), size=7,                  
                horizontalalignment='right', verticalalignment='top', transform=ax.transAxes,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
        ax.set_xticks(x_bins)
        ax.set_xticklabels([],fontsize=6)
        ax.set_ylabel('CAN Message Counts',fontsize=8)
        plt.xlabel('CAN Bus ID',fontsize=8)
        colors = ["r" for i in x_bins]
        for c in np.arange(0, len(status_array)):
            if bus_array[c] == 1: colors[c] = "r"
            else: colors[c] = "g"    
        
        ax.legend(labels=["Requested CAN Messages (TX)", "Responded CAN Messages (RX)"],fontsize=7)
        plt.xlabel('CAN Bus ID',fontsize=8)
        plt.xticks(rotation=60)
        # ax2.errorbar(x_bins, eff, yerr=0.0, fmt='o-', color=col_row[7], label='Communication Efficiency')
        # ax2.spines['right'].set_position(('outward', 1))
        # ax2.set_xticks(x_bins)
        ax.set_xticklabels(["Bus"+x for x in bus_array],fontsize=6)
        # ax2.set_ylabel('Efficiency',fontsize=8)
        # ax2.grid()
        colorax = ax.twiny()
        colorax.xaxis.set_ticks_position('bottom') # set the position of the second x-axis to bottom
        colorax.xaxis.set_label_position('bottom') # set the position of the second x-axis to bottom
        colorax.spines['bottom'].set_position(('outward', 50))
        colorax.set_xticks(x_bins)
        symbolsx = ["⚫" for i in x_bins]
        colorax.set_xticklabels(symbolsx, size=15)
        colorax.set_xlim(ax.get_xlim())
        for tick, color in zip(colorax.get_xticklabels(), colors): tick.set_color(color)  
        
        plt.tight_layout()
        plt.savefig('mopshub_%sbuses_simulation_bus_activity.png'%num[0])
        PdfPages.savefig()
        plt.close(fig)
#plot_CANCompare_Bar(file=os.path.expanduser('~')+"/tb_mopshub_top_tb_mopshub_top_32bus.data_generator0.can_bus_activity0_buses_1.csv",test = "test_tx")
#plot_CANCompare_Bar(file=os.path.expanduser('~')+"/tb_mopshub_top_tb_mopshub_top_16bus.data_generator0.can_bus_activity0_buses_1.csv",test = "test_tx")
plot_CANCompare_Bar(file="/home/dcs/git/canmops/output_data/mopshub_data_32.csv",test = "test_tx")
#plot_CANCompare_Bar(file="../output_data/mopshub_top_32bus.csv",test = "test_tx")
plot_adc(file ="/home/dcs/git/canmops/output_data/mopshub_data_32.csv", nodeId = 1 )
PdfPages.close()


