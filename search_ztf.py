#!/usr/bin/env python

import subprocess
try:
    from tns_api.api import get_object
except:
    pass

def main():
    sn_name = input('Enter the SN IAU name (e.g., 2022vqz) or ZTF internal name (e.g. ZTF22abhrjld):')

    if sn_name.startswith('ZTF') is False:
        sn_name_ztf = sn_name
        # look for ZTF name
        sn_dict = get_object(sn_name)
        if isinstance(sn_dict['internal_names'], str):
            sn_dict['internal_names'] = [sn_dict['internal_names']]

        for name in sn_dict['internal_names']:
            if name.startswith('ZTF'):
                sn_name_ztf = name
                break
        
        if sn_name_ztf.startswith('ZTF') is False:
            raise NameError(f'No ZTF name found: {sn_name}')
    else:
        sn_name_ztf = sn_name

    urls = ['https://wis-tns.weizmann.ac.il/object/' + sn_name,
            'https://alerce.online/object/' + sn_name_ztf,

    ]
    for url in urls:
        subprocess.call(['firefox', '-new-tab', '-url', url])

main()
