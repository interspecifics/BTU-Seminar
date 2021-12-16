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

# modules
import pandas as pd
import numpy as np
from matplotlib import pyplot
from dtw import accelerated_dtw, dtw
from sklearn.metrics.pairwise import euclidean_distances
dist_fun = euclidean_distances


# read data from file
data = pd.read_csv('data_c.csv', header=0, index_col=0)
print(data.head())


# separate by columns
sin_t = data["sin(t)"].values.tolist()
sin_2t = data["sin(2t)"].values.tolist()
sin_t4 = data["sin(t/4)"].values.tolist()
sin_4t2 = data["sin(4 * t/2)"].values.tolist()


# convert lists to vectors
vector_t = np.array(([sin_t]), dtype=float)
vector_2t = np.array(([sin_2t]), dtype=float)
vector_t4 = np.array(([sin_t4]), dtype=float)
vector_4t2 = np.array(([sin_4t2]), dtype=float)
#print(vector_t); print(vector_t.shape)


# calculate dtw
dist_1, _a, _b, _c = dtw([vector_t], [vector_2t], dist_fun)
dist_2, _a, _b, _c = dtw([vector_t], [vector_t4], dist_fun)
dist_3, _a, _b, _c = dtw([vector_t], [vector_4t2], dist_fun)

dist_4, _a, _b, _c = dtw([vector_2t], [vector_t4], dist_fun)
dist_5, _a, _b, _c = dtw([vector_2t], [vector_4t2], dist_fun)

dist_6, _a, _b, _c = dtw([vector_t4], [vector_4t2], dist_fun)


