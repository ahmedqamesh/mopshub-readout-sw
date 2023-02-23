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
from logger_main   import Logger
from analysis_utils import AnalysisUtils
from analysis import Analysis
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
logger = Logger().setup_main_logger(name = " Lib Check ",console_loglevel=logging.INFO, logger_file = False)

rootdir = os.path.dirname(os.path.abspath(__file__))
config_dir = "config_files/"
lib_dir = rootdir[:-8]

class UHALWrapper(object):#READSocketcan):#Instead of object

    def __init__(self,
                 file_loglevel=logging.INFO, 
                 logdir=None,load_config = False, 
                 logfile = None,
                 console_loglevel=logging.INFO):
       
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
        self.logger = Logger().setup_main_logger(name = "UHAL Wrapper",console_loglevel=console_loglevel, logger_file = False)
        
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
        if logfile is not None:
            ts = os.path.join(logdir, time.strftime('%Y-%m-%d_%H-%M-%S_UHAL_Wrapper.'))
            self.logger.info(f'Existing logging Handler: {ts}'+'log')
            self.logger_file = Logger().setup_file_logger(name = "UHALWrapper",console_loglevel=console_loglevel, logger_file = ts)#for later usage
            self.logger_file.success('....Done Initialization!')
    
    def set_hw_connection(self):
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
        hw.dispatch()
        return node

    def load_settings_file(self):
        filename = lib_dir + config_dir + "main_settings.yml"
        filename = os.path.join(lib_dir, config_dir + "main_settings.yml")
        test_date = time.ctime(os.path.getmtime(filename))
        # Load settings from CAN settings file
        self.logger.notice("Loading bus settings from the file %s produced on %s" % (filename, test_date))
        try:
            _channelSettings = AnalysisUtils().open_yaml_file(file=config_dir + "main_settings.yml", directory=lib_dir)
            _uri = _channelSettings['ethernet']["uri"]
            _addressFilePath = _channelSettings['ethernet']["addressFilePath"]
            return _uri,_addressFilePath
        except:
          self.logger.error("uri %s settings Not found" % (_uri)) 
          return None,None

    def read_uhal_message(self, hw = None, node =None, registerName=None, timeout=None, out_msg = True):
        reg_value = node.read()
        # Send IPbus transactions
        hw.dispatch()
        time.sleep(timeout)
        if out_msg:  self.logger.info(f'Read {registerName} Value = {hex(reg_value.value())}')
        return reg_value

    def write_uhal_message(self,hw =None, node =None, data=None, registerName=None, timeout=None, out_msg = True ):
        if out_msg : self.logger.info(f'writing {hex(data)} to reg {registerName}') 
        reqmsg = 0
        node.write(data)
        # Send IPbus transactions
        hw.dispatch()
        time.sleep(timeout)
        reqmsg= 1
        return reqmsg                                     

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
        if out_msg: self.logger.info("Writing data to registers %s"%reg)
        nodes = []
        reqmsg = 0
        for r in reg: nodes = np.append(nodes,self.get_ual_node(hw =hw, registerName = r))
        [self.write_uhal_message(hw =hw,node =nodes[data.index(d)], data=d, registerName=r, timeout=timeout, out_msg=out_msg) for r,d in zip(nodes,data)]
        reqmsg = 1
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
        count, count_limit = 0, 5
        #irq_tra_sig = 0x0
        while (count !=count_limit):
            irq_tra_sig =   self.read_uhal_message(hw = hw, 
                                                    node =self.get_ual_node(hw =hw, registerName = "reg3"),
                                                    registerName="reg3", timeout=timeout, out_msg = None)
            count= count+1
            if out_msg: self.logger.info(f'Read irq_tra_sig =  {irq_tra_sig} Count ({count})')
            time.sleep(timeout)
            if irq_tra_sig >=0x1:break
        #Read data  from FIFO        
        if irq_tra_sig>0x0:
            found_msg =True
            if out_msg: self.logger.info(f'Found Message in the buffer (irq_tra_sig = {irq_tra_sig})')
            self.write_uhal_message(hw = hw, 
                                         node =self.get_ual_node(hw =hw, registerName = "reg10"), 
                                         registerName="reg10", 
                                         data = 0x1, 
                                         timeout=timeout, out_msg = False)  
        else: 
            found_msg = False
            self.logger.info(f'Nothing Found in the buffer (irq_tra_sig = {irq_tra_sig})')
        return found_msg 
    
    def read_uhal_mopshub_message(self, reg =None, timeout=None, out_msg = True):
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
                time.sleep(timeout)
                if out_msg: self.logger.info(f'Read reg {r} Value = {hex(reg_value.value())}')
                reg_values = np.append(reg_values,hex(reg_value.value()))    
            respmsg = 1
            t = time.time()
            data, responsereg =  self.build_response_sdo_msg(reg = reg_values ,out_msg=out_msg)      
            cobid = int(data[0],16)
            data_ret = [0 for b in np.arange(len(data)-1)]
            for i in np.arange(len(data_ret)): data_ret[i] = int(data[i+1],16)
            if out_msg: self.dumpMessage(cobid, data_ret, t)
            self.__uhalMsgQueue.appendleft((cobid, data_ret, t))
            return cobid, bytearray(data_ret), respmsg, hex(responsereg), t
        else:
            respmsg = 0
            self.cnt["mopshub_response"] =self.cnt["mopshub_response"]+ 1
            return None, None, respmsg, None, None
        
    def  return_valid_message(self, nodeId, index, subindex, cobid_ret, data_ret, SDO_TX, SDO_RX,timeout):
        messageValid = False
        status = 0
        respmsg, responsereg = None, None
        messageValid_queue = False
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < 3000 / 1000 and messageValid_queue == False:
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
            for i in range(nDatabytes): 
                data.append(data_ret[4 + i])
            return int.from_bytes(data, 'little'), messageValid_queue, status, respmsg, responsereg
        else:
            status = 0
            self.logger.info(f'SDO read response timeout (node {nodeId}, index'
                 f' {index:04X}:{subindex:02X})')
            self.__cnt["messageInvalid_queue"]=self.__cnt["messageInvalid_queue"]+1
            return None, messageValid_queue, status, respmsg, responsereg

    def read_sdo_uhal(self, hw = None,bus= None, nodeId=None, index=None, subindex=None, timeout=1, SDO_TX=0x600, SDO_RX=0x580,out_msg=None):
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
        if nodeId is None or index is None or subindex is None:
            self.logger.warning('SDO read protocol cancelled before it could begin.')               
            self.cnt['SDO read total'] += 1
            return None, None, None,None, None, status 
        
        #build Payload in a CAN SDO format
        reg6_hex, reg7_hex, reg8_hex, requestreg = self.build_request_sdo_msg(cobid = SDO_TX+nodeId, bus = bus,  index=index, subindex=subindex)
        #write the Request to the Socket
        try:
            reqmsg =  self.write_uhal_mopshub_message(hw =hw, 
                                                  data=[reg6_hex,reg7_hex,reg8_hex,0x10000000], 
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
        if (not all(m is None for m in _frame)):
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
                else : return None, reqmsg, hex(requestreg),respmsg, responsereg, status          
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
                                        +bin(0)[2:].zfill(4)#4bits
                                        )
        
        reg7_hex = Analysis().binToHexa(bin(0)[2:].zfill(4)#4bits
                                        +msg_bin_3#8bits
                                        +bin(bus)[2:].zfill(8)#8bits
                                        +msg_bin_1#8bits
                                        +bin(0)[2:].zfill(4))#4bits
                                        
        reg8_hex = Analysis().binToHexa(bin(0)[2:].zfill(32))
        
        requestreg = Analysis().binToHexa(bin(cobid)[2:].zfill(12)#12bits
                                        +msg_bin_0#8bits
                                        +msg_bin_2#8bits
                                        +bin(0)[2:].zfill(4)#4bits
                                        +bin(0)[2:].zfill(4)#4bits
                                        +msg_bin_3#8bits
                                        +bin(bus)[2:].zfill(8)#8bits
                                        +msg_bin_1#8bits
                                        +bin(0)[2:].zfill(4)
                                        +bin(0)[2:].zfill(32))
        return reg6_hex, reg7_hex, reg8_hex, requestreg
    
    
    def read_mopshub_adc_channels(self, hw, bus_range, file, directory , nodeId, outputname, outputdir, n_readings,timeout):
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
        fieldnames = ['time',"test_tx",'bus_id',"nodeId","adc_ch","index","sub_index","adc_data", "adc_data_converted","reqmsg","requestreg","respmsg","responsereg", "status"]
        csv_writer = AnalysisUtils().build_data_base(fieldnames=fieldnames,outputname = outputname, directory = outputdir)
        for point in np.arange(0, n_readings): 
            for bus in bus_range:
                # Read ADC channels
                for c in tqdm(np.arange(len(_channelItems)),colour="green"):
                #for c in np.arange(len(_channelItems)):
                    channel =  _channelItems[c]
                    subindex = channel - 2
                    monitoringTime = time.time()
                    data_point, reqmsg, requestreg, respmsg,responsereg , status =  self.read_sdo_uhal(hw = hw,
                                                                                                          bus = bus, 
                                                                                                          nodeId= nodeId, 
                                                                                                          index = int(_adc_index, 16), 
                                                                                                          subindex = subindex, 
                                                                                                          timeout = timeout,
                                                                                                          out_msg = None)                   
                    
                    #await asyncio.sleep(0.1)
                    time.sleep(timeout*2)
                    ts = time.time()
                    elapsedtime = ts - monitoringTime
                    if data_point is not None:
                        adc_converted = Analysis().adc_conversion(_adc_channels_reg[str(channel)], data_point)
                        adc_converted = round(adc_converted, 3)
                        self.logger.info(f'Got data for channel {channel}: = {adc_converted}')
                    else:
                        adc_converted = 0
                    csv_writer.writerow((str(elapsedtime),
                                         str(1),
                                         str(bus),
                                         str(nodeId),
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
        
        self.logger.info(f'No. of invalid responses = {self.__cnt["messageInvalid_queue"]}|| No. of failed responses {self.cnt["mopshub_response"]}')
        self.logger.notice("ADC data are saved to %s/%s" % (outputdir,outputname))

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
            time.sleep(random.random())  
               
if __name__ == "__main__":
    main()      
    
    ProducerThread().start()
    ConsumerThread().start()  