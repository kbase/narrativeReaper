#!/usr/bin/python

import requests

import urllib3
# there is a way to only disable InsecurePlatformWarning but I can't find it now
urllib3.disable_warnings()

def get_proxy_map(proxyMapUrl):
    proxy_map = requests.get(proxyMapUrl)
    return proxy_map

def main():
    proxyMapUrl='https://next.kbase.us/proxy_map'
    print get_proxy_map(proxyMapUrl).json()

if __name__ == "__main__":
    main()
