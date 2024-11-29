#!/usr/bin/env python

import os
import sys
import time
from io import StringIO
from pathlib import Path

import tns_api
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from astropy.time import Time
from astropy.cosmology import FlatLambdaCDM
COSMO = FlatLambdaCDM(H0=70, Om0=0.3, Tcmb0=2.725)

plt.rcParams["font.family"] = "GFS Artemisia"
plt.rcParams['mathtext.fontset'] = "cm"

tns_env_file = Path(tns_api.__path__[0], '.env')
if tns_env_file.is_file() is False:
    print("Creating '.env' file with TNS BOT info. Please, re-run the script to apply the changes...")
    with open(tns_env_file, 'w') as file:
        file.write("tns_id = '157253'\n")
        file.write("name = 'TEMB_API'\n")
        file.write("api_key = '65c2203a72ffcff04e4b6c89e99e4c98f00e6cfc'\n")

#######
# ZTF #
#######
def get_ztfname(sn_dict):
    """Obtains the ZTF internal name for the target.
    
    Parameters
    ----------
    sn_dict: dict
        SN info from TNS.
    
    Returns
    -------
    ztfname: str
        ZTF internal name.
    """
    ztfname = None
    
    internal_names_str = sn_dict['internal_names']
    internal_names_str = internal_names_str.replace(' ', '')
    internal_names = internal_names_str.split(',')
    
    for name in internal_names:
        if name.startswith('ZTF'):
            ztfname = name
            break
            
    return ztfname

def download_ztf_lightcurve(ztfname):
    """Downloads the ZTF light curve of a target.
    
    Parameters
    ----------
    ztfname: str
        ZTF internal name.
    
    Returns
    -------
    phot_df: DataFrame
        ZTF light curve.
    """
    # get the light curves from Alerce
    res = requests.get(f'https://api.alerce.online/ztf/v1/objects/{ztfname}/detections')
    res.raise_for_status()
    jsn = res.json()
    
    phot_df = pd.DataFrame.from_dict(jsn)
    phot_df = phot_df[['fid', 'mjd', 'magpsf', 'sigmapsf']]
    phot_df.rename(columns={'fid':'filter', 
                            'mjd':'time', 
                            'magpsf':'mag', 
                            'sigmapsf':'mag_err'}, 
                   inplace=True)
    
    # Remove bad values of time and magnitude:
    mask = (np.isfinite(phot_df.time.values) & 
            np.isfinite(phot_df.mag.values) & 
            np.isfinite(phot_df.mag_err.values)
           )
    phot_df = phot_df[mask]

    # Replace photometric filter numbers with keywords used in Flows:
    photfilter_dict = {1: 'ztf_g', 2: 'ztf_r', 3: 'ztf_i'}
    phot_df['filter'] = [photfilter_dict[fid] for fid in phot_df['filter']]

    # Sort the table on photfilter and time:
    phot_df.sort_values(['filter', 'time'], inplace=True)

    return phot_df

#########
# ATLAS #
#########
def get_token(user, password):
    BASEURL = "https://fallingstar-data.com/forcedphot"
    
    if os.environ.get('ATLASFORCED_SECRET_KEY'):
        token = os.environ.get('ATLASFORCED_SECRET_KEY')
        print('Using stored token')
    else:
        data = {'username': user, 'password': password}
        resp = requests.post(url=f"{BASEURL}/api-token-auth/", data=data)

        if resp.status_code == 200:
            token = resp.json()['token']
            print(f'Your token is {token}')
            print('Store this by running/adding to your .zshrc file:')
            print(f'export ATLASFORCED_SECRET_KEY="{token}"')
        else:
            print(f'ERROR {resp.status_code}')
            print(resp.text)
            sys.exit()
            
    return token

def get_headers(token):
    headers = {'Authorization': f'Token {token}', 
               'Accept': 'application/json'}
    
    return headers

