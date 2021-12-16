"""
// i n t e r s p e c i f i c s  @  T U B, Autumn 2021
Module 2: Brain Bioelectricity

Potencial de Acción
Time Series and Dynamic Time Warping tutorial


a. Time series data
b. Reading and plotting data
c. DTW as distance measure
d. Data event definition
e. Training
f. DTW for EEG event detection

"""


import math
import pandas as pd


# sine equation:
# A * sin(F * angle)


# create a data file
data_a = [math.sin(math.pi/32 * t) for t in range(64)]
df = pd.DataFrame(data_a)
df.to_csv("data_a.csv", sep=",")


#create a indexed data file
data_b = [math.sin(2 * math.pi/32 * t) for t in range(64)]
df = pd.DataFrame(data_b, index=[i for i in range(64)], columns=["sin(t)"])
df.to_csv("data_b.csv", sep=",")


#create a multicolumn file
data_a = [math.sin(math.pi/32 * t) for t in range(64)] + [0 for t in range(196)]
data_b = [0 for t in range(196)] + [math.sin(2 * math.pi/32 * t) for t in range(64)]
data_c = [math.sin(math.pi/128 * t) for t in range(256)]
data_d = [math.sin(4 * math.pi/64 * t) for t in range(256)]
df = pd.DataFrame(list(zip(data_a, data_b, data_c, data_d)), columns=["sin(t)", "sin(2t)", "sin(t/4)", "sin(4 * t/2)"])
df.to_csv("data_c.csv", sep=",")


#custom headers and indexes
df.to_csv("data_cn.csv", sep=",", index=None, header=True)
df.to_csv("data_cf.csv", sep=",", index=None, header=False)


