#!/usr/bin/env python

import sys
from astropy import units as u
from astropy.coordinates import SkyCoord, FK5

def main():
    x1 = input('RA DEC (2000):')
    x2 = input('choose which format to cenvert to ([degrees]/hmsdms):')

    if (x2=='') or (x2=='degrees'):
        c = SkyCoord(x1, frame=FK5, unit=(u.hourangle, u.deg))
        print('-------------------------------------')
        print('RA DEC (2000):', c.ra.degree, c.dec.degree)

    elif x2=='hmsdms':
        ra, dec = float(x1.split()[0]), float(x1.split()[1])
        c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame=FK5)
        print('-------------------------------------')
        print('RA DEC (2000):', c.to_string('hmsdms'))
        
main()

