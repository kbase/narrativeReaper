#!/usr/bin/python

import requests
import sys
import os
import json
import pprint
import docker
import subprocess
import pickle
import time
# was hoping to use psutil.net_connections() but the container runs in a different namespace
#import psutil

import urllib3
# there is a way to only disable InsecurePlatformWarning but I can't find it now
urllib3.disable_warnings()

pp = pprint.PrettyPrinter(indent=4)

def read_pickle_data(filename):
    fh = open (filename)
    data = pickle.load(fh)
    fh.close()
    return data

def save_pickle_data(obj, filename):
    fh = open (filename, 'w')
    data = pickle.dump(obj, fh)
    fh.close()
    
def est_connections(filename,containerName):

    connectionMap = read_pickle_data(filename)
    timestamp = time.time()

    # would prefer to use docker lib but not working at the moment
    netstatOut = subprocess.check_output(['docker','exec',containerName,'netstat','-nt'])
    for line in netstatOut.split('\n'):
        if 'ESTABLISHED' not in line:
            continue
        if '8888' not in line:
            continue
        splitLine = line.split()
        connectionMap[splitLine[4]] = timestamp

    save_pickle_data(connectionMap, filename)
    return connectionMap

def get_proxy_map(proxyMapUrl):
    proxy_map = requests.get(proxyMapUrl)
    return proxy_map.json()

def marker(proxyMap,estConnections,timeout):
    now = time.time()

    for session in proxyMap:
        # skip provisioned containers
        if session['state'] == 'queued':
            continue
        if session['proxy_target'] in estConnections:
            sessionAge = now - estConnections[session['proxy_target']]
            print session['session_id'] + ' in estConnections ' + str(sessionAge) + ' seconds old'
        else:
            print session['session_id'] + ' not in estConnections '

def main():
    # needed only to initialize
    # put this in an if which sees if file exists and inits if not

    proxyMapUrl=sys.argv[1]
    nginxContainerName = sys.argv[2]
    pickleFile = sys.argv[3]
    timeout = 600

    if (not os.path.isfile(pickleFile)):
        sys.stderr.write("creating new pickle file " + pickleFile + "\n")
        save_pickle_data({}, pickleFile)

# read in connections (from pickle file and current)
# find connections in proxy_map but aged out/idle: DELETE and remove from connection dict
# find connections no longer in proxy_map: remove from connection dict
# save pickle file

    estConnections = est_connections(pickleFile, nginxContainerName)
    marker(get_proxy_map(proxyMapUrl), estConnections,timeout)
#    pp.pprint(get_proxy_map(proxyMapUrl))
#    pp.pprint(est_connections())

if __name__ == "__main__":
    main()
