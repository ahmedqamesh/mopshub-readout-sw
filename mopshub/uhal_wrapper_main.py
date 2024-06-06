#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module provides a class for a UHAL wrapper for the ADC channels of the MOPS Chip.
It also provides a function for using this server as a command line tool.
Note
----
:Author: Ahmed Qamesh
:Contact: ahmed.qamesh@cern.ch
:Organization: Bergische Universität Wuppertal
"""
# Standard library modules
#from __future__ import annotations
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from configparser import ConfigParser
from typing import *
import time
import datetime
import keyboard
import atexit
#import asyncio
#from asyncio.tasks import sleep
import sys
import os
from threading import Thread, Event, Lock
import threading
import subprocess
import numpy as np
try:
    from logger_main   import Logger
    from analysis_utils import AnalysisUtils
    from analysis import Analysis
except (ImportError, ModuleNotFoundError):
    from .logger_main   import Logger
    from .analysis_utils import AnalysisUtils
    from .analysis import Analysis
import struct
# Third party modules
from collections import deque, Counter
from tqdm import tqdm
import ctypes as ct
import logging
import queue
from bs4 import BeautifulSoup #virtual env
from typing import List, Any
from random import randint
import uhal
import random
uhal.setLogLevelTo(uhal.LogLevel.WARNING )
#from csv import writer
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format = log_format,name = "UHAL Wrapper",console_loglevel=logging.INFO, logger_file = False)

rootdir = os.path.dirname(os.path.abspath(__file__))
config_dir = "config_files/"
lib_dir = rootdir[:-8]

class UHALWrapper(object):

    def __init__(self,
                 file_loglevel=logging.INFO, 
                 logdir=None,load_config = False, 
                 logfile = None,
                 console_loglevel=logging.INFO,
                 mainWindow= False):
       
        super(UHALWrapper, self).__init__()  # super keyword to call its methods from a subclass:        

        """:obj:`~logging.Logger`: Main logger for this class"""
        if logdir is None:
            #'Directory where log files should be stored'
            logdir = os.path.join(lib_dir, 'log')                 
        self.logger = log_call.setup_main_logger()
        
        if load_config:
           # Read UHAL settings from a file 
            self.__uri, self.__addressFilePath =   self.load_settings_file()          

        # Initialize library and set connection parameters
        self.__uhalMsgQueue = deque([], 100)
        self.__cnt = Counter()
        self.error_counter = 0
        self.__pill2kill = Event()  
        self.__hw = None
        self.logger.success('....Done Initialization!')
        self.__address_byte = [0x80, 0x88, 0x90, 0x98, 0x80]
        if logfile is not None:
            ts = os.path.join(logdir, time.strftime('%Y-%m-%d_%H-%M-%S_UHAL_Wrapper.'))
            self.logger.info(f'Existing logging Handler: {ts}'+'log')
            self.logger_file = Logger().setup_file_logger(name = "UHALWrapper",console_loglevel=console_loglevel, logger_file = ts)#for later usage
            self.logger_file.success('....Done Initialization!')
    
    def config_ipbus_hardware(self, uri = None, addressFilePath = None):
        """
        This function establishes a connection to the hardware device using the specified URI and address file path.
        If no URI or address file path is provided, it uses the default values specified during object initialization.
        
        Parameters:
        - uri (str): String with the protocol and location of the hardware endpoint in URI format. Defaults to None.
        - addressFilePath (str): String with the path to the XML address table for the hardware device. Defaults to None.
    
        Returns:
        - hw_interface: A HwInterface object representing the configured hardware interface.
    
        Usage:
        hw_interface = config_ipbus_hardware(uri="ipbusudp-2.0://localhost:50001", addressFilePath="/path/to/address_table.xml")
    
        Example:
        # Configure UHAL hardware interface with default URI and address file path
        hw_interface = config_ipbus_hardware()
    """
        if uri is None: uri = self.__uri
        if addressFilePath is None: addressFilePath = self.__addressFilePath 
        hw_interface = uhal.getDevice("mopshub", uri, "file://" + addressFilePath)
        self.set_uhal_hardware(hw_interface)

        return hw_interface

    def load_settings_file(self, file="main_settings.yml"):
        """
        Load all the information related to the hardware from a YAML settings file.
    
        Parameters:
        - file (str, optional): The name of the YAML settings file. Defaults to "main_settings.yml".
    
        Returns:
        - tuple: A tuple containing the URI and address file path loaded from the settings file.
    
        Usage:
        # Load settings from the default YAML file
        uri, address_file_path = load_settings_file()
        """
        # Construct the full path to the settings file
        filename = os.path.join(lib_dir, config_dir + file)
         # Get the last modified date of the settings file
        test_date = time.ctime(os.path.getmtime(filename))
        # Load settings from bus settings file
        self.logger.notice("Loading bus settings from the file %s produced on %s" % (filename, test_date))
        try:
            # Open and load settings from the YAML file
            _channelSettings = AnalysisUtils().open_yaml_file(file=config_dir + "main_settings.yml", directory=lib_dir)
            # Extract URI and address file path from loaded settings
            _uri = _channelSettings['ethernet']["uri"]
            _addressFilePath = _channelSettings['ethernet']["addressFilePath"]
            return _uri,_addressFilePath
        except:
          self.logger.error("uri %s settings Not found" % (_uri)) 
          return None,None

    def read_uhal_message(self, hw = None, node =None, registerName=None, out_msg = True, w_r= "Read"):
        """
        Read a value from a uHAL node.
    
        Parameters:
        - hw (uhal.HwInterface, optional): The uHAL hardware interface object. Defaults to None.
        - node (uhal.Node, optional): The uHAL node object representing the register to read from. Defaults to None.
        - registerName (str, optional): The name of the register being read from. Defaults to None.
        - out_msg (bool, optional): Flag indicating whether to output log messages. Defaults to True.
        - w_r (str, optional): Indicates whether the operation is a read or a write. Defaults to "Read".
    
        Returns:
        - uhal.ValWord: The value read from the register.
    
        Usage:
        # Assuming 'hw' and 'node' are valid objects
        value = read_uhal_message(hw, node, "REGISTER_NAME")
        """
        reg_value = node.read()
        # Send IPbus transactions
        hw.dispatch()
        if out_msg:  self.logger.info(f'{w_r} {hex(reg_value.value())} : {registerName}')
        return reg_value
    
    def write_elink_message(self, hw=None, data=None, reg=None, out_msg=True):
        """
        Writes data to multiple registers in the MOPSHub device.
    
        This function writes data to multiple registers specified by their names (reg) with corresponding data values.
        It utilizes the `write_uhal_message` function to perform individual register writes. It then dispatches IPbus
        transactions and returns a flag indicating if the write requests were successfully queued.
    
        Parameters:
        - hw (HwInterface): The UHAL hardware interface object.
        - data (list): A list containing the data values to write to each register.
        - reg (list): A list containing the names of the registers in the address table.
        - out_msg (bool, optional): Flag to enable/disable printing of warning messages. Defaults to True.
    
        Returns:
        - int: Flag indicating if the write requests were successfully queued (1 for success, 0 for failure).
    
        Usage:
        # Write data to multiple registers in the MOPSHub device
        success = write_elink_message(hw, data, reg, out_msg)
        """
        nodes = []# List to store node objects
        reqmsg = 0# Flag indicating if the write requests were successfully queued
        # Retrieve the node objects corresponding to the registers
        for r in reg: nodes = np.append(nodes,hw.getNode(r))
         # Perform individual register writes using write_uhal_message function
        [self.write_uhal_message(hw =hw,node =nodes[data.index(d)], data=d, registerName=r, out_msg=out_msg) for r,d in zip(reg,data)]
        # Set the flag indicating write requests were made
        reqmsg = 1
        
        return reqmsg

    def write_uhal_message(self,hw =None, node =None, data=None, registerName=None, out_msg = True ):
        """
        Writes data to a register and optionally reads back the written value.
    
        This function writes data to the specified node/register and optionally reads back the written value
        to verify the write operation. It then dispatches IPbus transactions and returns a flag indicating
        if the write request was successfully queued.
    
        Parameters:
        - hw (HwInterface): The UHAL hardware interface object.
        - node (str): The name of the node containing the register to write.
        - data (int): The data to write to the register.
        - registerName (str): The name of the register in the address table.
        - out_msg (bool, optional): Flag to enable/disable printing of warning messages. Defaults to True.
    
        Returns:
        - int: Flag indicating if the write request was successfully queued (1 for success, 0 for failure).
    
        Usage:
        # Write data to a register and read back the written value
        success = write_uhal_message(hw, node, data, registerName, out_msg)
    """
        # Flag indicating if the write request was successfully queued
        reqmsg = 0
        # Write data to the node
        node.write(data)
        # Set the flag indicating a write request was made
        reqmsg= 1
        # Read the value back from the register to verify the write operation
        reg_ret_value = self.read_uhal_message(hw = hw, node =node, registerName=registerName, out_msg = out_msg, w_r= "Writing") 
        # Compare the written data with the read data
        status = (hex(data) ==hex(reg_ret_value.value())) 
        # Print a warning message if the read-back data does not match the written data
        if out_msg and not status:  self.logger.warning(f'Writing mismatch in {registerName} [W: {hex(data)} |R:{hex(reg_ret_value.value())}]') 
        # Send IPbus transactions
        hw.dispatch()
        
        return reqmsg         
    
    def build_data_rec_elink(self, reg =[], out_msg = True):
        """
        Build a response message for an SDO (Service Data Object) communication.
    
        Parameters:
        - reg (list of str, optional): List containing three hexadecimal strings representing the registers to build the response message from. Defaults to an empty list.
        - out_msg (bool, optional): Flag indicating whether to output log messages. Defaults to True.
    
        Returns:
        - tuple: A tuple containing:
            - list of str: The new bytes representing the response message.
            - str: The hexadecimal representation of the response register.
    
        Usage:
        # Assuming 'reg' is a list of three hexadecimal strings
        new_bytes, response_reg = build_data_rec_elink(reg)
        """
        # Data_rec_reg is 76 bits = sdo[12bits]+payload[32bits]+bus_id[5bits]++3bits0+8bits0+16bits0
        reg_values = []
        data_ret = [0 for b in np.arange(9)]    
        new_Bytes = [0 for b in np.arange(9)]    
        responsereg = Analysis().binToHexa(bin(int(reg[0],16))[2:].zfill(32) 
                                           +bin(int(reg[1],16))[2:].zfill(32) 
                                           +bin(int(reg[2],16))[2:].zfill(32))
        for r in reg: 
            try: reg_values = np.append(reg_values,hex(r))
            except: reg_values = np.append(reg_values,r)
        msg_bin_0 = bin(int(reg_values[0],16))[2:].zfill(32)
        msg_bin_1 = bin(int(reg_values[1],16))[2:].zfill(32)
        msg_bin_2 = bin(int(reg_values[2],16))[2:].zfill(32)     
        data_ret  = [hex(Analysis().binToHexa(msg_bin_0[0:12]))#cobid
                   ,hex(Analysis().binToHexa(msg_bin_0[12:20]))
                   ,hex(Analysis().binToHexa(msg_bin_0[20:28]))
                   ,hex(Analysis().binToHexa(msg_bin_0[28:32]+msg_bin_1[0:4]))
                   ,hex(Analysis().binToHexa(msg_bin_1[4:12]))
                   ,hex(Analysis().binToHexa(msg_bin_1[12:20]) )
                   ,hex(Analysis().binToHexa(msg_bin_1[20:28]) )
                   ,hex(Analysis().binToHexa(msg_bin_1[28:32]+msg_bin_2[0:4]))
                   ,hex(Analysis().binToHexa(msg_bin_2[4:12]) )]
        new_Bytes= [data_ret[0],data_ret[1],data_ret[3],data_ret[2],data_ret[4],data_ret[8],data_ret[7],data_ret[6],data_ret[5]]
        
        for i in range(len(data_ret)): 
            if new_Bytes[i] =='': new_Bytes[i]=0       
        else:   pass 
        return new_Bytes, responsereg
    
 
    def dumpMessage(self, cobid =None, msg =None, t =None):
        """Dumps a uhal message to the screen and log file
        Parameters
        ----------
        cobid : :obj:`int`
            |UHAL| identifier
        msg : :obj:`bytes`
            |UHAL| data - max length 8
        t : obj'int'
        """
        msgstr = '{:3X} {:d}   '.format(cobid, 8)
        for i in range(len(msg)):
            msgstr += '{:02x}  '.format(msg[i])
        msgstr += '    ' * (8 - len(msg))
        st = datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S')
        msgstr += str(st)
        self.logger.report(msgstr)
                       
    def enable_read_elink (self, out_msg = None,subindex= 0):
        """
        Enable the read signal and wait for an interrupt signal from the Internal MOPSHUB FIFO.
    
        Parameters:
        - timeout (float, optional): Time to wait for each check of the interrupt signal. Defaults to None.
        - out_msg (bool, optional): Flag indicating whether to output log messages. Defaults to None.
        - subindex (int, optional): Index value used in log messages. Defaults to 0.
    
        Returns:
        - bool: True if a message is found in the buffer, False otherwise.
    
        Usage:
        # Example usage with optional parameters
        message_found = enable_read_elink(out_msg=True, subindex=1)
        """
         #wait for interrupt signal from FIFO
        hw = self.get_uhal_hardware()
        count, count_limit = 0, 3
        #irq_tra_sig = 0x0
        while (count !=count_limit):
            irq_tra_sig =   self.read_uhal_message(hw = hw, 
                                                    node = hw.getNode("IPb_addr3"),
                                                    registerName="IPb_addr3", out_msg = None)
            count= count+1
            if out_msg: self.logger.info(f'Read irq_tra_sig =  {irq_tra_sig} : Count ({count})')
            time.sleep(0.05)#Time to wait for each check of the interrupt signal
            if irq_tra_sig >=0x1:break
        #Read data  from FIFO        
        if irq_tra_sig>0x0:
            found_msg =True
            if out_msg: self.logger.info(f'Found Message in the buffer (irq_tra_sig = {irq_tra_sig})')
            # Start read elink
            self.write_uhal_message(hw = hw, 
                                         node =hw.getNode("IPb_addr10"), 
                                         registerName="IPb_addr10", 
                                         data = 0x1, 
                                         out_msg = False)  
        else: 
            found_msg = False
            self.logger.warning(f'Nothing Found in the buffer (irq_tra_sig = {irq_tra_sig})[{hex(subindex)}]')
        return found_msg 
    
    def read_elink_message(self, reg =None,  out_msg = True, subindex = 0):
        """
        Read message from MOPS Hub.
    
        Parameters:
        - reg (list): List of register names to read.
        - out_msg (bool, optional): Flag indicating whether to output log messages. Defaults to True.
        - subindex (int, optional): Index value used in log messages. Defaults to 0.
    
        Returns:
        - tuple: A tuple containing cobid, data, respmsg, responsereg, and timestamp.
    
        Usage:
        # Example usage with optional parameters
        cobid, data, respmsg, responsereg, timestamp = read_elink_message(reg=["IPb_addr1", "IPb_addr2"], timeout=0.1, out_msg=True, subindex=1)
        """       
        hw = self.get_uhal_hardware()
        nodes = []
        reg_values = []
        respmsg = 0
        msg_found =  self.enable_read_elink(out_msg = out_msg, subindex = subindex) 
        if msg_found:
            for r in reg: 
                nodes = np.append(nodes,hw.getNode(r))
                reg_value = nodes[reg.index(r)].read()
                # Send IPbus transactions
                hw.dispatch()
                if out_msg: self.logger.info(f'Read {r} Value = {hex(reg_value.value())}')
                reg_values = np.append(reg_values,hex(reg_value.value()))    
            respmsg = 1
            t = time.time()
            data, responsereg =  self.build_data_rec_elink(reg = reg_values, out_msg=out_msg)      
            cobid = int(data[0],16)
            data_ret = [0 for b in np.arange(len(data)-1)]
            for i in np.arange(len(data_ret)): data_ret[i] = int(data[i+1],16)
            if out_msg: self.dumpMessage(cobid, data_ret, t)
            self.__uhalMsgQueue.appendleft((cobid, data_ret, t))
            return cobid, bytearray(data_ret), respmsg, hex(responsereg), t
        else:
            respmsg = 0
            self.__cnt["messageFailed_response"] =self.__cnt["messageFailed_response"]+ 1
            
            return None, None, respmsg, None, None
        
    def  check_valid_message(self, nodeId = None, index = None, subindex = None, cobid_ret = None, data_ret = None, SDO_TX = None, SDO_RX = None,seu_test = None):
        """
        Check for a valid message and handle error signals.
    
        Parameters:
        - nodeId (int): Node ID.
        - index (int): Index value.
        - subindex (int): Subindex value.
        - cobid_ret (int): COBID return value.
        - data_ret (list): List of data return values.
        - SDO_TX (int): SDO transmit value.
        - SDO_RX (int): SDO receive value.
        - seu_test (bool): Flag indicating SEU test mode.
    
        Returns:
        - tuple: A tuple containing the decoded data, message validity, status, response message, and response register.
    
        Usage:
        # Example usage with required parameters
        data, message_valid, status, resp_msg, resp_reg = check_valid_message(nodeId=1, index=2, subindex=3, cobid_ret=0x1234, data_ret=[0x80, 0x43, 0x00, 0x03], SDO_TX=0x10, SDO_RX=0x11, seu_test=False)
    """
        messageValid = False
        errorSignal   = False  # check any reset signal from the chip
        errorResponse = False  # SocketUHAL error message
        status = 0
        respmsg, responsereg = 0, None
        t0 = time.perf_counter()
        timeout = 1000
        queue_copy = deque(self.__uhalMsgQueue)
        while time.perf_counter() - t0 < timeout / 1000 and messageValid == False:
                # check the message validity [nodid, msg size,...]
                for i, (cobid_ret, data_ret, t) in zip(range(len(queue_copy)),queue_copy):
                    if not seu_test:
                        
                        messageValid = (cobid_ret == SDO_RX + nodeId
                                        and data_ret[0] in [0x80, 0x43, 0x47, 0x4b, 0x4f, 0x42] 
                                        and int.from_bytes([data_ret[1], data_ret[2]], 'little') == index
                                        and data_ret[3] == subindex) 
                    
                    else:
                        messageValid = (cobid_ret == SDO_TX + nodeId
                                        and data_ret[0] in [0x40,0x80, 0x43, 0x47, 0x4b, 0x4f, 0x42] 
                                        and int.from_bytes([data_ret[1], data_ret[2]], 'little') == index
                                        and data_ret[3] == subindex) 
                                                
                    errorSignal = (cobid_ret == 0x700 + nodeId 
                                  and data_ret[0] in [0x05, 0x08,0x85]) 
                
                    errorResponse = (cobid_ret == 0x88 
                                     and data_ret[0] in [0x00]) 
    
    
                    if (messageValid or errorResponse): 
                        del self.__uhalMsgQueue[i]
                        break
                    if (messageValid ==False):
                        _, _, respmsg, responsereg, _ = self.read_elink_message(reg = ["IPb_addr0","IPb_addr1","IPb_addr2"],subindex = subindex, out_msg = None) 
                #self.__uhalMsgThread.join()     
        if errorSignal   : self.logger_file.notice(f'Received a reset Signal with cobid:{hex(cobid_ret)} while calling subindex: {hex(subindex)}')
        if messageValid  or errorSignal:
            status = 1
            nDatabytes = 4 - ((data_ret[0] >> 2) & 0b11) if data_ret[0] != 0x42 else 4
            data = []
            for i in range(nDatabytes-1): 
                data.append(data_ret[4 + i])
            return int.from_bytes(data, 'little'), messageValid, status, respmsg, responsereg
        else:
            status = 0
            self.logger.info(f'SDO read response timeout (node {nodeId}, index'
                 f' {index:04X}:{subindex:02X})')
            self.__cnt["messageValid"]=self.__cnt["messageValid"]+1
            return None, messageValid, status, respmsg, responsereg
    
    def read_adc(self,hw, bus_id,timeout):

        self.logger.debug(f'CIC Channel {bus_id} - ADC readout')

        adc_result = [[int(), int()] for _ in range(4)]
        adc_info = []
        self.logger.debug("Read ADC channels:")
        counter = 0
        for address in self.__address_byte:
            #adc_out = self.spi.xfer2([address, 0x00, 0x00, 0x00, 0x00])
            _, _, _, adc_out =  self.read_monitoring_uhal(hw =hw,
                                                              cobid = 0x20,
                                                              spi_reg =address,
                                                              spi_select=bus_id,
                                                              timeout=timeout, 
                                                              out_msg =False)
            time.sleep(0.7)                     
            last_bits = bin(adc_out[4])[6:][:2]
            adc_info.append(adc_out)
            if adc_out[4] == 255:
                adc_result[int(last_bits, 2)][0] = self.__address_byte.index(address)
                adc_result[int(last_bits, 2)][1] = -1
            # search in the last four bits channel indicator bits 
            elif last_bits in {'00', '01', '10'}:#indicates which physical inputs to be converted
                if bin(adc_out[4])[9:] == '1':
                    self.logger.warning(
                        f"OF-Error during ADC Readout of phy. channel {int(last_bits, 2)}")
                    self.cnt[f"OF-ERROR Channel {int(last_bits, 2)}"] += 1
                    self.logger.warning(adc_out[4])
                if bin(adc_out[4])[8:][:1] == '1':
                    self.logger.warning(
                        f"OD-Error during ADC Readout of phy. channel {int(last_bits, 2)}")
                    self.cnt[f"OD-ERROR Channel {int(last_bits, 2)}"] += 1
                    self.logger.warning(adc_out[4])
                try:#ch1 is Ucurr(in volt) has a apecial conversion
                    if last_bits == '01':
                        value = round(((adc_out[2] * 256 + adc_out[3]) * 0.03814697), 3)
                    else:
                        value = round(((adc_out[2] * 256 + adc_out[3]) * 0.03814697 / 1000), 3)
                    adc_result[int(last_bits, 2)][0] = int(last_bits, 2)
                    adc_result[int(last_bits, 2)][1] = value  # 2,5V Ref
                except ZeroDivisionError:
                    adc_result[int(last_bits, 2)][0] = int(last_bits, 2)
                    adc_result[int(last_bits, 2)][1] = -1
            elif last_bits == '11':
                if bin(adc_out[4])[9:] == '1':
                    self.logger.warning(
                        f"OF-Error during ADC Readout of phy. channel {int(last_bits, 2)}")
                    self.cnt[f"OF-ERROR Channel {int(last_bits, 2)}"] += 1
                    self.logger.warning(adc_out[4])
                if bin(adc_out[4])[8:][:1] == '1':
                    self.logger.warning(
                        f"OD-Error during ADC Readout of phy. channel {int(last_bits, 2)}")
                    self.cnt[f"OF-ERROR Channel {int(last_bits, 2)}"] += 1
                    self.logger.warning(adc_out[4])
                try:
                    v_ntc = round(((adc_out[2] * 256 + adc_out[3]) * 0.03814697 / 1000), 3)
                    r_ntc = v_ntc * (20 / 2.5)
                    value = round((298.15 / (1 - (298.15 / 3435) * np.log(10 / r_ntc))) - 273.15, 3)
                    adc_result[int(last_bits, 2)][0] = int(last_bits, 2)
                    adc_result[int(last_bits, 2)][1] = value
                except ZeroDivisionError:
                    adc_result[int(last_bits, 2)][0] = int(last_bits, 2)
                    adc_result[int(last_bits, 2)][1] = -1
            else:
                adc_result[self.__address_byte.index(address)][0] = self.__address_byte.index(address)
                adc_result[self.__address_byte.index(address)][1] = -1
                counter += 1
                self.cnt["error_cnt"] += 1
                if counter % 5 == 0:
                    self.cnt["bad_readout"] += 1
                    self.logger.warning(f"Bad readout - {adc_result} - {self.cnt}")

        if self.cnt["bad_readout"] % 3 == 1:
            self.cnt["reset_cnt"] += 1
            #self.cs5523_startup(spi_cs, bus_id, mp_id)
            self.logger.warning(f"Restart ADC on Bus {bus_id}")

        # print(f"ADC readout finished: Bus_id: {bus_id} - {adc_result}")
        self.logger.debug(f"ADC readout finished: Bus_id: {bus_id} - {adc_result}")
        return
    
    
    def read_monitoring_uhal(self,hw =None, spi_reg =None, spi_select=None,cobid = 0X20,out_msg=None):
        """
        Read monitoring data using the uHAL library.
    
        Parameters:
        - hw: HwInterface object representing the hardware interface.
        - spi_reg: The SPI register to read.
        - spi_select: The SPI select value.
        - cobid: COBID value.
        - timeout: Timeout value for reading.
        - out_msg: Flag indicating whether to print log messages.
    
        Returns:
        - tuple: A tuple containing COBID, SPI select, SPI register, and ADC output data.
    
        Usage:
        # Example usage with required parameters
        cobid_ret, spi_select_ret, spi_reg_ret, adc_out = read_monitoring_uhal(hw=my_hw, spi_reg=0x01, spi_select=0x02, cobid=0x20, timeout=1, out_msg=True)
        """
    
        status =0;
        respmsg, responsereg  = 0, None
        #build Payload in a UHAL SDO format
        mon_IPb_addr6_hex = Analysis().binToHexa(bin(cobid)[2:].zfill(8)+
                                            bin(spi_select)[2:].zfill(8)+
                                            bin(spi_reg)[2:].zfill(8)+
                                            bin(0)[2:].zfill(8)) 
        reqmsg =  self.write_elink_message(hw =hw, 
                                              data=[mon_IPb_addr6_hex,0x0,0x0,0xa], 
                                              reg = ["IPb_addr6","IPb_addr7","IPb_addr8","IPb_addr9"], 
                                              out_msg = out_msg)     
        #read the response from the socket
        _frame  =  self.read_elink_message(reg = ["IPb_addr0","IPb_addr1","IPb_addr2"], 
                                                        out_msg = out_msg) 
        _, msg_ret,respmsg_ret, responsereg_ret, t = _frame
        if (not all(m is None for m in _frame[0:2])):
            responsereg_ret = bin(int(responsereg_ret,16))[2:].zfill(96)
            cobid_ret    = hex(Analysis().binToHexa(responsereg_ret[0:8]))
            spi_select_ret   = hex(Analysis().binToHexa(responsereg_ret[8:16]))
            spi_reg_ret  = hex(Analysis().binToHexa(responsereg_ret[16:24]))
            
            adc_out =   [hex(Analysis().binToHexa(responsereg_ret[16:24])),#spi_reg_ret
                         hex(Analysis().binToHexa(responsereg_ret[24:32])),#The first 8 sck_m are used to clear the SDO flag
                         hex(Analysis().binToHexa(responsereg_ret[32:40])),#The last 24 are needed to read the conversion result.
                         hex(Analysis().binToHexa(responsereg_ret[40:48])),
                         hex(Analysis().binToHexa(responsereg_ret[48:56]))]
            xadc_code =  Analysis().binToHexa(responsereg_ret[64:76])
            temp_xadc = xadc_code*503.975/4096-273.15
            reserved_value =hex(Analysis().binToHexa(responsereg_ret[56:64]))
            if out_msg: self.logger.info(f'cobid_ret:{cobid_ret}|| spi_select_ret: {spi_select_ret}||spi_reg_ret:{spi_reg_ret}||adc_out:{adc_out})')
            if out_msg: self.logger.info(f'FPGA temp_xadc:{round(temp_xadc,2)} C')
            adc_out =[int(adc_out[i],16) for i in range(len(adc_out))]
            last_bits = bin(adc_out[4])[2:][4:]
            #print(hex(spi_reg),last_bits[1:3], adc_out, bin(adc_out[4])[2:])
            return cobid_ret, spi_select_ret, spi_reg_ret, adc_out
        else:
            status = 0
        #     if responsereg is not None: return None, reqmsg, hex(responsereg),respmsg, responsereg, status
            return None, None, None, None 
        #

    def read_sdo_uhal(self,hw= None, bus= None, nodeId=None, index=None, subindex=None, SDO_TX=0x600, SDO_RX=0x580,out_msg=None,seu_test=None):
        """
        Read data using the SDO protocol with uHAL.
    
        Parameters:
        - hw: HwInterface object representing the hardware interface.
        - bus: Bus identifier.
        - nodeId: Node ID.
        - index: Index value.
        - subindex: Subindex value.
        - SDO_TX: Transmit COBID value.
        - SDO_RX: Receive COBID value.
        - out_msg: Flag indicating whether to print log messages.
        - seu_test: Flag indicating whether it's a single event upset test.
    
        Returns:
        - tuple: A tuple containing the read data, request message status, request message, response message status, response message, and overall status.
    
        Usage:
        # Example usage with required parameters
        data, reqmsg, requestreg, respmsg, responsereg, status = read_sdo_uhal(hw=my_hw, bus=1, nodeId=2, index=0x1234, subindex=0x01, SDO_TX=0x600, SDO_RX=0x580, out_msg=True, seu_test=False)
        """       
        status =0;
        respmsg, responsereg  = 0, None
        if nodeId is None or index is None or subindex is None:
            self.logger.warning('SDO read protocol UHALcelled before it could begin.')               
            self.__cnt["SDO read total"] = self.__cnt["SDO read total"]+1
            return None, None, None,respmsg, responsereg , status 
        hw_interface =  self.get_uhal_hardware()
        #build Payload in a UHAL SDO format
        IPb_addr6_hex, IPb_addr7_hex, IPb_addr8_hex, requestreg = self.build_data_tra_elink(cobid = SDO_TX+nodeId, bus = bus,  index=index, subindex=subindex,seu_test = seu_test)

        #write the Request
        try:
            reqmsg =  self.write_elink_message(hw =hw_interface, 
                                                  data=[IPb_addr6_hex,IPb_addr7_hex,IPb_addr8_hex,0xa], 
                                                  reg = ["IPb_addr6","IPb_addr7","IPb_addr8","IPb_addr9"], 
                                                  out_msg = out_msg)     
        except:
            reqmsg = 0
        #read the response
        _frame  =  self.read_elink_message(reg = ["IPb_addr0","IPb_addr1","IPb_addr2"],
                                                       subindex=subindex, 
                                                       out_msg = out_msg) 
        
        hw.dispatch()
        cobid_ret, msg_ret,respmsg_ret, responsereg_ret, t = _frame
        if (not all(m is None for m in _frame[0:2])):
           data_ret, messageValid, status,respmsg, responsereg  =  self.check_valid_message(nodeId=nodeId,
                                                                                             index=index, 
                                                                                             subindex=subindex,
                                                                                             cobid_ret=cobid_ret,
                                                                                             data_ret=msg_ret,
                                                                                             SDO_TX=SDO_TX, SDO_RX=SDO_RX,
                                                                                             seu_test = seu_test)
           if responsereg is None: 
               responsereg = responsereg_ret 
               respmsg = respmsg_ret 
           # Check command byte
           if msg_ret[0] == (0x80):
                status =0
                abort_code = int.from_bytes(msg_ret[4:], 'little')
                self.logger.error(f'Received SDO abort message while reading '
                                  f'object {index:04X}:{subindex:02X} of node '
                                  f'{nodeId} with abort code {abort_code:08X}')
                if requestreg is not None: return None, reqmsg, hex(requestreg),respmsg, responsereg, status
                else : return None, reqmsg, requestreg,respmsg, responsereg, status          
           else:
                return data_ret , reqmsg, hex(requestreg), respmsg, responsereg  , status  
        
        else:
            status = 0
            if responsereg is not None: return None, reqmsg, hex(responsereg),respmsg, responsereg, status
            else : return None, reqmsg, hex(requestreg),respmsg, responsereg, status   

                                
    def build_data_tra_elink(self,bus = None, cobid = None, index=None, subindex=None,msg_0 =0x40,seu_test = None):
        """
        Build an SDO request message.
    
        Parameters:
        - bus: Bus identifier.
        - cobid: COBID value.
        - index: Index value.
        - subindex: Subindex value.
        - msg_0: Message 0 value.
        - seu_test: Flag indicating whether it's a single event upset test.
    
        Returns:
        - tuple: A tuple containing the hexadecimal values for registers 6, 7, 8, and the request register.
    
        Usage:
        # Example usage with required parameters
        IPb_addr6_hex, IPb_addr7_hex, IPb_addr8_hex, requestreg = build_data_tra_elink(bus=1, cobid=0x600, index=0x1234, subindex=0x01, msg_0=0x40, seu_test=False)
        """

        max_data_bytes = 8
        msg = [0 for i in range(max_data_bytes)]
        msg[0] = msg_0
        msg[1], msg[2] = index.to_bytes(2, 'little')
        msg[3] = subindex
        msg_bin_0 = bin(msg[0])[2:].zfill(8)
        msg_bin_1 = bin(msg[1])[2:].zfill(8)
        msg_bin_2 = bin(msg[2])[2:].zfill(8)
        msg_bin_3 = bin(msg[3])[2:].zfill(8)
        IPb_addr6_hex = Analysis().binToHexa(bin(cobid)[2:].zfill(12)#12bits
                                        +msg_bin_0#8bits
                                        +msg_bin_2#8bits
                                        +msg_bin_1[0:4]#4bits
                                        )
        if seu_test: data = bin(0xA)[2:].zfill(8)
        else:  data = bin(0)[2:].zfill(8)
        IPb_addr7_hex = Analysis().binToHexa(msg_bin_1[4:8]#4bits
                                        +msg_bin_3#8bits
                                        +bin(bus)[2:].zfill(8)#8bits
                                        +data#8bits
                                        +bin(0)[2:].zfill(4))#4bits
                                                
        IPb_addr8_hex = Analysis().binToHexa(bin(0)[2:].zfill(32))
        
        requestreg = Analysis().binToHexa(bin(cobid)[2:].zfill(12)#12bits
                                        +msg_bin_0#8bits
                                        +msg_bin_2#8bits
                                        +msg_bin_1#bin(0)[2:].zfill(4)#4bits
                                        #+bin(0)[2:].zfill(4)#4bits
                                        +msg_bin_3#8bits
                                        +bin(bus)[2:].zfill(8)#8bits
                                        +bin(0)[2:].zfill(8)#it was msg_bin_1 8bits
                                        +bin(0)[2:].zfill(4)
                                        +bin(0)[2:].zfill(32))
        return IPb_addr6_hex, IPb_addr7_hex, IPb_addr8_hex, requestreg
    
    
    def create_mopshub_adc_data_file(self,outputname, outputdir):
        """
        Create a MopsHub ADC data file.
    
        Parameters:
        - outputname: Name of the output file.
        - outputdir: Directory to save the output file.
    
        Returns:
        - tuple: A tuple containing the CSV writer and the output file CSV.
    
        Usage:
        # Example usage with required parameters
        csv_writer, out_file_csv = create_mopshub_adc_data_file(outputname="data.csv", outputdir="/path/to/directory")
        """
        # Write header to the data
        fieldnames = ['Times','elabsed_time',"test_tx",'bus_id',"nodeId","adc_ch","index","sub_index","adc_data", "adc_data_converted","reqmsg","requestreg","respmsg","responsereg", "status"]
        csv_writer,out_file_csv = AnalysisUtils().build_data_base(fieldnames=fieldnames,outputname = outputname, directory = outputdir)        
        return csv_writer,out_file_csv
    
    def read_mopshub_adc_channels(self, hw= None, bus_range= None, file= None, config_dir= None,outputname= None, outputdir= None , nodeIds= None,
                                  csv_writer= None, csv_file = None, seu_test =None):
        """
        Read ADC channels of MopsHub.
    
        Parameters:
        - hw: HwInterface object representing the hardware interface.
        - bus_range: Range of bus identifiers.
        - file: Name of the YAML configuration file.
        - config_dir: Directory containing the configuration file.
        - outputname: Name of the output file.
        - outputdir: Directory to save the output file.
        - nodeIds: List of node IDs to read ADC channels from.
        - csv_writer: CSV writer object to write data to the output file.
        - csv_file: Output file CSV object.
        - seu_test: Flag indicating whether it's a single event upset test.
    
        Returns:
        - None
    
        Usage:
        # Example usage with required parameters
        read_mopshub_adc_channels(hw=my_hw, bus_range=[1, 2], file="config.yml", config_dir="/path/to/config", outputname="output.csv", outputdir="/path/to/output", nodeIds=[1, 2],timeout=1, csv_writer=my_csv_writer, csv_file=my_csv_file, seu_test=False)
        """ 
        self.logger.info(f'Reading ADC channels of Mops with ID {nodeIds}')
        def exit_handler():
        # This function will be called on script termination
            self.logger.warning("Script interrupted. Closing the program.")
            sys.exit(0)
            
        dev = AnalysisUtils().open_yaml_file(file=file, directory=config_dir)
        # yaml file is needed to get the object dictionary items
        _adc_channels_reg = dev["adc_channels_reg"]["adc_channels"]
        _adc_index = list(dev["adc_channels_reg"]["adc_index"])[0]
        _channelItems = [int(channel) for channel in list(_adc_channels_reg)]
        # Write header to the data
        atexit.register(exit_handler)
        monitoringTime = time.time()
        i = 0
        file_time_now = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        try :  
            while True:
                #user_input = input("Press Enter to finish: ")  
                i = i+1
                for bus in bus_range:
                    for node in nodeIds:    
                        # Read ADC channels
                        #for c in tqdm(np.arange(len(_channelItems)),colour="green"):
                        for c in np.arange(len(_channelItems)):
                            channel =  _channelItems[c]
                            subindex = channel - 2
                            data_point, reqmsg, requestreg, respmsg,responsereg , status =  self.read_sdo_uhal(hw =hw,
                                                                                                               bus = bus, 
                                                                                                               nodeId= node, 
                                                                                                               index = int(_adc_index, 16), 
                                                                                                               subindex = subindex, 
                                                                                                               seu_test = seu_test,
                                                                                                               out_msg = False)                   
                            ts = time.time()
                            elapsedtime = ts - monitoringTime
                            if data_point is not None:
                                adc_converted = Analysis().adc_conversion(_adc_channels_reg[str(channel)], data_point)
                                adc_converted = round(adc_converted, 3)
                                self.logger.report(f'[{i}|{bus}] Got data for channel {channel} [{hex(subindex)}]: = {adc_converted}')
                            else:
                                adc_converted = None
                            csv_writer.writerow((str(file_time_now),
                                                 str(elapsedtime),
                                                 str(1),
                                                 str(bus),
                                                 str(node),
                                                 str(channel),
                                                 str(_adc_index),
                                                 str(subindex),
                                                 str(data_point),
                                                 str(adc_converted),
                                                 str(reqmsg),
                                                 str(requestreg), 
                                                 str(respmsg),
                                                 str(responsereg), 
                                                 status))
                            csv_file.flush() # Flush the buffer to update the file
        except (KeyboardInterrupt):
            #Handle Ctrl+C to gracefully exit the loop
            self.logger.warning("User interrupted. Closing the program.")
        finally:
            ts = time.time()
            elapsedtime = ts - monitoringTime
            csv_writer.writerow((str(file_time_now),
                         str(elapsedtime),
                         str(1),
                         str(None),
                         str(None),
                         str(None),
                         str(None),
                         str(None),
                         str(None),
                         str(None),
                         str(None),
                         str(None), 
                         str(None),
                         str(None), 
                         "End of Test"))    
            csv_file.close()
            self.logger.info(f'No. of invalid responses = {self.__cnt["messageValid"]}|| No. of failed responses = {self.__cnt["messageFailed_response"]}')
            self.logger.notice("ADC data are saved to %s/%s" % (outputdir,outputname))
        
        return None
    # Setter and getter functions
    def set_uhal_hardware(self, x):
        self.__hw = x

    def set_nodeList(self, x):
        self.__nodeList = x
    
    def set_channelPorts(self, x):
        self.__UHAL_channels = x
            
    def set_channel(self, x):
        self.__channel = x
    
    def set_ipAddress(self, x):
        self.__ipAddress = x
        
    def set_bitrate(self, bitrate):
        if self.__interface == 'Kvaser':
            self.__bitrate = bitrate
        else:
            self.__bitrate = bitrate 
 
    def set_sample_point(self, x):
        self.__sample_point = float(x)
                   
    def get_DllVersion(self):
        ret = analib.wrapper.dllInfo()
        return ret
    
    def get_nodeList(self):
        return self.__nodeList

    def get_channelPorts(self):
        return self.__UHAL_channels
        
    def get_bitrate(self):
        return self.__bitrate

    def get_sample_point(self):
        return self.__sample_point
        
    def get_ipAddress(self):
        """:obj:`str` : Network address of the AnaGate partner. Only used for
        AnaGate UHAL interfaces."""
        if self.__interface == 'Kvaser':
            raise AttributeError('You are using a Kvaser UHAL interface!')
        return self.__ipAddress

    def get_uhal_hardware(self):
        return self.__hw
    
    def get_channel(self):
        """:obj:`int` : Number of the crurrently used |UHAL| channel."""
        return self.__channel
           
    def get_channelState(self, channel):
        return channel.state

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_type is KeyboardInterrupt:
            self.logger.warning('Received Ctrl+C event (KeyboardInterrupt).')
        else:
            self.logger.exception(exception_value)
        self.stop()
        logging.shutdown()
        return True
           
    @property
    def lock(self):
        """:class:`~threading.Lock` : Lock object for accessing the incoming
        message queue :attr:`uhalMsgQueue`"""
        return self.__lock

    @property
    def uhalMsgQueue(self):
        """:class:`collections.deque` : Queue object holding incoming |UHAL|
        messages. This class supports thread-safe adding and removing of
        elements but not thread-safe iterating. Therefore the designated
        :class:`~threading.Lock` object :attr:`lock` should be acquired before
        accessing it.

        The queue is initialized with a maxmimum length of ``1000`` elements
        to avoid memory problems although it is not expected to grow at all.

        This special class is used instead of the :class:`queue.Queue` class
        because it is iterable and fast."""
        return self.__uhalMsgQueue
    
    @property
    def kvaserLock(self):
        """:class:`~threading.Lock` : Lock object which should be acquired for
        performing read or write operations on the Kvaser |UHAL| channel. It
        turned out that bad things UHAL happen if that is not done."""
        return self.__kvaserLock

    @property
    def cnt(self):
        """:class:`~collections.Counter` : Counter holding information about
        quality of transmitting and receiving. Its contens are logged when the
        program ends."""
        return self.__cnt

    @property
    def pill2kill(self):
        """:class:`threading.Event` : Stop event for the message collecting
        method :meth:`read_UHAL_message_thread`"""
        return self.__pill2kill
    
    # @property
    def channel(self):
        """Currently used |UHAL| channel. The actual class depends on the used
        |UHAL| interface."""
        return self.ch0

    @property
    def bitRate(self):
        """:obj:`int` : Currently used bit rate. When you try to change it
        :func:`stop` will be called before."""
        if self.__interface == 'Kvaser':
            return self.__bitrate
        else:
            return self.ch0.baudrate
     
    @bitRate.setter
    def bitRate(self, bitrate):
        if self.__interface == 'Kvaser':
            self.stop()
            self.__bitrate = bitrate
            self.start()
        else:
            self.ch0.baudrate = bitrate     

def main():
    """Wrapper function for using the server as a command line tool

    The command line tool accepts arguments for configuring the server which
    are transferred to the :class:`UHALWrapper` class.
    """

    # Parse arguments
    parser = ArgumentParser(description='UHALMOPS Interpreter for MOPS chip',
                            epilog='For more information contact '
                            'ahmed.qamesh@cern.ch',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    
    parser.set_defaults(interface='socketUHAL')
    # UHAL interface
    CGroup = parser.add_argument_group('UHAL interface')
    iGroup = CGroup.add_mutually_exclusive_group()
    iGroup.add_argument('-K', '--kvaser', action='store_const', const='Kvaser',
                        dest='interface',
                        help='Use Kvaser UHAL interface (default). When no '
                        'Kvaser interface is found or connected a virtual '
                        'channel is used.')
    iGroup.add_argument('-A', '--anagate', action='store_const',
                        const='AnaGate', dest='interface',
                        help='Use AnaGate Ethernet UHAL interface')
    
    iGroup.add_argument('-S', '--socketUHAL', action='store_const',
                        const='socketUHAL', dest='interface',
                        help='Use socketUHAL  interface')
    
    # UHAL settings group
    cGroup = parser.add_argument_group('UHAL settings')
    cGroup.add_argument('-c', '--channel', metavar='CHANNEL',
                        help='Number of UHAL channel to use', 
                        default=0)
    
    cGroup.add_argument('-i', '--ipaddress', metavar='IPADDRESS',
                        default='192.168.1.254', dest='ipAddress',
                        help='IP address of the AnaGate Ethernet UHAL '
                        'interface')
    cGroup.add_argument('-b', '--bitrate', metavar='BITRATE',
                        default=125000,
                        help='UHAL bitrate as integer in bit/s')

    cGroup.add_argument('-sp', '--samplePoint', metavar='SAMPLEPOINT',
                        default=0.5,
                        help='UHAL sample point in decimal')

    cGroup.add_argument('-sjw', '--sjw', metavar='SJW',
                        default=4,
                        help='Synchronization Jump Width')
    
    cGroup.add_argument('-tseg1', '--tseg1', metavar='tseg1',
                        default=0,
                        help='Time Segment1')
    
    cGroup.add_argument('-tseg2', '--tseg2', metavar='tseg2',
                        default=0,
                        help='Time Segment2')
            
    cGroup.add_argument('-nodeid', '--nodeid', metavar='nodeid',
                        default=0,
                        help='Node Id of the MOPS chip under test')
        
    # Logging configuration
    lGroup = parser.add_argument_group('Logging settings')
    lGroup.add_argument('-cl', '--console_loglevel',
                        choices={'NOTSET', 'SPAM', 'DEBUG', 'VERBOSE', 'INFO',
                                 'NOTICE', 'SUCCESS', 'WARNING', 'ERROR',
                                 'CRITICAL'},
                        default='INFO',
                        help='Level of console logging')

    args = parser.parse_args()
    
    # Start the server
    wrapper = UHALWrapper(**vars(args))  

if __name__ == "__main__":
    main()      