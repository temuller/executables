#!/usr/bin/env python

import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sep
import aplpy
from astropy import wcs
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.stats import sigma_clipped_stats
from photutils.aperture import ApertureStats
from photutils.aperture import SkyCircularAnnulus

from hostphot._constants import font_family
from hostphot.utils import suppress_stdout

import warnings
from astropy.utils.exceptions import AstropyWarning

def extract_image(file):
    """Obtains the data and other information from a FITS file.

    Parameters
    ----------
    file: str
        Name of the FITS file.

    Returns
    -------
    data: ndarray
        Image data/counts.
    header: ~fits.header
        Image header.
    img_wcs: ~astropy.wcs
        Image WCS.
    hdu: ~fits.hdu
        Image Header Data Unit.
    """
    hdu = fits.open(file)
    
    header = hdu[0].header
    data = hdu[0].data
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", AstropyWarning)
        img_wcs = wcs.WCS(header, naxis=2)

    data = data.astype(np.float64)
    
    return data, header, img_wcs, hdu

def get_sep_stats(data, **sep_kwargs):
    """Obtains the background mean and rms from an array
    using SEP (SExtractor).

    Parameters
    ----------
    data: ndarray
        Image data/counts.

    Returns
    -------
    bkg_mean: float
        Background mean.
    bkg_rms: float
        Background root-mean-square.
    """
    bkg = sep.Background(data, **sep_kwargs)
    bkg_mean = bkg.globalback
    bkg_rms = bkg.globalrms
    
    return bkg_mean, bkg_rms

def get_astropy_stats(data, sigma=3.0):
    """Obtains the background mean, median and std from an array
    using Astropy's sigma-clipping stats.

    Parameters
    ----------
    data: ndarray
        Image data/counts.
    sigma: float, default '3.0'
        Sigma used for the sigma clipping.

    Returns
    -------
    mean: float
        Background mean.
    mean: float
        Background median.
    std: float
        Background standard deviation.
    """
    mean, median, std = sigma_clipped_stats(data, sigma=sigma)
    
    return mean, median, std

def get_target_stats(data, img_wcs, ra, dec, r_in, r_out):
    """Obtains the background mean, median and std around
    the given coordinates using an annulus.

    Parameters
    ----------
    data: ndarray
        Image data/counts.
    img_wcs: ~astropy.wcs
        Image WCS.
    ra: float
        Right ascension.
    dec: float
        Declination.
    r_in: float
        Inner radius of the annulus.
    r_out: float
        Outer radius of the annulus.

    Returns
    -------
    aperstats: ~astropy.aperture.ApertureStats
        Annulus statistics.
    """
    coords = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame="icrs")

    r_in = r_in * u.arcsec
    r_out = r_out * u.arcsec
    aperture = SkyCircularAnnulus(coords, r_in=r_in, r_out=r_out)
    aperstats = ApertureStats(data, aperture, wcs=img_wcs) 

    return aperstats
            
