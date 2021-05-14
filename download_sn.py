#!/usr/bin/env python

import json
import pickle
import os.path
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main():
    print('Download from the Open Supernova Catalog')
    print('------------------------------------------')
    sn = input('Enter SN name (e.g., SN2011fe):')
    
    url = f'https://sne.space/astrocats/astrocats/supernovae/output/json/{sn}.json'
    
    if os.path.isfile(f'{sn}.json'):
        download = input(f'The file {sn}.json already exists, download anyway? ([no]|yes):')
        if download=='yes' or download=='y':
            print('Warning: the file will be saved with a different name given that it is a copy.')
            subprocess.call(['wget', url])
    else:
        subprocess.call(['wget', url])

    ######## photometry ########
    with open(f'{sn}.json') as f:
        sn_json = json.load(f)[sn]
        
    sn_photometry = sn_json['photometry']
    sn_dict = {'mjd':[], 'band':[], 'mag':[], 'err':[]}

    for data in sn_photometry:
        if 'band' in data:
            if 'e_magnitude' in data:
                err = float(data['e_magnitude'])
            else:
                err = np.nan
            if 'system' in data:
                system = data['system']
            else:
                system = np.nan

            sn_dict['mjd'].append(float(data['time']))
            sn_dict['mag'].append(float(data['magnitude']))
            sn_dict['err'].append(err)
            sn_dict['band'].append(data['band'])

    sn_df = pd.DataFrame.from_dict(sn_dict)
    sn_df = sn_df.sort_values(['band', 'mjd'])
    sn_df.to_csv(f'{sn}.phot', index=False)  

    ######## spectroscopy ########
    with open(f'{sn}.json') as input_file:
        sn_json = json.load(input_file)[sn]
        
    sn_spectra = sn_json['spectra']
    sn_dict = {}

    for data in sn_spectra:
        mjd_dict = {}
 
        if 'time' in data:
            time = data['time']
        elif 'file_name' in data:
            time = data['file_name']
        else:
            time = 0.0

        spec = np.asarray(data['data']).T
        wave, flux = spec[0].astype(float), spec[1].astype(float)

        mjd_dict['wave'] = wave
        mjd_dict['flux'] = flux
        mjd_dict['units'] = data['u_fluxes']
        mjd_dict['ref'] = data['source']

        sn_dict[time] = mjd_dict

    with open(f'{sn}.spec', 'wb') as outfile:
        pickle.dump(sn_dict, outfile, pickle.HIGHEST_PROTOCOL)

    ######## plots ########
    plot_phot = input('Plot the photometry? ([yes]|no):')

    if plot_phot=='yes' or plot_phot=='y' or plot_phot=='':
        sn_df = pd.read_csv(f'{sn}.phot')

        f, ax = plt.subplots()
        for band in sn_df.band.unique():
            band_data = sn_df[sn_df.band.values==band]
            ax.errorbar(band_data.mjd.values, band_data.mag.values, band_data.err.values, fmt='--.', label=band)
            ax.set_xlabel('Modified Julian Date')
            ax.set_ylabel('Apparent Magnitude')
            ax.set_title(f'{sn}')

        plt.gca().invert_yaxis()
        plt.show()

    ###
    plot_phot = input('Plot the spectra? ([yes]|no):')

    if plot_phot=='yes' or plot_phot=='y' or plot_phot=='':
        sn_dict = pickle.load(open(f'{sn}.spec', 'rb'))

        f, ax = plt.subplots()
        for i, time in enumerate(sn_dict.keys()):
            spec_info = sn_dict[time]
            if spec_info['units']=='erg/s/cm^2/Angstrom':
                wave = spec_info['wave']
                flux = spec_info['flux']

                ax.plot(wave, flux*wave, label=time)
                ax.set_xlabel('Wavelength [$\AA$]')
                ax.set_ylabel(r'Flux [erg/s/cm$^2$]')
                ax.set_title(f'{sn}')

        plt.show()  

main()
