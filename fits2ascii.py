#!/usr/bin/env python

from __future__ import print_function
import os
import numpy as np
from pyraf import iraf
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord, FK5, ICRS

def fits2ascii(input_files):

    if '.list' in input_files:
        input_files = [line.rstrip('\n') for line in open(input_files)]
        
    elif len(input_files.split()) > 1:
        pass
        
    elif '.fits' in input_files:
        input_files = [input_files]

    for input_file in input_files:
        try:
            output_file = input_file.split('.fits')[0] + '.dat'
            iraf.wspectext(input_file+'[*,1]', output_file, header=False)
            print(input_file, ' > ', output_file)
        except:
            print(input_file, ' failed...')

def main():
    input_files = raw_input('Enter fits file, list of them or file with a list in it (with ".list" extension) to convert to ascii: ')
    
    fits2ascii(input_files)

main()
