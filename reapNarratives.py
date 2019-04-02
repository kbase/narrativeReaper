#!/usr/bin/python

import requests
import sys
import json
import pickle

import urllib3
# there is a way to only disable InsecurePlatformWarning but I can't find it now
urllib3.disable_warnings()

def pickleFile(filename):
    pickleFh = open (filename)
    pickle.dump(get_proxy_map(proxyMapUrl) , pickleFh )
    close pickleFh

def get_proxy_map(proxyMapUrl):
    proxy_map = requests.get(proxyMapUrl)
    return proxy_map

def main():
    proxyMapUrl='https://next.kbase.us/proxy_map'
    pickleFilename='pickle.python'
    pickleFile(pickleFilename)

if __name__ == "__main__":
    main()
