"""
*************************************************************************
TU-Seminar 2021 //. i n t e r s p e c i f i c s
Module 01 Bioelectricity S2. Energy Bending Lab


a) receive serial-port incoming data from arduino
b) if active, record incoming data to file
c) send incoming voltage reading as osc

*************************************************************************
"""

# import external libraries
import time
import serial
import numpy as np
from oscpy.client import OSCClient

# setup the serial port
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate = 115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# setup osc connection
#OSC_HOST = "192.168.1.250"
OSC_HOST ="25.5.244.74"
OSC_PORT = 8000
OSC_CLIENT = OSCClient(OSC_HOST, OSC_PORT)

#variables
in_line = 0
data = []
sc = 0

past_r = 0
actual_r = 0



# loop -------- >
while (True):
    in_line = ser.readline().decode()
    in_line = in_line.strip().rstrip()
    try:
        data = [float(v) for v in in_line.split(',')]
        print("{} | {} | {}".format(data[0],data[1],data[2]))
    except:
        continue
    sc += 1
    actual_r = data[2]
    if (actual_r == 1 and past_r == 0):
        namefile = "record.csv"
        fo = open(namefile, 'w')
    if (actual_r==0 and past_r==1):
        fo.close()
    if(actual_r == 1):
        aux = "{},{}\n".format(data[0],data[1])
        fo.write(aux)
        past_r = actual_r
    #buff.clear()
    #sc = 0
    # < >
println("[-_-] exit status: 0")

