#!/usr/bin/env python

import sys
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord, FK5, Angle
from astropy.cosmology import Planck15

def main():
    x1 = input('Redshift:')
    z = float(x1)
    mu = Planck15.distmod(z).value
    d = 10**(mu/5 + 1)

    x2 = input('Convert from [arsec]/coords/dist:')

    if (x2=='') or (x2=='arsec'):
        x3 = input('Arcsec:')
        theta = Angle(f'0d0m{x3}s').degree

        a = d*np.tan(theta)
        print('-------------------------------------')
        print('Distance:', a,'[parsec]')

    elif x2=='coords':  # not ready
        ra, dec = float(x1.split()[0]), float(x1.split()[1])
        c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame=FK5)
        print('-------------------------------------')
        print('RA DEC (2000):', c.to_string('hmsdms'))

    elif x2=='dist':
        x3 = input('Distance [parsec]:')
        a = float(x3)

        theta = np.arctan(a/d)
        ang = Angle(np.arctan(a/d), unit=u.deg)
        dms = ang.to_string(unit=u.degree, sep=('deg', 'm', 's'))

        arsec = dms.split('m')[-1]
        print('-------------------------------------')
        print('Arsec:', arsec)
        
main()
