from sioread.sioread import sioread
import numpy as np
from math import ceil
from scipy.io import loadmat

'''
Example usage of the sioread program
Note: This won't actually run unless you have a real sio file on your computer and specify it's path in line 23
'''

# I pick the number of samples I want based on the FFT resolution I desire
fs = 1500
df = .1
T = 1/df #length of fft snapshot to guarantee that resolution
overlap = .5 
N = np.power(2,ceil(np.log2(abs(T*fs)))) # make it a power of 2
T = N / fs # actual length of fft
df = 1 / T
freq = np.arange(df, fs/2 + df, df)

# here I make the input dictionary
# the only mandatory entry is 'fname'
fname = 'name_of_file.sio'
inp = {'fname': fname, 's_start':N/2+1, 'Ns' : N, 'channels': [1,2]} # notice I pass channels a list
[tmp, hdr] = sioread(**inp)

# tmp is the array
# it will have dimensions N x 2 (Ns = N, Nc = 2)
# hdr is a dictionary
# loop through and see what it says
for key in hdr.keys():
    print(key + ':', hdr[key])

# i'm confused
help(sioread) # show the docstring