def submit_task(ra, dec, headers, mjd_min=None, mjd_max=None):
    BASEURL = "https://fallingstar-data.com/forcedphot"
    
    task_url = None
    while not task_url:
        with requests.Session() as s:
            resp = s.post(f"{BASEURL}/queue/", headers=headers, data={
                'ra': ra, 'dec': dec, 'send_email': False,
                'mjd_min':mjd_min, 'mjd_max':mjd_max})

            if resp.status_code == 201:  # successfully queued
                task_url = resp.json()['url']
                print(f'The task URL is {task_url}')
            elif resp.status_code == 429:  # throttled
                message = resp.json()["detail"]
                print(f'{resp.status_code} {message}')
                t_sec = re.findall(r'available in (\d+) seconds', message)
                t_min = re.findall(r'available in (\d+) minutes', message)
                if t_sec:
                    waittime = int(t_sec[0])
                elif t_min:
                    waittime = int(t_min[0]) * 60
                else:
                    waittime = 10
                print(f'Waiting {waittime} seconds')
                time.sleep(waittime)
            else:
                print(f'ERROR {resp.status_code}')
                print(resp.text)
                sys.exit()
                
    return task_url

def get_url(task_url, headers):
    result_url = None
    taskstarted_printed = False
    while not result_url:
        with requests.Session() as s:
            resp = s.get(task_url, headers=headers)

            if resp.status_code == 200:  # HTTP OK
                if resp.json()['finishtimestamp']:
                    result_url = resp.json()['result_url']
                    print(f"Task is complete with results available at {result_url}")
                    if result_url is None:
                        return None
                elif resp.json()['starttimestamp']:
                    if not taskstarted_printed:
                        print(f"Task is running (started at {resp.json()['starttimestamp']})")
                        taskstarted_printed = True
                    time.sleep(2)
                else:
                    print(f"Waiting for job to start (queued at {resp.json()['timestamp']})")
                    time.sleep(4)
            else:
                print(f'ERROR {resp.status_code}')
                print(resp.text)
                sys.exit()
                
    return result_url

def get_atlas_lightcurves(ra, dec, user, password, mjd_min=None, mjd_max=None):
    token = get_token(user, password)
    headers = get_headers(token)
    task_url = submit_task(ra, dec, headers, mjd_min, mjd_max)
    result_url = get_url(task_url, headers)
    if result_url is None:
        return None
    
    with requests.Session() as s:
        textdata = s.get(result_url, headers=headers).text

    lc_df = pd.read_csv(StringIO(textdata.replace("###", "")), 
                        delim_whitespace=True)
    
    return lc_df

#########
# PLOTS #
#########
def bin_data(x, y, yerr, dx):
    """Combines the dat given a window size. 
    """
    # Initialize lists to store statistics for each bin
    binned_x = []
    binned_y = []
    binned_yerr = []

    bin_edges = np.arange(x.min(), x.max() + dx, dx)
    bin_indices = np.digitize(x, bin_edges)
    
    # Compute statistics for each bin
    for i in range(1, len(bin_edges)):
        # Select data points that fall into the current bin
        bin_x = x[bin_indices == i]
        bin_y = y[bin_indices == i]
        bin_yerr = yerr[bin_indices == i]
        
        # Calculate and store statistics if bin_data is not empty
        if len(bin_x) > 0:
            binned_x.append(np.mean(bin_x))
            binned_y.append(np.mean(bin_y))
            binned_yerr.append(np.sqrt(np.sum(bin_yerr ** 2) / len(bin_yerr)))
        else:
            binned_x.append(np.nan)
            binned_y.append(np.nan)
            binned_yerr.append(np.nan)
    
    # remove NaNs
    nan_mask = ~np.isnan(binned_x)
    binned_x = np.array(binned_x)[nan_mask]
    binned_y = np.array(binned_y)[nan_mask]
    binned_yerr = np.array(binned_yerr)[nan_mask]

    return binned_x, binned_y, binned_yerr

def plot_lcs(sn_df, iauname, z=None, bin=True):
    filters = {"ztf_g":"g", 
               "ztf_r":"r", 
               "atlas_c":"cyan", 
               "atlas_o":"orange"
              }
    
    fig, ax = plt.subplots()
    if z is not None:
        title = fr'{iauname} ($z={z:.4f}$)'
        ax2 = ax.twinx()
        ax2.invert_yaxis()
        ax2.set_ylabel('Absolute Magnitude', fontsize=18, rotation=-90, labelpad=15)
        ax2.tick_params(labelsize=18)
    else:
        title = iauname
        
    for filt in filters.keys():
        if filt not in sn_df["filter"].values:
            continue
        filt_df = sn_df[sn_df["filter"]==filt]
        times = filt_df.time.values
        mags = filt_df.mag.values
        mags_err = filt_df.mag_err.values

        if bin is True:
            # combine data 
            times, mags, mags_err = bin_data(times, mags, mags_err, dx=1)
        
        ax.errorbar(times, mags, yerr=mags_err, color=filters[filt], label=filt, marker="o", ls="--")
        if z is not None:
            distmod = COSMO.distmod(z).value
            ax2.errorbar(times, mags - distmod, yerr=mags_err, color=filters[filt], marker="o", ls="--")
                
    ax.invert_yaxis()
    ax.set_title(title, fontsize=18)
    ax.set_ylabel('Appartent Magnitude', fontsize=18)
    ax.set_xlabel('MJD', fontsize=18)
    ax.tick_params(labelsize=18)
    ax.legend(fontsize=18)
    plt.tight_layout()
    plt.show()

