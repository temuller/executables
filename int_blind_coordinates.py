#!/usr/bin/env python

def main():
    x1 = input('year (e.g. 2022): ')
    x1 = input('month (e.g. 10): ')
    x3 = input('Blind target coordinates RA DEC (e.g. 23 00 13.9600573728 +15 58 25.952519676): ')
    x4 = input('Proper motion in mas/yr (e.g. 11.532 0.283): ')

    year = float(x1)
    month = float(10)

    # proper motion correction factor
    prop = x4
    ra_prop = float(prop.split()[0])
    dec_prop = float(prop.split()[-1])

    corr_ra = (year - 2000 + month/12) * ra_prop/1500
    corr_dec = (year - 2000 + month/12) * dec_prop/1000

    print('')
    print('##################################')
    print(f'corrections {corr_ra:.3f} (RA), {corr_dec:.3f} (DEC)')
    print('')

    # reference star (blind offset) corrdinates
    coords = x3

    ra = coords.split()[0]
    dec = coords.split()[-1]

    split_coords = coords.split()

    # apply corrections
    split_coords[2] = f'{eval(split_coords[2]) + corr_ra:.3f}'
    if split_coords[3][0]=='-':
        split_coords[-1] = f'{eval(split_coords[-1])*-1 + corr_dec:.3f}'[1:]
    else:
        split_coords[-1] = f'{eval(split_coords[-1]) + corr_dec:.3f}'

    new_coords = ' '.join([val for val in split_coords])

    print('Initial coordinates:', coords)
    print('Corrected coordinates:', new_coords)

main()
