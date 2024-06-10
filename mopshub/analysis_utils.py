from __future__ import division
import logging
import os
import yaml
import numpy as np
import pandas as pd
import csv
from pathlib import Path
import coloredlogs as cl
import socket
import ipaddress
from logger_main   import Logger
import logging
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="Analysis", console_loglevel=logging.INFO, logger_file=False)
logger = log_call.setup_main_logger()#

class AnalysisUtils(object):
    
    def __init__(self):
        pass
    # Conversion functions    
    def save_to_h5(self,data=None, outname=None, directory=None, title = "Beamspot scan results"):
        if not os.path.exists(directory):
                os.mkdir(directory)
        filename = os.path.join(directory, outname)
        with tb.open_file(filename, "w") as out_file_h5:
            out_file_h5.create_array(out_file_h5.root, name='data', title = title, obj=data)  
    
    def open_yaml_file(self,directory=None , file=None):
        filename = os.path.join(directory, file)
        with open(filename, 'r') as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        return cfg
    
    def dump_yaml_file(self,directory=None , file=None, loaded = None):
        
        filename = os.path.join(directory, file)
        with open(filename, 'w') as ymlfile:
            yaml.dump(loaded, ymlfile, sort_keys=False)#default_flow_style=False


    def check_last_row (self, data_frame = None, file_name = None, column = "status"):
        data_frame_last_row = data_frame.tail(1)
        pattern_exists = any(data_frame_last_row[column].astype(str).str.contains("End of Test"))
        if pattern_exists: 
            logger.notice(f"Noticed a Complete test file named: {file_name}") 
            data_frame = data_frame.iloc[:-1]
        else: logger.warning(f"Noticed Incomplete test file")    
        return data_frame
    
        
    def save_to_csv(self,data=None, outname=None, directory=None):
        df = pd.DataFrame(data)
        if not os.path.exists(directory):
                os.mkdir(directory)
        filename = os.path.join(directory, outname)    
        df.to_csv(filename, index=True)

    def read_csv_file(self, file=None):
        """ This function will read the data using pandas
        """
        data_file = pd.read_csv(file,encoding = 'utf-8').fillna(0)
        return data_file
                
    def open_h5_file(self,outname=None, directory=None):
        filename = os.path.join(directory, outname)
        with tb.open_file(filename, 'r') as in_file:
            data = in_file.root.data[:]
        return data
                    
    def get_subindex_description_yaml(self,dictionary = None, index =None, subindex = None):
        index_item = [dictionary[i] for i in [index] if i in dictionary]
        subindex_items = index_item[0]["subindex_items"]
        subindex_description_items = subindex_items[subindex]
        return subindex_description_items
    
    def get_info_yaml(self,dictionary = None, index =None, subindex = "description_items"):
        index_item = [dictionary[i] for i in [index] if i in dictionary]
        index_description_items = index_item[0][subindex]
        return index_description_items
                
    def get_subindex_yaml(self,dictionary = None, index =None, subindex = "subindex_items"):
        index_item = [dictionary[i] for i in [index] if i in dictionary]
        subindex_items = index_item[0][subindex]
        return subindex_items.keys()
    
    def open_csv_file(self,outputname=None, directory=None, fieldnames = ['A', 'B']):
        if not os.path.exists(directory):
            os.mkdir(directory)
        filename = os.path.join(directory, outputname) 
        
        out_file_csv = open(filename + '.csv', 'w+')
        return out_file_csv

    def build_data_base(self,fieldnames=["A","B"],outputname = False, directory = False):
        out_file_csv =self.open_csv_file(outputname=outputname, directory=directory)
        
        writer = csv.DictWriter(out_file_csv, fieldnames=fieldnames)

        writer.writeheader()    
        
        csv_writer = csv.writer(out_file_csv)  # , delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)     
           
        return csv_writer, out_file_csv 
  
    
    def get_ip_device_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
        s.close()
    
    def get_ip_from_subnet(self, ip_subnet):
        #https://realpython.com/python-ipaddress-module/
        ips= ipaddress.ip_network(ip_subnet)
        ip_list=[str(ip) for ip in ips]
        return ip_list

 
    def get_data_for_day_hour(self, data_frame = None, target_day = None, target_hour = None, device = None):
         # Convert timestamp column to datetime format
        if device == "fpga_card":
            time_format = '%H:%M:%S'
            time_header_format = "Times"
        else:
            time_format = '%Y-%m-%d_%H:%M:%S'
            time_header_format = "TimeStamp"
        
        # Make a copy of the DataFrame to avoid SettingWithCopyWarning
        data_frame = data_frame.copy()
    
        data_frame['TimeStamp'] = pd.to_datetime(data_frame[time_header_format], format=time_format)
        
        #Extract day and hour from timestamp
        data_frame['day'] = data_frame['TimeStamp'].dt.date
        data_frame['hour'] = data_frame['TimeStamp'].dt.hour
        return data_frame
   
    def getDay(self,TimeStamps =None, device = None): 
        pos = 0
        day_pos = 0
        day = ""
        #day = TimeStamps[0].split('_')[0]# Extracting the day part assuming the format is "YYYY-MM-DD_HH:MM:SS"
        if device == "fpga_card":
            day = 1
            pos = 1
        else:
            while len(TimeStamps[0]) != pos:
                day += str(TimeStamps[0][pos])
                pos += 1
            
        last_day = None
        unique_days = []
        days = [[""]*1 for i in range(len(TimeStamps))]
        for TimeStamp in TimeStamps:
            if device == "fpga_card":
                TimeStamp = str(TimeStamp) 
            else:
                TimeStamp = TimeStamp            
            current_stamp = TimeStamp[0:10]
            days[day_pos] =current_stamp#11+12 for hours 
            if current_stamp != last_day:
    
                unique_days.append(current_stamp)
                last_day = current_stamp         
        #day_pos += 1
        return day, unique_days

    def count_consecutive_repeats(self, timestamps=None):
        if not timestamps:
            return []
    
        consecutive_counts = []
    
        current_timestamp = timestamps[0]
        count = 1
        index = 0
        for i in range(1, len(timestamps)):
            if timestamps[i] == current_timestamp:
                count += 1
            else:
                consecutive_counts.append((index, count))
                current_timestamp = timestamps[i]
                count = 1
                index = index+1
        
        # Update the count for the last timestamp
        consecutive_counts.append((index, count))#instead of current_timestamp
        
        repeats = [counts[1] for counts in consecutive_counts]
        consecutive_repeats = [counts[0] for counts in consecutive_counts]
        new_array = [entry[0] for entry in consecutive_counts for _ in range(entry[1])]
        return consecutive_repeats, repeats, new_array


    def getHours(self,TimeStamps, min_scale =None, device = None):
        hour = 0
        unique_hours = []
        last_hour = None
        hours = [[""]*1 for i in range(len(TimeStamps))]
        for TimeStamp in TimeStamps:
            if device == "cic_card":
                if min_scale == "min_scale" : hours[hour] = TimeStamp[14] + TimeStamp[15] #14+15 for min 
                else: hours[hour] = TimeStamp[11] + TimeStamp[12] #11+12 for hours
            
            if device == "power_card":
                if min_scale == "min_scale" : hours[hour] = TimeStamp[14] + TimeStamp[15] #14+15 for min 
                else: 
                    #try:
                    current_stamp = TimeStamp[11:13]
                    hours[hour] =current_stamp#11+12 for hours  
                    if current_stamp != last_hour:
                        unique_hours.append(int(current_stamp))
                        last_hour = current_stamp   
                    #except:
                    #    pass
            if device == "fpga_card":
                #hours[hour] = TimeStamp[0] + TimeStamp[1] #11+12 for hours
                TimeStamp = str(TimeStamp)            
                current_stamp = TimeStamp[11] + TimeStamp[12]
                hours[hour] =current_stamp#11+12 for hours  
                if current_stamp != last_hour:
                    unique_hours.append(int(current_stamp))
                    last_hour = current_stamp  
                                    
            else:
                if min_scale == "min_scale" : hours[hour] = TimeStamp[14] + TimeStamp[15] #14+15 for min 
                else: 
                    #try:
                    current_stamp = TimeStamp[11:13]
                    hours[hour] =current_stamp#11+12 for hours  
                    if current_stamp != last_hour:
                        unique_hours.append(int(current_stamp))
                        last_hour = current_stamp   
                    #except:
                    #    pass
            hour += 1
        return hours, unique_hours
    


    def get_hourly_average_value(self,data_frame = None, column = None,unique_days = None, device = None,n_points =1 ):
        hourlyAverageValues = []
        hourlySTDValues = []
        data_for_day_hour = self.get_data_for_day_hour(data_frame = data_frame, device = device)
        for target_day in unique_days:
            condition = (data_for_day_hour['day'] == pd.to_datetime(target_day))
            data = data_for_day_hour[condition]
            data = data.apply(pd.to_numeric, errors='coerce')
            interval = pd.cut(data['hour'], bins=n_points)
            hourly_avg = data.groupby('hour').agg('mean')
            hourly_std = data.groupby('hour').agg('std')
            #hourly_avg = data.groupby(['hour', interval]).agg('mean')
            #hourly_std = data.groupby(['hour', interval]).agg('std')
            
            for hour, avg_value in hourly_avg.iterrows():
                hourlyAverageValues = np.append(hourlyAverageValues, avg_value[column])
            for hour, std_value in hourly_std.iterrows():
                hourlySTDValues = np.append(hourlySTDValues, std_value[column])        
        return hourlyAverageValues, hourlySTDValues
    

    def getHourlyAverageValue(self,hours =None, data =None, min_scale =None, unique_hours = None,unique_days = None):
        if min_scale == "min_scale" :dataSum = [np.zeros(0) for i in range(60)] #24 if hours and 60 if min 
        else: dataSum = [np.zeros(0) for i in range(len(unique_hours))] #24 if hours and 60 if min 
        
        pos = 0
        for h in hours:
            try:
                dataSum[int(h)] = np.append(dataSum[int(h)],float(data[pos]))
                pos += 1
            except: 
                pass
                #logger.warning("No real Number")
        hourlyAverageValues = [[""]*1 for i in range(len(dataSum))]
        
        for hour in range(len(dataSum)): 
            if dataSum[hour].any()>0:
                hourlyAverageValues[hour] = np.average(dataSum[hour])
            else:  
                hourlyAverageValues[hour] = None
        return hourlyAverageValues
             