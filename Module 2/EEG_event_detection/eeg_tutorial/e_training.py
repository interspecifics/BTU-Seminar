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
from random import random
import math
dist_fun = euclidean_distances




# make some data

data = [0 for t in range(512)] + [math.sin(8* math.pi/32 * t) for t in range(256)] + [-1 + 2 * random() for t in range(256)]
event = [math.sin(8 * math.pi/32 * t) for t in range(256)]



# show data
data_f = pd.DataFrame(data)
data_f.plot()
pyplot.show()

# show event
event_f = pd.DataFrame(event)
event_f.plot()
pyplot.show()



#shift the measure


# vectorize
v_event = np.array(([event]), dtype=float)




#shift the measure
for i in range(512+256):
    dat = data[i : i+256]
    v_dat = np.array(([dat]), dtype=float)
    dist, _a, _b, _c = dtw([v_event], [v_dat], dist_fun)
    print("distance at sample {} is: {}".format(i, dist))
