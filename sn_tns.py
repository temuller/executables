#!/usr/bin/env python

import os
import requests
import pandas as pd


def tns_user_agent(tns_id, name):
    """Sets up the user-agent for Transient
    Name Server (TNS) website.

    **Note:** you can check 'MY ACCOUNT'
    on the website for your information.

    Parameters
    ==========
    tns_id, str
        TNS ID number.
    name, str
        TNS username.

    Returns
    =======
    headers, dict
        Headers with the user-agen information.
    """

    headers = {'User-Agent': '{"tns_id":"%s", \
                              "type":"user", \
                              "name":"%s"}' % (tns_id, name)
               }

    return headers

def main():
    sn_name = input('SN name (e.g. 2011fe): ')

    headers = tns_user_agent('2034', 'temuller-bravo')
    TNS = 'https://www.wis-tns.org'

    try:
        url = f'{TNS}/search?&name={sn_name}&format=csv'
        response = requests.get(url, headers=headers)

        # 200: OK; 429: too many requests (sleep for a bit)
        if response.status_code == 200:
            pass
        elif response.status_code == 429:
            sleep_time = int(response.headers['x-rate-limit-reset'])
            time.sleep(sleep_time)
            # try again
            response = requests.get(url, headers=headers)

    except Exception as message:
        print(f'{sn_name} failed: {message}.')

    with open('temp.csv', 'wb') as file:
        file.write(response.content)

    sn_df = pd.read_csv('temp.csv')
    os.remove('temp.csv')

    params = ['Name', 'RA', 'DEC', 'Obj. Type', 'Redshift', 'Host Name', 'Host Redshift']

    for param in params:
        param_value = sn_df[param].values[0]
        print(f'{param}: {param_value}')

main()