def plot_target(
    hdu,
    ra=None,
    dec=None,
    aperture=None,
    size=1.0,
    info_dict=None,
    show_plot=True,
    outfile=None,
):
    """Plots the objects extracted with :func:`sep.extract()``.

    Parameters
    ----------
    hdu: ~fits.hdu
        Image Header Data Unit.
    ra: float, default 'None'
       Right ascension of an object, in degrees. Used for plotting the position of the object.
    dec: float, default 'None'
    aperture: ~astropy.aperture, default 'None'
        Annulus aperture used for the background.
    size: float, default '1.0'
        Size of the image to be plotted, in arcminutes.
    info_dict: dict, default 'None'
        Dictionary with background statistics.
    show_plot: bool, default 'True'
        Wether to show the output plot.
    outfile: str, default 'None'
        Output file name.
    """
    figure = plt.figure(figsize=(10, 10))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", AstropyWarning)
        fig = aplpy.FITSFigure(hdu, figure=figure)

    with suppress_stdout():
        fig.show_grayscale(stretch="arcsinh")

    if (ra is not None) and (dec is not None):
        # resize image to show only around the coordinates
        size_arcmin = size*u.arcmin
        size_degree = size_arcmin.to(u.degree)
        fig.recenter(ra, dec, size_degree.value)
        
        if aperture is not None:
            # plot annulus
            fig.show_circles(
                ra,
                dec,
                aperture.r_in.to(u.degree),
                linewidth=2,
                edgecolor="r",
                label='Annulus',
                layer='r_in'
            )
            fig.show_circles(
                ra,
                dec,
                aperture.r_out.to(u.degree),
                linewidth=2,
                edgecolor="r",
                layer='r_out'
            )

    sep_mean, sep_std = info_dict['sep']
    astro_mean, astro_median, astro_std = info_dict['astro']
    target_bkg, target_std, percent = info_dict['target']
    sep_diff = info_dict['sep_diff']
    astro_diff = info_dict['astro_diff']
    
    text = 'Background stats\n'
    text += f'SEP: mean={sep_mean:.2f}, std={sep_std:.2f}\n'
    text += f'ASTROPY: mean={astro_mean:.2f}, median={astro_median:.2f}, std={astro_std:.2f}\n'
    text += f'Annulus: percentile ({percent}%)={target_bkg:.2f}, std={target_std:.2f}\n'
    text += f'$\Delta$(SEP): {sep_diff:.2f}$\sigma$, $\Delta$(ASTROPY): {astro_diff:.2f}$\sigma$'
    
    fig.add_label(0.04, 0.11, text, relative=True, **{"family": font_family, 
                                                      "size": 18, 
                                                      "weight":"bold",
                                                      "horizontalalignment":"left",
                                                      "bbox":{"boxstyle":"round", "facecolor":"white", "alpha":0.7},
                                                      #"alpha":0.6,
                                                     })
    
    # ticks
    fig.tick_labels.set_font(**{"family": font_family, "size": 18})
    fig.tick_labels.set_xformat("dd.dd")
    fig.tick_labels.set_yformat("dd.dd")
    fig.ticks.set_length(6)

    fig.axis_labels.set_font(**{"family": font_family, "size": 18})
    fig.set_theme("publication")

    # output
    if outfile is not None:
        plt.savefig(outfile)
    if show_plot:
        plt.show()
    else:
        plt.ioff()
    
