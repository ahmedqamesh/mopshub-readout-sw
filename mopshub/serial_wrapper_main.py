import binascii
import os
import serial
from serial.tools import list_ports
import time
import numpy as np
from clint.textui import colored
try:
    from logger_main   import Logger
    from design_info   import DesignInfo
except (ImportError, ModuleNotFoundError):
    from .logger_main   import Logger
    from .design_info   import DesignInfo
import sys   
import logging
import re
import subprocess
sm_info = DesignInfo()

log_format = '%(log_color)s[%(levelname)s]  - %(name)s -%(message)s'
log_call = Logger(log_format = log_format,name = "Serial Debug",console_loglevel=logging.INFO, logger_file = False)


class SerialServer(serial.Serial):

    def __init__(self, port=None, baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE,device = None):
        self.logger = log_call.setup_main_logger()
        #self.logger.info(f'Serial Settings : Port{port}, baudrate {baudrate}')
        port_detected = self.get_serial_port(device)
        if port_detected : port = port_detected[0]
        else: port = port
        try:
            super().__init__(port=port, baudrate=baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                             stopbits=serial.STOPBITS_ONE) 
        except Exception as e : 
            ports_return = self.avail_ports(msg = None)
            self.logger.error(f'Port{port} is not activated, The following ports are available {ports_return}')
            self.avail_ports(msg = True)
            sys.exit(1)
            
        self.__bytes_written = 0
     
    def avail_ports(self,msg = True):
        ports = serial.tools.list_ports.comports()
        ports_return = []
        for port in ports:
            ports_return.append(port.device)
            
            if msg:  self.logger.info(f'Port : {port.device} - {port.description} - {port.manufacturer} - {port.serial_number}')
        return ports_return

    def debug_mopshub_uart(self,read_sm = ["0","1","2","3","4","5","6","7"]):   
        return_states = []
        for sm_id in read_sm:
            #Write to Uart 
            self.tx_data(bytearray(bytes.fromhex("0"+sm_id)))
            # Read from Uart
            time.sleep(0.2)
            Byte = self.rx_data() #read one byte
            # print info
            return_states = np.append(return_states,int(Byte.hex(),16))
            sm_info.get_sm_info(sm_id = int(sm_id,16), return_state = Byte)
            time.sleep(0.5)
        return return_states
    
    def openServer(self):
        if not self.isOpen():
            self.open()
            
    def closeServer(self):
        if self.open():
            # Destructor, close port when serial port instance is freed
            self.__del__()
    def rx_data(self):
        #Byte = ser.readline()
        return self.read() #read one byte
    
    
    def tx_data(self, data):
        self.openServer()
        #ser.write('6'.encode())
        self.__bytes_written = self.write(data)

    def bytes_written(self):
        return self.__bytes_written


    def get_serial_port(self, vid_pid):
        ##
        # @return Array of compatible serial ports
        # @param vid_pid Vendor id, can be obtained via lsusb
        #
        # Provides all serial ports with vid_pid
        # Exits if no mathich port is found
        #
    
        list_ports.comports()
        temp = list(list_ports.grep(vid_pid))
        ports = []
        if(len(temp) == 0):
            self.logger.error('No matching USB device (' + colored.blue(vid_pid) + ') found!. Please check if Arty board is connected.')
        else:
            #self.logger.status('Found {:d} possible USB deivces'.format(len(temp)))
            for n in range(len(temp)):
                self.logger.status('Detect USB device ' + colored.blue(vid_pid) + ' at ' + colored.yellow(temp[n][0]))
                ports.append(temp[n][0])
        return ports


    def list_usb_ports(self):
        device_re = re.compile(b"Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
        df = subprocess.check_output("lsusb")
        devices = []
        for i in df.split(b'\n'):
            if i:
                info = device_re.match(i)
                if info:
                    dinfo = info.groupdict()
                    dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
                    devices.append(dinfo)
                    print(dinfo)
