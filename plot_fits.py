#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

def plot_fits(input_file):

    img = fits.open(input_file)
    data = img[0].data
    if data is None:
        data = img[1].data

    fig, ax = plt.subplots()
    m, s = np.nanmean(data), np.nanstd(data)
    im = ax.imshow(data, interpolation='nearest', origin='lower',
                   cmap='gray', vmin=m-s, vmax=m+s)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.show()

def main():
    input_file = input('Enter fits file: ')
    plot_fits(input_file)

main()