def check_background(file, ra, dec, r_in=3, r_out=6, method='mean', percent=90, size=1.0, show_plot=True, dest_dir=""):
    """Calculates the difference, in sigmas, between an image global
    background and the background around the given coordinates.
    
    Examples:
    diff = np.abs(target_percentile - bkg_mean)/bkg_std
    diff = np.abs(target_percentile - bkg_median)/bkg_std
    
    Parameters
    ----------
    file: str
        Name of the FITS file.
    ra: float
        Right ascension.
    dec: float
        Declination.
    r_in: float, default '3'
        Inner radius of the annulus (in arcsec).
    r_out: float, default '6'
        Outer radius of the annulus (in arcsec).
    method: str, default 'mean'
        Method used to estimate the difference in background.
        Either 'mean' or 'median'. SEP only uses 'mean'.
    percent: int, default '90'
        Percentile used for the background around the target.
    size: float, default '1.0'
        Size of the image to be plotted, in arcminutes.
    show_plot: bool default 'True'
        Whether to show the image with the annulus used.
    dest_dir: str, default '"'
        Where to save the output files.
    """
    data, header, img_wcs, hdu = extract_image(file)
    
    # sep and astropy background statistics
    sep_mean, sep_std = get_sep_stats(data)
    astro_mean, astro_median, astro_std = get_astropy_stats(data)
    # target's background statistics using an annulus
    aperstats = get_target_stats(data, img_wcs, ra, dec, r_in, r_out)
    aperture = aperstats.aperture
    target_bkg = np.percentile(aperstats.data_cutout.data, percent)
    target_std = aperstats.std  # not used as it is not a good statistic
    
    assert method in ['mean', 'median'], "Not a valid method!"
    
    # calculate difference in background level, in units of sigmas
    sep_diff = np.abs(target_bkg-sep_mean)/sep_std
    if method=='mean':
        astro_diff = np.abs(target_bkg-astro_mean)/astro_std
    elif method=='median':
        astro_diff = np.abs(target_bkg-astro_median)/astro_std
     
    # save output into a file
    out_dict = {'file':[file],
                'ra':[ra],
                'dec':[dec],
                'r_in':[r_in],
                'r_out':[r_out],
                'method':[method],
                'sep_diff':[sep_diff],
                'astro_diff':[astro_diff],
                'sep_mean':[sep_mean],
                'sep_std':[sep_std],
                'astro_mean':[astro_mean],
                'astro_median':[astro_median],
                'astro_std':[astro_std],
                'annulus_bkg':[target_bkg],
                'annulus_std':[target_std],
                'annulus_percent':[percent]
               }
    
    df = pd.DataFrame(out_dict)
    outfile = os.path.basename(file).replace('.fits', '')
    outfile = os.path.join(dest_dir, 'bkg_' + outfile + '.csv')
    df.to_csv(outfile, index=False)

    print(f'SEP: {np.round(sep_diff, 2)} sigmas')
    print(f'ASTROPY: {np.round(astro_diff, 2)} sigmas')

    # plotting    
    info_dict = {'sep':[sep_mean, sep_std],
                    'astro':[astro_mean, astro_median, astro_std],
                    'target':[target_bkg, target_std, percent],
                    'sep_diff':sep_diff,
                    'astro_diff':astro_diff,
                }
    outfile = outfile.replace('.csv', '.jpg')
    plot_target(hdu, ra, dec, aperture, size, info_dict, show_plot, outfile)
        
        
def main(args=None):
    description = f"Checks image background to identify the need of templates for image subtraction"
    usage = "check_background file ra dec [options]"
    
    if not args:
        args = sys.argv[1:] if sys.argv[1:] else ["--help"]
        
    parser = argparse.ArgumentParser(prog='check_background',
                                     usage=usage,
                                     description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument("file",
                        type=str,
                        help="Name of the FITS file."
                        )
    parser.add_argument("ra",
                        type=float,
                        help="Right ascension."
                        )
    parser.add_argument("dec",
                        type=float,
                        help="Declination."
                        )
    parser.add_argument("--r_in",
                        dest="r_in",
                        action="store",
                        default=3,
                        type=float,
                        help="Inner radius of the annulus."
                        )
    parser.add_argument("--r_out",
                        dest="r_out",
                        action="store",
                        default=6,
                        type=float,
                        help="Outer radius of the annulus."
                        )
    parser.add_argument("-p",
                        "--percent",
                        dest="percent",
                        action="store",
                        default=90,
                        type=int,
                        help="Annulus percentile."
                        )
    parser.add_argument("-m"
                        "--method",
                        dest="method",
                        action="store",
                        default="mean",
                        choices=["mean", "median"],
                        type=str,
                        help=("Method used to estimate the difference in background."
                              "Either 'mean' or 'median'. SEP only uses 'mean'.")
                        )
    parser.add_argument("-s",
                        "--size",
                        dest="size",
                        action="store",
                        default=1,
                        type=float,
                        help="Size of the image to be plotted, in arcminutes."
                        )
    parser.add_argument("--show_plot",
                        dest="show_plot",
                        action="store",
                        default=1,
                        choices=[0, 1],
                        type=int,
                        help="Whether to show the image with the annulus used."
                        )
    parser.add_argument("--dest_dir",
                        dest="dest_dir",
                        action="store",
                        default="",
                        type=str,
                        help="Where to store the output files."
                        )
    
    args = parser.parse_args(args)
    check_background(args.file, args.ra, args.dec, args.r_in, args.r_out, 
                     args.method, args.percent, args.size, args.show_plot, args.dest_dir)

if __name__ == "__main__":
    main(sys.argv[1:])