########
# MAIN #
########
import argparse
from getpass import getpass

def main(args=None):
    description = f"Plotting ZTF and ATLAS light curves by T. Müller-Bravo"
    usage = "plot_lightcurves IAU_NAME [options]"
    
    if not args:
        args = sys.argv[1:] if sys.argv[1:] else ["--help"]
        
    parser = argparse.ArgumentParser(prog='plot_lightcurves',
                                     usage=usage,
                                     description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument("iau_name",
                        action="store",
                        type=str,
                        help="The object to plot (e.g. 2024xxx)."
                        )
    parser.add_argument("-z",
                        dest="z",
                        action="store",
                        type=float,
                        help=("Redshift value for plotting absolute magnitude. This replaces the redshift from TNS.")
                        )
    parser.add_argument("-n",
                        "--ztfname",
                        dest="ztfname",
                        action="store",
                        type=str,
                        help=("ZTF name used for finding ZTF light curves. If not given, used the name found on TNS, if any.")
                        )
    parser.add_argument("-u",
                        "--username",
                        dest="username",
                        action="store",
                        type=str,
                        help=("ATLAS force-photometry username (fallingstar website).")
                        )
    parser.add_argument("--no-bin",
                        dest="bin",
                        action="store_false", 
                        help=("Disables the binning of data using a 1-day window.")
                        )
    
    # Run script
    args = parser.parse_args(args)
    # SN info
    sn_dict = tns_api.api.get_object(args.iau_name)
    ra, dec = sn_dict['radeg'], sn_dict['decdeg']
    if args.z is None:
        z = sn_dict['redshift']
    else:
        z = args.z
    if args.ztfname is None: 
        ztfname = get_ztfname(sn_dict)
    else:
        ztfname = args.ztfname

    # ZTF light curve
    if ztfname is not None:
        print("Downloading ZTF light curves...\n")
        ztf_df = download_ztf_lightcurve(ztfname)
    else:
        ztf_df = None
        print("No ZTF name found!\n")

    # ATLAS light curve
    disc_date = sn_dict['discoverydate'].replace(" ", "T")
    disc_time = Time(disc_date, format='isot', scale='utc').mjd
    
    print("Downloading ATLAS light curves...")
    # credentials from fallingstar website
    if args.username is not None: 
        user = args.username
    else:
        user = 't.e.muller-bravo'
    password = str(getpass("ATLAS Force Photometry Password:"))
    try:
        downloaded_df = get_atlas_lightcurves(ra, dec, user, password, disc_time - 20, disc_time + 150)
        
        atlas_df = downloaded_df.copy()
        atlas_df = atlas_df.rename(columns={"MJD":"time", "m":"mag", "dm":"mag_err", "F":"filter"})
        columns = ['filter', 'time', 'mag', 'mag_err']
        atlas_df = atlas_df[columns]

        atlas_df["filter"] = "atlas_" + atlas_df["filter"].astype(str).values  # rename filters
        atlas_df = atlas_df[atlas_df.mag > 0.0]
        snr = atlas_df.mag.values / atlas_df.mag_err.values
        atlas_df = atlas_df[snr > 3]
    except Exception as exc:
        print(exc)
        print("ATLAS failed. Let's continue without ATLAS...")
        atlas_df = None

    # merge ZTF + ATLAS
    sn_df = pd.concat([ztf_df, atlas_df])

    print("\nPlotting light curves...")
    plot_lcs(sn_df, args.iau_name, z, bool(args.bin))

if __name__ == "__main__":
    main(sys.argv[1:])
