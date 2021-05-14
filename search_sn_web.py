#!/usr/bin/env python

import subprocess

def main():
    sne = input('Enter SN name (e.g., SN2011fe) or list of them:')
    website = input('Choose website(s) (tns|osc|wiserep|all or list of them):')

    for sn in sne.split(' '):

        url_dict = {'tns':'https://wis-tns.weizmann.ac.il/object/' + sn[2:],
                    'osc':'https://sne.space/sne/' + sn,
                    'wiserep':'https://wiserep.weizmann.ac.il/search?name=' + sn
                   }

        if website=='all' or website=='':
            for url in url_dict.values():
                subprocess.call(['firefox', '-new-tab', '-url', url])

        else:
            for site in website.split():
                url = url_dict[site]
                subprocess.call(['firefox', '-new-tab', '-url', url])

main()
