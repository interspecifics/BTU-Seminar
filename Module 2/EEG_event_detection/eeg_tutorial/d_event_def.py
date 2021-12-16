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

# interactive python shell
# pip install ipython


# modules
import pandas as pd
import numpy as np
from matplotlib import pyplot
from dtw import accelerated_dtw, dtw
from sklearn.metrics.pairwise import euclidean_distances
dist_fun = euclidean_distances


# reading EEG data
# read data from file
data = pd.read_csv('../eeg_analyzer/data/EEGdata_02_ReducFilterIC/aracely_RF_ELEC.csv', header=0, index_col=0)
print(data.head())


# plot
data.plot()
pyplot.show()


# separate by columns
data_AF3 = data["AF3"].values.tolist()
data_F7 = data["F7"].values.tolist()
data_F3 = data["F3"].values.tolist()
data_F4 = data["F4"].values.tolist()
data_F8 = data["F8"].values.tolist()
data_AF7 = data["AF7"].values.tolist()
print(data.head())



# zoom
d_AF3 = pd.DataFrame(data_AF3)
d_AF3.plot()
pyplot.show()


# crop
AF3_p = data_AF3[1128 : 1128 + 256] #extract elements from 0 to 256 in the list
d_AF3_p = pd.DataFrame(AF3_p)
d_AF3_p.plot()
pyplot.show()


# vectorize
v_AF3 = np.array(([AF3_p]), dtype=float)


# load prototype to compare
data = pd.read_csv('data_c.csv', header=0, index_col=0)
sin_t4 = data["sin(t/4)"].values.tolist()
v_t4 = np.array(([sin_t4]), dtype=float)


# calculate dtw
dist, _a, _b, _c = dtw([v_AF3], [v_t4], dist_fun)


#shift the measure
for i in range(256):
    AF3_p = data_AF3[i : i+256]
    v_AF3 = np.array(([AF3_p]), dtype=float)
    dist, _a, _b, _c = dtw([v_AF3], [v_t4], dist_fun)
    print("distance at sample {} is: {}".format(i, dist))
