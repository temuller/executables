#!/usr/bin/env python

import sys
from astropy.time import Time

def main():
    x1 = input('Convert from [iso]/mjd/jd/isot:')
    if (x1=='') or (x1=='iso'):
        x2 = input('Time (yyyy-mm-dd hh:mm:ss):')
        time = x2
        t = Time(time, format='iso', scale='utc')
  
    elif x1=='mjd':
        x2 = input('MJD:')
        time = float(x2)
        t = Time(time, format='mjd', scale='utc')

    elif x1=='jd':
        x2 = input('JD:')
        time = float(x2)
        t = Time(time, format='jd', scale='utc')

    elif x1=='isot':
        x2 = input('Time (yyyy-mm-ddThh:mm:ss):')
        time = x2
        t = Time(time, format='isot', scale='utc')

    print('---------------------------------------------------')
    print(f'ISOT / MJD / JD: {t.datetime.isoformat()} / {t.mjd} / {t.jd}')
        

main()
