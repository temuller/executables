#!/usr/bin/env python
import astropy.units as u
from astropy.coordinates import ICRS
from astropy.coordinates import SkyCoord
import warnings

def main():
    x1 = input('year (e.g. 2022): ')
    x2 = input('month (e.g. 10): ')
    x3 = input('Blind target coordinates RA DEC (e.g. 23 00 13.9600573728 +15 58 25.952519676): ')
    x4 = input('Proper motion in mas/yr (e.g. 11.532 0.283): ')

    year = float(x1)
    month = float(x2)

    # proper motion correction factor
    prop = x4
    ra_prop = float(prop.split()[0])
    dec_prop = float(prop.split()[-1])

    corr_ra = (year - 2000 + month/12) * ra_prop/15000
    corr_dec = (year - 2000 + month/12) * dec_prop/1000

    print('')
    print('##################################')
    print(f'Corrections: {corr_ra:.3f} (RA), {corr_dec:.3f} (DEC)')
    print('')

    # reference star (blind offset) corrdinates
    coords = x3

    """
    ra = coords.split()[0]
    dec = coords.split()[-1]

    split_coords = coords.split()

    # apply corrections
    # RA
    split_coords[2] = f'{eval(split_coords[2]) + corr_ra:.3f}'

    # DEC
    if split_coords[3][0]=='-':
        split_coords[-1] = f'{eval(split_coords[-1])*-1 + corr_dec:.3f}'[1:]
    else:
        split_coords[-1] = f'{eval(split_coords[-1]) + corr_dec:.3f}'

    new_coords = ' '.join([val for val in split_coords])

    print('Initial coordinates:', coords)
    print('Corrected coordinates:', new_coords)
    """
    c = SkyCoord(coords,
                 unit=(u.hourangle, u.deg),
                 frame=ICRS,
                 pm_ra_cosdec=ra_prop * u.mas / u.yr, pm_dec=dec_prop * u.mas / u.yr,
                 )

    dt = year - 2000 + month/12
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        new_coords = c.apply_space_motion(dt=dt * u.year).to_string('hmsdms')

    for char in 'hdms':
        new_coords = new_coords.replace(char, ' ')

    print('Initial coordinates:', coords)
    print('Corrected coordinates:', new_coords)

main()
