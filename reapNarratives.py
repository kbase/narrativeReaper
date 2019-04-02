#!/usr/bin/python

import requests
import sys
import json
import psutil

import urllib3
# there is a way to only disable InsecurePlatformWarning but I can't find it now
urllib3.disable_warnings()

def est_connections():
    return psutil.net_connections()

def get_proxy_map(proxyMapUrl):
    proxy_map = requests.get(proxyMapUrl)
    return proxy_map.json()

def main():
    proxyMapUrl='https://next.kbase.us/proxy_map'
    print get_proxy_map(proxyMapUrl)
    print est_connections()

if __name__ == "__main__":
    main()
