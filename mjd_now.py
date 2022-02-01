#!/usr/bin/env python

from astropy.time import Time
import numpy as np

T0 = Time.now()

T0.format = "jd"
print('JD:', np.round(T0.value, 2))

T0.format = "mjd"
print('MJD:', np.round(T0.value, 2))
