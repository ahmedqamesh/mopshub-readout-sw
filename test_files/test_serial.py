import sys
import os
import serial
import time               
            
def read_sem():
    bitrate = 115200#9600
    #Digilent_Digilent_USB_Device_210319A279BE
    with serial.Serial('/dev/ttyUSB1', parity=serial.PARITY_NONE,baudrate= bitrate, timeout=1
                       , bytesize=serial.EIGHTBITS,
                       stopbits=serial.STOPBITS_ONE) as ser:
        while True:
            
            Byte = ser.read() #read one byte
            #Byte = ser.readline()
            
            print(Byte)
            #ser.write(b'hello',s)
            

if __name__ == "__main__":
    read_sem()
   