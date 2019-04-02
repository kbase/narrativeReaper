#!/usr/bin/python

import requests
import sys
import json
import psutil
import pprint

import urllib3
# there is a way to only disable InsecurePlatformWarning but I can't find it now
urllib3.disable_warnings()

def est_connections():
    return psutil.net_connections()

def get_proxy_map(proxyMapUrl):
    proxy_map = requests.get(proxyMapUrl)
    return proxy_map.json()

def marker(proxyMap):
    for session in proxyMap:
        print session['last_ip']

def main():
    pp = pprint.PrettyPrinter(indent=4)
    proxyMapUrl='https://next.kbase.us/proxy_map'
    marker(get_proxy_map(proxyMapUrl))
#    pp.pprint(get_proxy_map(proxyMapUrl))
    pp.pprint(est_connections())

if __name__ == "__main__":
    main()
