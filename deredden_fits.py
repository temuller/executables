#!/usr/bin/env python

import os
import sfdmap
import extinction
import numpy as np
from pyraf import iraf
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord, FK5, ICRS

def deredden(wave, flux, ra, dec, scaling=0.86):
    
    m = sfdmap.SFDMap(mapdir='~/OneDrive/sfddata-master/', scaling=scaling) 
    ebv = m.ebv(ra, dec) # RA and DEC in degrees
    r_v  = 3.1
    a_v = r_v*ebv
    ext = extinction.ccm89(wave, a_v, r_v)
    deredden_flux = extinction.apply(-ext, flux) #removes extinction from flux
    
    return deredden_flux

def deredden_fits(input_files):
    
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

            wave, flux = np.loadtxt(output_file).T
            os.remove(output_file)

            # get header information
            hdul = fits.open(input_file)
            header = hdul[0].header
            data = hdul[0].data

            ra_init = header['RA']
            dec_init = header['DEC']

            if 'RADESYS' in header:
                radesys = header['RADESYS']

                if radesys=='IRCS':
                    frame=IRCS
                elif radesys=='FK5':
                    frame=FK5

                coords = SkyCoord(f"{ra_init} {dec_init}", frame=frame, unit=(u.hourangle, u.deg))
                ra_degrees = coords.ra.degree
                dec_degrees = coords.dec.degree

            elif 'RADECSYS' in header:
                ra_degrees = float(ra_init)
                dec_degrees = float(dec_init)
                
            else:
                coords = SkyCoord(f"{ra_init} {dec_init}", frame=FK5, unit=(u.hourangle, u.deg))
                ra_degrees = coords.ra.degree
                dec_degrees = coords.dec.degree
                
            deredden_flux = deredden(wave, flux, ra_degrees, dec_degrees)
            try:
                data[0] = deredden_flux
            except:
                data = deredden_flux

            hdul[0].data = data
            deredden_file = input_file.split('.fits')[0] + '_deredden.fits'

            if os.path.exists(deredden_file):
                os.remove(deredden_file)

            hdul.writeto(deredden_file)
        
        except:
            print(f'{input_file} failed...')

def main():
    input_files = input('Enter fits file, list of them or file with a list in it (with ".list" extension):')

    deredden_fits(input_files)

main()
