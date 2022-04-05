#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

def plot_fits(input_file):

    img = fits.open(input_file)
    data = img[0].data

    fig, ax = plt.subplots()
    m, s = np.nanmean(data), np.nanstd(data)
    im = ax.imshow(data, interpolation='nearest', origin='lower',
                   cmap='gray', vmin=m-s, vmax=m+s)
    plt.show()

def main():
    input_file = input('Enter fits file: ')
    plot_fits(input_file)

main()
