#!/usr/bin/python

import requests
import sys
import os
import json
#import psutil
import pprint
import docker
import subprocess
import pickle
import time

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
    
def est_connections():

    filename='proxymap.pickle'
    connectionMap = read_pickle_data(filename)
#    pp.pprint(connectionMap)
    timestamp = time.time()

    containerName='r-next-core-nginx-1-edfd1207'
    netstatOut = subprocess.check_output(['docker','exec',containerName,'netstat','-nt'])
    for line in netstatOut.split('\n'):
        if 'ESTABLISHED' not in line:
            continue
        if '8888' not in line:
            continue
        splitLine = line.split()
        connectionMap[splitLine[4]] = timestamp

#    dockerClient = docker.from_env()
#    print dockerClient
#    nginxContainer = dockerClient.containers.get(containerName)
#    allConnections = nginxContainer.exec_run('netstat -nt')
#    allConnections = psutil.net_connections()
#    for conn in allConnections:
#        pp.pprint(conn)

    save_pickle_data(connectionMap, 'proxymap.pickle')
#    pp.pprint(connectionMap)
    return connectionMap

def get_proxy_map(proxyMapUrl):
    proxy_map = requests.get(proxyMapUrl)
    return proxy_map.json()

def marker(proxyMap):
    estConnections = est_connections()
    for session in proxyMap:
        # skip provisioned containers
        if session['state'] == 'queued':
            continue
        if session['proxy_target'] in estConnections:
            print session['session_id'] + ' in estConnections '
        else:
            print session['session_id'] + ' not in estConnections '

def main():
    # needed only to initialize
    # put this in an if which sees if file exists and inits if not

    pickleFile = 'proxymap.pickle'
    proxyMapUrl=sys.argv[1]

    if (not os.path.isfile('/path/to/file')):
        save_pickle_data({}, pickleFile)

# read in connections (from pickle file and current)
# find connections in proxy_map but aged out/idle: DELETE and remove from connection dict
# find connections no longer in proxy_map: remove from connection dict
# save pickle file

    marker(get_proxy_map(proxyMapUrl))
#    pp.pprint(get_proxy_map(proxyMapUrl))
#    pp.pprint(est_connections())

if __name__ == "__main__":
    main()
