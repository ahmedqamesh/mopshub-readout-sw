########################################################
"""
    This file is part of the MOPS-Hub project.
    Author: Ahmed Qamesh (University of Wuppertal)
    email: ahmed.qamesh@cern.ch  
    Date: 01.05.2023
"""
########################################################
from __future__ import division
import numpy as np
import pandas as pd
import logging
from logger_main   import Logger
from plotting   import Plotting
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="Analysis", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()#

class Analysis(object):
    
    def __init__(self):
        pass
    
    def get_run_info(self, data_frame = None , run_index = None, run_minutes = [None], data_dir = None,PdfPages =None):
        fluences_array = []
        run_fluences = []
        shaded_regions = [
            ("Run1", "2024-07-07 15:25:00", "2024-07-07 15:48:00"),
            ("Run2", "2024-07-07 16:30:00", "2024-07-07 16:40:00"),
            ("Run3", "2024-07-07 18:00:00", "2024-07-07 18:05:00"),
            ("Run4", "2024-07-07 18:14:00", "2024-07-07 18:26:00"),
            ("Run5", "2024-07-07 18:31:00", "2024-07-07 18:36:00"),
            ("Run6", "2024-07-07 18:53:00", "2024-07-07 19:03:00")
        ]     
        FWHM        = np.array([0,66,66,23,23,23,23])
        energy      = np.array([0,48.2,102.61,145.46,145.46,145.46,145.46])
        intensity   = np.array([0,3.2e+09, 3.2e+09, 3.2e+09, 8.0e+07,4.0e+08,1.2e+08]) 
        # Run Duration
        seu_time_min    = [0, 23 ,10,5, 12,5,10]
        reference_timestamp = [0, "2024-07-07_15:25:00", "2024-07-07_16:3:00", "2024-07-07_17:55:00", "2024-07-07_18:13:00", "2024-07-07_18:31:00","2024-07-07_18:52:00"]
    
        seu_time_min    = np.array(seu_time_min)
        seu_time_sec    = np.array(seu_time_min*60)
        fluences  = np.multiply(intensity, seu_time_sec)
        # Calculate cumulative sum
        accomulated_fluence_array = np.cumsum(fluences)
        #print(fluences, accomulated_fluence_array)
        Plotting().plot_run_info(x = np.cumsum(seu_time_min), 
                                 y = accomulated_fluence_array, 
                                 data_dir =data_dir, 
                                 PdfPages =PdfPages)
        run_name =run_index+1
        if   run_name >= 1: 
            run_info = f"Run{run_name}:I = {'{:.2e}'.format(intensity[run_name])} - FWHM = {FWHM[run_name]}mm - E = {energy[run_name]} Mev - T = {seu_time_min[run_name]} "
            logger.notice(run_info)
            reference_time = pd.to_datetime(reference_timestamp[run_name], format='%Y-%m-%d_%H:%M:%S')
            data_frame['duration'] = (data_frame['Times'] - reference_time).dt.total_seconds()
            data_frame['accfluence'] = np.cumsum(data_frame['duration'] * intensity[run_name])
            data_frame['fluence'] = data_frame['duration'] * intensity[run_name]
            data_frame['intensity'] = intensity[run_name]
            # Multiply the unique_minutes array by the multiplier, keeping False values unchanged
            run_fluences = [minute * intensity[run_name]*60  if minute is not False else False for minute in run_minutes]
        
        else: run_info = ""
        
        return run_info,data_frame,run_fluences,accomulated_fluence_array,shaded_regions

    # Conversion functions
    def adc_conversion(self, adc_channels_reg="V", value=None,resistor_ratio = 1,ref_voltage = 1.226):
        '''
        the function will convert each ADC value into a reasonable physical quantity in volt
        > MOPS has 12 bits ADC value ==> 2^12 = 4096 (this means that we can read from 0 -> 4096 different decimal values)
        > The full 12 bits ADC covers up to 850mV [or ref_voltage]
        >This means that each ADC value corresponds to 850/4096 = 0.207 mV for 1 bit this is the resolution of the ADC)
        > The true voltage on each ADC is V = value * resistance
        Example: 
        To calibrate each ADC value 
        1. multiply by 0.207 to give the answer in mV
        2. multiply by the resistor ratio to get the actual voltage
        '''
        if value is not None:
            if adc_channels_reg == "V":
                value = value * ref_voltage/4096  *resistor_ratio
            elif adc_channels_reg == "T":
                value = value * ref_voltage/4096 * resistor_ratio
            else:
                value = value
        return value

    def NTC_convertion(self,value =None):
        '''
        To convert ADC data to temperature you first find the thermistor resistance and then use it to find the temperature.
        https://www.jameco.com/Jameco/workshop/techtip/temperature-measurement-ntc-thermistors.html
        Rt = R0 * (( Vs / Vo ) - 1) 
        
        '''
       
        return value
    def binToHexa(self, n):
        # convert binary to int
        num = int(n, 2)   
        # convert int to hexadecimal
        hex_num = hex(num)
        return(num)
    
if __name__ == "__main__":
        pass
