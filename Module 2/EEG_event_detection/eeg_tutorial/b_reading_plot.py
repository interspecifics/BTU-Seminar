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


#import math
import pandas as pd
from matplotlib import pyplot


data = pd.read_csv('data_a.csv', header=0, index_col=0)
print(data.head())
data.plot()
pyplot.show()
# quit pressing 'q'


data = pd.read_csv('data_c.csv', header=0, index_col=0)
print(data.head())
data.plot()
pyplot.show()