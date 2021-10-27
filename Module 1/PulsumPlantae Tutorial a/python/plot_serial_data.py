"""
**************************************************************
TU-Seminar 2021 //. i n t e r s p e c i f i c s .
Module 01 Bioelectricity
Tutorial A_ Plotting serial data

a) receive serial-port incoming data from arduino
b) shows incoming values as a bar graph in terminal
c) calculates and plot the FFT 

****************************************************************
"""



# external modules
import time
import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy import fftpack

# setup the serial port
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate = 115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

#variables
in_line = 0
data = []
nodata = []
buff = []
dc = 0
sc = 0
Fs = 100
t = np.arange(0,1,1/Fs)
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(15,5))
plt.ylim(0,100)

# functions
def numbars(n):
    return (''.join(['█' for i in range(int(n+1))]))


# loop -------- >
while (True):
    in_line = ser.readline().decode()
    in_line = in_line.strip().rstrip()
    try:
        data = [int(v) for v in in_line.split(',')]
        nodata = [numbars(int(v)/100) for v in in_line.split(',')]
        buff.append(data[0])
        #print (undata)
        #print("|{} |{} |{}".format(undata[0].ljust(11),undata[1].ljust(11),undata[2].ljust(11)))
        #print("{ }/{}/{}".format(data[0],data[1],data[2]))
        print("|{} |".format(nodata[0].ljust(11)))
    except:
        continue
    sc += 1
    if (len(buff)>100):
        _d = buff.pop(0)
    #analize, then update plot
    if (sc>100 and sc%10==0):
        buff_array = np.array(buff, dtype=float)        
        buff_fft = fftpack.fft(buff_array)
        n = 24
        fr = 1 + (n) * np.linspace(0,1,n)
        buff_m = 2/n * abs(buff_fft[1:n+1])

        ax[0].clear()
        ax[1].clear()
        ax[0].plot(t, buff)    # samples
        ax[1].stem(fr, buff_m) # freq response
        plt.draw()
        plt.pause(0.0001)
        #buff.clear()
        #sc = 0
        # < >
println("[-_-] exit status: 0")
