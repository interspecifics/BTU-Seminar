"""
**************************************************************
TU-Seminar 2021 //. i n t e r s p e c i f i c s .
Module 01 Bioelectricity
Tutorial A_ Receiving serial data

a) receive serial-port incoming data from arduino
b) shows incoming values as a bar graph in terminal

****************************************************************
"""

# external modules
import time
import serial

# setup the serial port
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate = 115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# variables
in_line = 0
data = []
nodata = []
sc = 0

# a function to draw bars
def numbars(n):
    return (''.join(['█' for i in range(int(n+1))]))

# loop -------- > 
while (True):
    in_line = ser.readline().decode()
    in_line = in_line.strip().rstrip()
    try:
        data = [int(v) for v in in_line.split(',')]
        nodata = [numbars(int(v)/100) for v in in_line.split(',')]
        print("|{} |".format(nodata[0].ljust(11)))
        #print("{} | {} | {}".format(data[0],data[1],data[2]))
        #print("|{} |{} |{}".format(nodata[0].ljust(11),nodata[1].ljust(11),nodata[2].ljust(11)))
    except:
        continue
    # < >
    sc += 1
println("[-_-] exit status: 0")
