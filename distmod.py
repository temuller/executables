#!/usr/bin/env python
'''
import sys
from astropy.cosmology import Planck15

def main():
    x1 = input('redshift:')
    z = float(x1)
    mu = Planck15.distmod(z).value
    d = 10**(mu/5 + 1)
    
    x2 = input('apparent magnitude:')
    
    print('------------------------')
    print('distance modulus: %.3f [mag]' % mu)
    print('luminosity distance: %.3e [parsec] | %.3e [cm]' % (d, d*3.086e+18))
    if x2 != '':
        m = float(x2)
        M = m - mu
        print('absolute magnitude: %.3f [mag]' % M)
    

main()
'''

import sys
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u

#H0 between Planck and Riess et al. (2019)
cosmo = FlatLambdaCDM(H0=70 * u.km / u.s / u.Mpc, Tcmb0=2.725 * u.K, Om0=0.3)

def main():
    x1 = input('redshift:')
    z = float(x1)
    mu = cosmo.distmod(z).value
    d = 10**(mu/5 + 1)
    
    x2 = input('apparent magnitude: ')
    
    print('------------------------')
    print('distance modulus: %.3f [mag]' % mu)
    print('luminosity distance: %.3e [parsec] | %.3e [cm]' % (d, d*3.086e+18))
    if x2 != '':
        m = float(x2)
        M = m - mu
        print('absolute magnitude: %.3f [mag]' % M)

main()
