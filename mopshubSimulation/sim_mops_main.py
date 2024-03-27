#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module provides a class for a CAN wrapper for the ADC channels of the MOPS Chip.
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
#import asyncio
#from asyncio.tasks import sleep
import sys
import os
from threading import Thread, Event, Lock
import subprocess
import threading
import numpy as np
rootdir = os.path.dirname(os.path.abspath(__file__)) 
sys.path.insert(0, rootdir+'/mopshub')
from mopshub.analysis       import Analysis
from mopshub.logger_main    import Logger 
from mopshub.analysis_utils import AnalysisUtils
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
#from csv import writer
log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format=log_format, name="Lib Check ", console_loglevel=logging.INFO, logger_file=False)


config_dir = "config_files/"
lib_dir = rootdir[:-8]

class SIMMOPS(object):#READSocketcan):#Instead of object

    def __init__(self,
                 file_loglevel=logging.INFO, 
                 logdir=None,load_config = False, 
                 logfile = None,
                 console_loglevel=logging.INFO,
                 mainWindow= False):
       
        super(UHALWrapper, self).__init__()  # super keyword to call its methods from a subclass:        
        #Initialize a watchdog (to be done)
        #Begin a thread settings (to be done)
        self.sem_read_block = threading.Semaphore(value=0)
        self.sem_recv_block = threading.Semaphore(value=0)
        self.sem_config_block = threading.Semaphore()
        
        """:obj:`~logging.Logger`: Main logger for this class"""
        if logdir is None:
            #'Directory where log files should be stored'
            logdir = os.path.join(lib_dir, 'log')                 
        
        self.logger = log_call.setup_main_logger()
        if load_config:
           # Read CAN settings from a file 
            self.__uri, self.__addressFilePath =   self.load_settings_file()          

        # Initialize library and set connection parameters
        self.__canMsgQueue = deque([], 100)  # queue with a size of 100 to queue all the messages in the bus
        self.__uhalMsgQueue = deque([], 100)
        self.__cnt = Counter()
        self.error_counter = 0
        self.__pill2kill = Event()
        self.__lock = Lock()     
        self.__hw = None
        self.logger.success('....Done Initialization!')
        self.__address_byte = [0x80, 0x88, 0x90, 0x98, 0x80]
        if logfile is not None:
            ts = os.path.join(logdir, time.strftime('%Y-%m-%d_%H-%M-%S_UHAL_Wrapper.'))
            self.logger.info(f'Existing logging Handler: {ts}'+'log')
            self.logger_file = Logger().setup_file_logger(name = "UHALWrapper",console_loglevel=console_loglevel, logger_file = ts)#for later usage
            self.logger_file.success('....Done Initialization!')
    
    def set_hw_connection(self):
        self.logger.info(f'Starting a Thread for MOPSHUB')
        self.__uhalMsgThread = Thread(target=self.read_uhal_mopshub_message, args=(["reg0","reg1","reg2"], 0.001,  None))#self.between_thread_callback)
        self.__uhalMsgThread.start()  
                               
    def between_thread_callback(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.call_back_read_uhal_mopshub_message())
    
    def call_back_read_uhal_mopshub_message(self):
        self.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], timeout=0.001, out_msg = None)
        
    def config_uhal_hardware(self, uri = None, addressFilePath = None):
        if uri is None:
            uri = self.__uri
        if addressFilePath is None: 
            addressFilePath = self.__addressFilePath 
        hw = uhal.getDevice("mopshub", uri, "file://" + addressFilePath)
        self.set_uhal_hardware(hw)
        self.set_hw_connection()
        return hw

    def get_ual_node(self, hw =None, registerName = None):
        node = hw.getNode(registerName)
        return node

    def load_settings_file(self, file="main_settings.yml"):
        """Load all the information related to the hardware 
        Parameters
        ----------
        file : :obj:`str` represents the yaml file name 
        """
        
        filename = lib_dir + config_dir + file
        filename = os.path.join(lib_dir, config_dir + file)
        test_date = time.ctime(os.path.getmtime(filename))
        # Load settings from bus settings file
        self.logger.notice("Loading bus settings from the file %s produced on %s" % (filename, test_date))
        try:
            _channelSettings = AnalysisUtils().open_yaml_file(file=config_dir + "main_settings.yml", directory=lib_dir)
            _uri = _channelSettings['ethernet']["uri"]
            _addressFilePath = _channelSettings['ethernet']["addressFilePath"]
            return _uri,_addressFilePath
        except:
          self.logger.error("uri %s settings Not found" % (_uri)) 
          return None,None

    def read_uhal_message(self, hw = None, node =None, registerName=None, timeout=None, out_msg = True, w_r= "Read"):
        """Read incoming UHAL messages without storing any Queue
        node: obj: uhal._core type 
        registerName: str: 
        """
        reg_value = node.read()
        # Send IPbus transactions
        hw.dispatch()
        if out_msg:  self.logger.info(f'{w_r} {hex(reg_value.value())} : {registerName}')
        return reg_value
    
    def write_uhal_mopshub_message(self, hw =None, data=None,reg =None, timeout=None, out_msg= True):
        """Combining writing functions for different |CAN| interfaces
        Parameters
        ----------
        data : :obj:`list` of :obj:`int` or :obj:`bytes`
            Data bytes

        timeout : :obj:`int`, optional
            |SDO| write timeout in milliseconds. When :data:`None` or not
            given an infinit timeout is used.
        """
        nodes = []
        reqmsg = 0
        for r in reg:
            nodes = np.append(nodes,self.get_ual_node(hw =hw, registerName = r))
        [self.write_uhal_message(hw =hw,node =nodes[data.index(d)], data=d, registerName=r, timeout=timeout, out_msg=out_msg) for r,d in zip(reg,data)]
        reqmsg = 1
        return reqmsg

    def write_uhal_message(self,hw =None, node =None, data=None, registerName=None, timeout=None, out_msg = True ):
        reqmsg = 0
        node.write(data)
        reqmsg= 1
        reg_ret_value = self.read_uhal_message(hw = hw, node =node, registerName=registerName, timeout=timeout, out_msg = out_msg, w_r= "Writing") 
        status = (hex(data) ==hex(reg_ret_value.value())) 
        if out_msg and not status:  self.logger.warning(f'Writing mismatch in {registerName} [W: {hex(data)} |R:{hex(reg_ret_value.value())}]') 
        # Send IPbus transactions
        hw.dispatch()
        #time.sleep(timeout)
        return reqmsg         
    
    def build_response_sdo_msg(self, reg =[], out_msg = True):
        # Data_rec_reg is 76 bits = sdo[12bits]+payload[32bits]+bus_id[5bits]++3bits0+8bits0+16bits0
        reg_values = []
        data_ret = [0 for b in np.arange(9)]    
        new_Bytes = [0 for b in np.arange(9)]    
        responsereg = Analysis().binToHexa(bin(int(reg[0],16))[2:].zfill(32) 
                                           +bin(int(reg[1],16))[2:].zfill(32) 
                                           +bin(int(reg[2],16))[2:].zfill(32))
        for r in reg: 
            try:
                reg_values = np.append(reg_values,hex(r))
            except:
                reg_values = np.append(reg_values,r)
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
    
 
    def dumpMessage(self, cobid, msg, t):
        """Dumps a uhal message to the screen and log file
        Parameters
        ----------
        cobid : :obj:`int`
            |CAN| identifier
        msg : :obj:`bytes`
            |CAN| data - max length 8
        t : obj'int'
        """
        msgstr = '{:3X} {:d}   '.format(cobid, 8)
        for i in range(len(msg)):
            msgstr += '{:02x}  '.format(msg[i])
        msgstr += '    ' * (8 - len(msg))
        st = datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S')
        msgstr += str(st)
        self.logger.info(msgstr)
                       
    def enable_read_signal (self,timeout =None, out_msg = None):
         #wait for interrupt signal from FIFO
        hw = self.get_uhal_hardware()
        count, count_limit = 0, 2
        #irq_tra_sig = 0x0
        while (count !=count_limit):
            irq_tra_sig =   self.read_uhal_message(hw = hw, 
                                                    node =self.get_ual_node(hw =hw, registerName = "reg3"),
                                                    registerName="reg3", timeout=timeout, out_msg = None)
            count= count+1
            if out_msg: self.logger.info(f'Read irq_tra_sig =  {irq_tra_sig} Count ({count})')
            time.sleep(0.001)
            if irq_tra_sig >=0x1:break
        #Read data  from FIFO        
        if irq_tra_sig>0x0:
            found_msg =True
            if out_msg: self.logger.info(f'Found Message in the buffer (irq_tra_sig = {irq_tra_sig})')
            # Start read elink
            self.write_uhal_message(hw = hw, 
                                         node =self.get_ual_node(hw =hw, registerName = "reg10"), 
                                         registerName="reg10", 
                                         data = 0x1, 
                                         timeout=timeout, out_msg = False)  
        else: 
            found_msg = False
            self.logger.warning(f'Nothing Found in the buffer (irq_tra_sig = {irq_tra_sig})')
        return found_msg 
    
    def read_uhal_mopshub_message(self, reg =None, timeout=None,  out_msg = True):
        hw = self.get_uhal_hardware()
        nodes = []
        reg_values = []
        respmsg = 0
        msg_found =  self.enable_read_signal(timeout= timeout, out_msg = out_msg)
        if msg_found:
            for r in reg: 
                nodes = np.append(nodes,self.get_ual_node(hw =hw, registerName = r))
                reg_value = nodes[reg.index(r)].read()
                # Send IPbus transactions
                hw.dispatch()
                #time.sleep(timeout)#The code has really developed afer commenting this line
                if out_msg: self.logger.info(f'Read {r} Value = {hex(reg_value.value())}')
                reg_values = np.append(reg_values,hex(reg_value.value()))    
            respmsg = 1
            t = time.time()
            data, responsereg =  self.build_response_sdo_msg(reg = reg_values, out_msg=out_msg)      
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
        
    def  return_valid_message(self, nodeId, index, subindex, cobid_ret, data_ret, SDO_TX, SDO_RX,timeout):
        messageValid = False
        status = 0
        respmsg, responsereg = 0, None
        messageValid_queue = False
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < 1 and messageValid_queue == False:
                # check the message validity [nodid, msg size,...]
                for i, (cobid_ret, data_ret, t) in zip(range(len(self.__uhalMsgQueue)), self.__uhalMsgQueue):
                    messageValid_queue = (cobid_ret == SDO_RX + nodeId
                                    and data_ret[0] in [0x80, 0x43, 0x47, 0x4b, 0x4f, 0x42] 
                                    and int.from_bytes([data_ret[1], data_ret[2]], 'little') == index
                                    and data_ret[3] == subindex) 
                    
                    
                    if (messageValid_queue):
                        del self.__uhalMsgQueue[i]
                        break
                if (messageValid_queue ==False):
                    _, _, respmsg, responsereg, _ = self.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], timeout=timeout, out_msg = None) 
                self.__uhalMsgThread.join()
        # The following are the only expected response    
        #
        # messageValid = (cobid_ret == SDO_RX + nodeId
        #                 and data_ret[0] in [0x80, 0x43, 0x47, 0x4b, 0x4f, 0x42] 
        #                 and int.from_bytes([data_ret[1], data_ret[2]], 'little') == index
        #                 and data_ret[3] == subindex)       
        if messageValid_queue:
            status = 1
            nDatabytes = 4 - ((data_ret[0] >> 2) & 0b11) if data_ret[0] != 0x42 else 4
            data = []
            for i in range(nDatabytes-1): 
                data.append(data_ret[4 + i])
            return int.from_bytes(data, 'little'), messageValid_queue, status, respmsg, responsereg
        else:
            status = 0
            self.logger.info(f'SDO read response timeout (node {nodeId}, index'
                 f' {index:04X}:{subindex:02X})')
            self.__cnt["messageInvalid_queue"]=self.__cnt["messageInvalid_queue"]+1
            return None, messageValid_queue, status, respmsg, responsereg
    
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
            time.sleep(0.02)                     
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
    
    
    def read_monitoring_uhal(self,hw =None, spi_reg =None, spi_select=None,cobid = 0X20, timeout=1,out_msg=None):
        status =0;
        respmsg, responsereg  = 0, None
        #build Payload in a CAN SDO format
        mon_reg6_hex = Analysis().binToHexa(bin(cobid)[2:].zfill(8)+
                                            bin(spi_select)[2:].zfill(8)+
                                            bin(spi_reg)[2:].zfill(8)+
                                            bin(0)[2:].zfill(8)) 
        reqmsg =  self.write_uhal_mopshub_message(hw =hw, 
                                              data=[mon_reg6_hex,0x0,0x0,0xa], 
                                              reg = ["reg6","reg7","reg8","reg9"], 
                                              timeout=timeout, 
                                              out_msg = out_msg)     
        #read the response from the socket
        _frame  =  self.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], 
                                                        timeout=timeout, 
                                                        out_msg = out_msg) 
        hw.dispatch()
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

    def read_sdo_uhal(self,hw= None, bus= None, nodeId=None, index=None, subindex=None, timeout=1, SDO_TX=0x600, SDO_RX=0x580,out_msg=None):
        """Read an object via |SDO|
    
        Currently expedited and segmented transfer is supported by this method.
        The function will writing the dictionary request from the master to the node then read the response from the node to the master
        The user has to decide how to decode the data.
    
        Parameters
        ----------
        nodeId : :obj:`int`
            The id from the node to read from
        index : :obj:`int`
            The Object Dictionary index to read from
        subindex : :obj:`int`
            |OD| Subindex. Defaults to zero for single value entries.
        timeout : :obj:`int`, optional
            |SDO| timeout in milliseconds
    
        Returns
        -------
        :obj:`list` of :obj:`int`
            The data if was successfully read
        :data:`None`
            In case of errors
        """
        status =0;
        respmsg, responsereg  = 0, None
        if nodeId is None or index is None or subindex is None:
            self.logger.warning('SDO read protocol cancelled before it could begin.')               
            self.__cnt["SDO read total"] = self.__cnt["SDO read total"]+1
            return None, None, None,respmsg, responsereg , status 
        hw =  self.get_uhal_hardware()
        #build Payload in a CAN SDO format
        reg6_hex, reg7_hex, reg8_hex, requestreg = self.build_request_sdo_msg(cobid = SDO_TX+nodeId, bus = bus,  index=index, subindex=subindex)

        #write the Request to the Socket
        try:
            reqmsg =  self.write_uhal_mopshub_message(hw =hw, 
                                                  data=[reg6_hex,reg7_hex,reg8_hex,0xa], 
                                                  reg = ["reg6","reg7","reg8","reg9"], 
                                                  timeout=timeout, 
                                                  out_msg = out_msg)     
        except:
            reqmsg = 0
        #read the response from the socket
        _frame  =  self.read_uhal_mopshub_message(reg = ["reg0","reg1","reg2"], 
                                                       timeout=timeout, 
                                                       out_msg = out_msg) 
        hw.dispatch()
        cobid_ret, msg_ret,respmsg_ret, responsereg_ret, t = _frame
        if (not all(m is None for m in _frame[0:2])):
           data_ret, messageValid, status,respmsg, responsereg  =  self.return_valid_message(nodeId=nodeId,
                                                                                             index=index, 
                                                                                             subindex=subindex,
                                                                                             cobid_ret=cobid_ret,
                                                                                             data_ret=msg_ret,
                                                                                             SDO_TX=SDO_TX, SDO_RX=SDO_RX,
                                                                                             timeout=timeout)
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

                                
    def build_request_sdo_msg(self,bus = None, cobid = None, index=None, subindex=None,msg_0 =0x40):
        max_data_bytes = 8
        msg = [0 for i in range(max_data_bytes)]
        msg[0] = msg_0
        msg[1], msg[2] = index.to_bytes(2, 'little')
        msg[3] = subindex
        msg_bin_0 = bin(msg[0])[2:].zfill(8)
        msg_bin_1 = bin(msg[1])[2:].zfill(8)
        msg_bin_2 = bin(msg[2])[2:].zfill(8)
        msg_bin_3 = bin(msg[3])[2:].zfill(8)
        reg6_hex = Analysis().binToHexa(bin(cobid)[2:].zfill(12)#12bits
                                        +msg_bin_0#8bits
                                        +msg_bin_2#8bits
                                        +msg_bin_1[0:4]#4bits
                                        )
        
        reg7_hex = Analysis().binToHexa(msg_bin_1[4:8]#4bits
                                        +msg_bin_3#8bits
                                        +bin(bus)[2:].zfill(8)#8bits
                                        +bin(0)[2:].zfill(8)#8bits
                                        +bin(0)[2:].zfill(4))#4bits
                                        
        reg8_hex = Analysis().binToHexa(bin(0)[2:].zfill(32))
        
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
        return reg6_hex, reg7_hex, reg8_hex, requestreg
    
    
    def create_mopshub_adc_data_file(self,outputname, outputdir):
        # Write header to the data
        fieldnames = ['time',"test_tx",'bus_id',"nodeId","adc_ch","index","sub_index","adc_data", "adc_data_converted","reqmsg","requestreg","respmsg","responsereg", "status"]
        csv_writer = AnalysisUtils().build_data_base(fieldnames=fieldnames,outputname = outputname, directory = outputdir)        
        return csv_writer
        
    def read_mopshub_adc_channels(self, hw, bus_range, file, directory,outputname, outputdir , nodeId, n_readings,timeout,csv_writer):
        """Start actual CANopen communication
        This function contains an endless loop in which it is looped over all
        ADC channels. Each value is read using
        :meth:`read_sdo_can_thread` and written to its corresponding
        """     
        self.logger.info(f'Reading ADC channels of Mops with ID {nodeId}')
        dev = AnalysisUtils().open_yaml_file(file=file, directory=directory)
        # yaml file is needed to get the object dictionary items
        _adc_channels_reg = dev["adc_channels_reg"]["adc_channels"]
        _adc_index = list(dev["adc_channels_reg"]["adc_index"])[0]
        _channelItems = [int(channel) for channel in list(_adc_channels_reg)]
        # Write header to the data
        #fieldnames = ['time',"test_tx",'bus_id',"nodeId","adc_ch","index","sub_index","adc_data", "adc_data_converted","reqmsg","requestreg","respmsg","responsereg", "status"]
        #csv_writer = AnalysisUtils().build_data_base(fieldnames=fieldnames,outputname = outputname, directory = outputdir)
        monitoringTime = time.time()
        for point in np.arange(0, n_readings): 
            for bus in bus_range:
                for node in nodeId:    
                    # Read ADC channels
                    for c in tqdm(np.arange(len(_channelItems)),colour="green"):
                        channel =  _channelItems[c]
                        subindex = channel - 2
                        data_point, reqmsg, requestreg, respmsg,responsereg , status =  self.read_sdo_uhal(hw =hw,
                                                                                                           bus = bus, 
                                                                                                           nodeId= node, 
                                                                                                           index = int(_adc_index, 16), 
                                                                                                           subindex = subindex, 
                                                                                                           timeout = timeout,
                                                                                                           out_msg = False)                   
                        
                        #time.sleep(0.01) #It makes no difference
                        ts = time.time()
                        elapsedtime = ts - monitoringTime
                        if data_point is not None:
                            adc_converted = Analysis().adc_conversion(_adc_channels_reg[str(channel)], data_point)
                            adc_converted = round(adc_converted, 3)
                            self.logger.info(f'[{point}] Got data for channel {channel} [{hex(subindex)}]: = {adc_converted}')
                        else:
                            adc_converted = None
                        csv_writer.writerow((str(elapsedtime),
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
        
        self.logger.info(f'No. of invalid responses = {self.__cnt["messageInvalid_queue"]}|| No. of failed responses = {self.__cnt["messageFailed_response-1"]}')
        #self.logger.notice("ADC data are saved to %s/%s" % (outputdir,outputname))

    # Setter and getter functions
    def set_uhal_hardware(self, x):
        self.__hw = x

    def set_nodeList(self, x):
        self.__nodeList = x
    
    def set_channelPorts(self, x):
        self.__can_channels = x
            
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
        return self.__can_channels
        
    def get_bitrate(self):
        return self.__bitrate

    def get_sample_point(self):
        return self.__sample_point
        
    def get_ipAddress(self):
        """:obj:`str` : Network address of the AnaGate partner. Only used for
        AnaGate CAN interfaces."""
        if self.__interface == 'Kvaser':
            raise AttributeError('You are using a Kvaser CAN interface!')
        return self.__ipAddress

    def get_uhal_hardware(self):
        """:obj:`str` : Vendor of the CAN interface. Possible values are
        ``'Kvaser'`` and ``'AnaGate'``."""
        return self.__hw
    
    def get_channel(self):
        """:obj:`int` : Number of the crurrently used |CAN| channel."""
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
        message queue :attr:`canMsgQueue`"""
        return self.__lock

    @property
    def canMsgQueue(self):
        """:class:`collections.deque` : Queue object holding incoming |CAN|
        messages. This class supports thread-safe adding and removing of
        elements but not thread-safe iterating. Therefore the designated
        :class:`~threading.Lock` object :attr:`lock` should be acquired before
        accessing it.

        The queue is initialized with a maxmimum length of ``1000`` elements
        to avoid memory problems although it is not expected to grow at all.

        This special class is used instead of the :class:`queue.Queue` class
        because it is iterable and fast."""
        return self.__canMsgQueue
    
    @property
    def kvaserLock(self):
        """:class:`~threading.Lock` : Lock object which should be acquired for
        performing read or write operations on the Kvaser |CAN| channel. It
        turned out that bad things can happen if that is not done."""
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
        method :meth:`read_can_message_thread`"""
        return self.__pill2kill
    
    # @property
    def channel(self):
        """Currently used |CAN| channel. The actual class depends on the used
        |CAN| interface."""
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
    are transferred to the :class:`CanWrapper` class.
    """

    # Parse arguments
    parser = ArgumentParser(description='CANMOPS Interpreter for MOPS chip',
                            epilog='For more information contact '
                            'ahmed.qamesh@cern.ch',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    
    parser.set_defaults(interface='socketcan')
    # CAN interface
    CGroup = parser.add_argument_group('CAN interface')
    iGroup = CGroup.add_mutually_exclusive_group()
    iGroup.add_argument('-K', '--kvaser', action='store_const', const='Kvaser',
                        dest='interface',
                        help='Use Kvaser CAN interface (default). When no '
                        'Kvaser interface is found or connected a virtual '
                        'channel is used.')
    iGroup.add_argument('-A', '--anagate', action='store_const',
                        const='AnaGate', dest='interface',
                        help='Use AnaGate Ethernet CAN interface')
    
    iGroup.add_argument('-S', '--socketcan', action='store_const',
                        const='socketcan', dest='interface',
                        help='Use socketcan  interface')
    
    # CAN settings group
    cGroup = parser.add_argument_group('CAN settings')
    cGroup.add_argument('-c', '--channel', metavar='CHANNEL',
                        help='Number of CAN channel to use', 
                        default=0)
    
    cGroup.add_argument('-i', '--ipaddress', metavar='IPADDRESS',
                        default='192.168.1.254', dest='ipAddress',
                        help='IP address of the AnaGate Ethernet CAN '
                        'interface')
    cGroup.add_argument('-b', '--bitrate', metavar='BITRATE',
                        default=125000,
                        help='CAN bitrate as integer in bit/s')

    cGroup.add_argument('-sp', '--samplePoint', metavar='SAMPLEPOINT',
                        default=0.5,
                        help='CAN sample point in decimal')

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
    wrapper = CanWrapper(**vars(args))  

class ConsumerThread(Thread):
    def run(self):
        global queue
        while True:
            lock.acquire()
            if not queue:
                print ("Nothing in queue, but consumer will try to consume")
            num = queue.pop(0)
            print ("Consumed", num) 
            lock.release()
            #time.sleep(random.random())  
               
if __name__ == "__main__":
    main()      
    
    ProducerThread().start()
    ConsumerThread().start()  