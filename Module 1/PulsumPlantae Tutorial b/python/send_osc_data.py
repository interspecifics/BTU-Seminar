"""
*************************************************************************
TU-Seminar 2021 //. i n t e r s p e c i f i c s
Module 01 Bioelectricity
Tutorial B_ Sending OSC data

a) receive serial-port incoming data from arduino
b) shows incoming values as a bar graph in terminal
c) calculates and plot the FFT 
d) select a frequency bin and send its power as
    d.1 coeficient floting point value
    d.2 normalized (x-min/max-min) value between 0 and 1
    d.3 thresholded data (send 1 when val>thresh, send 0 when val<thresh)

*************************************************************************
"""

# import external libraries
import time
import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy import fftpack
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
#OSC_HOST = "201.124.35.129"
OSC_HOST ="25.5.244.74"
#OSC_HOST = "192.168.1.250"
OSC_PORT = 8000
OSC_CLIENT = OSCClient(OSC_HOST, OSC_PORT)

#variables
in_line = 0
data = []
nodata = []
buff = []
dc = 0
sc = 0
Fs = 100
t = np.arange(0,1,1/Fs)
#fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(15,5))
#plt.ylim(0,100)

max_val = 10
min_val = 0
isabove = False
freq_index = 8
freq_i2 = 19
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
        # plot here
        #ax[0].clear()
        #ax[1].clear()
        #ax[0].plot(t, buff)    # samples
        #ax[1].stem(fr, buff_m) # freq response
        #plt.draw()
        #plt.pause(0.0001)

        # then send osc
        aa = buff_m[freq_index]
        # silence if low signal
        if (aa<10): aa=0
        ruta = '/pulsum/8hz/a'.encode()
        OSC_CLIENT.send_message(ruta, [aa])
        # range and normalization
        if (aa>max_val): max_val = aa
        if (aa<min_val): min_val = aa
        bb = (aa-min_val)/(max_val-min_val)
        ruta = '/pulsum/8hz/b'.encode()
        OSC_CLIENT.send_message(ruta, [bb])
        if (bb>0.25 and isabove==False):
            ruta = '/pulsum/8hz/c'.encode()
            OSC_CLIENT.send_message(ruta, [1])
            isabove=True
        # threshold
        if(bb<0.25 and isabove==True):
            ruta = '/pulsum/8hz/c'.encode()
            OSC_CLIENT.send_message(ruta, [0])
            isabove=False

        # then another osc
        d2a = buff_m[freq_i2]
        # silence if low signal
        if (d2a<10): d2a=0
        ruta = '/pulsum/19hz/a'.encode()
        OSC_CLIENT.send_message(ruta, [aa])
        # range and normalization
        if (d2a>max_val): max_val = d2a
        if (d2a<min_val): min_val = d2a
        d2b = (d2a-min_val)/(max_val-min_val)
        ruta = '/pulsum/19hz/b'.encode()
        OSC_CLIENT.send_message(ruta, [d2b])
        if (d2b>0.25 and isabove==False):
            ruta = '/pulsum/19hz/c'.encode()
            OSC_CLIENT.send_message(ruta, [1])
            isabove=True
        # threshold
        if(d2b<0.25 and isabove==True):
            ruta = '/pulsum/19hz/c'.encode()
            OSC_CLIENT.send_message(ruta, [0])
            isabove=False


        #buff.clear()
        #sc = 0
        # < >
println("[-_-] exit status: 0")


#sudo hamachi attach less@interspecifics.cc
#sudo hamachi login
#sudo hamachi do-join 460-040-464
#sudo hamachi join 460-040-464
