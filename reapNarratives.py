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

def shutdown_session(url,sessionId):
    return 0

def est_connections(containerName):

    timestamp = time.time()
    connectionMap = {}

    # would prefer to use docker lib but not working at the moment
    netstatOut = subprocess.check_output(['docker','exec',containerName,'netstat','-nt'])
    for line in netstatOut.split('\n'):
        if 'ESTABLISHED' not in line:
            continue
        if '8888' not in line:
            continue
        splitLine = line.split()
        connectionMap[splitLine[4]] = timestamp

    return connectionMap

def get_proxy_map(proxyMapUrl):
    proxy_map = requests.get(proxyMapUrl)
    return proxy_map.json()

def marker(currentProxyMap, localProxyMap, shutdownUrl,estConnections,timeout):
    now = time.time()

    for session in currentProxyMap:
        # skip provisioned containers
        if session['state'] == 'queued':
            continue
        if session['proxy_target'] in estConnections:
            print session['session_id'] + ' currently has an established connection, updating local map'
# use what's currently in active proxy map, in case it's a new connection
            localProxyMap[session['session_id']] = session
            localProxyMap[session['session_id']]['last_seen'] = estConnections[session['proxy_target']]
        else:
#            pp.pprint(localProxyMap[session['session_id']])
            sessionAge = now - float(localProxyMap[session['session_id']]['last_seen'])
            if sessionAge > timeout:
                print session['session_id'] + ' in proxy map to be timed out ' + str(sessionAge) + ' seconds old'
                if shutdown_session(shutdownUrl,session['session_id']):
                    # pop returns the value and removes it from the dict
                    localProxyMap.pop(session['proxy_target'])
                else:
                    sys.stderr.write("unable to delete session " + session['session_id'] + " !\n")
            else:
                print session['session_id'] + ' in proxy map ' + str(sessionAge) + ' seconds old, not reaping'
#            print session['session_id'] + ' not in estConnections, skipping'
#            print session['session_id'] + ' not in estConnections, age ' + str(now - float(localProxyMap['last_seen']))
#            localProxyMap[session['session_id']] = session
#            localProxyMap[session['session_id']]['age'] = sessionAge

    for localSession in localProxyMap:
        pp.pprint (localSession)
        if localSession['session_id'] not in currentProxyMap:
            print localSession['session_id'] + ' not in current proxy map, removing from local map'

    return localProxyMap

def main():
    # needed only to initialize
    # put this in an if which sees if file exists and inits if not

    proxyMapUrl=sys.argv[1]
    nginxContainerName = sys.argv[2]
    pickleFile = sys.argv[3]
    shutdownUrl = sys.argv[4]
    timeout = sys.argv[5]

    if (not os.path.isfile(pickleFile)):
        sys.stderr.write("creating new pickle file " + pickleFile + "\n")
        save_pickle_data({}, pickleFile)

# read in connections (from pickle file and current)
# find connections in proxy_map but aged out/idle: DELETE and remove from connection dict
# find connections no longer in proxy_map: remove from connection dict
# save pickle file

    oldProxyMap = read_pickle_data(pickleFile)
    estConnections = est_connections(nginxContainerName)
    newProxyMap = marker(get_proxy_map(proxyMapUrl), oldProxyMap, shutdownUrl, estConnections, int(timeout))
    save_pickle_data(newProxyMap, pickleFile)

    pp.pprint(newProxyMap)
#    pp.pprint(get_proxy_map(proxyMapUrl))
#    pp.pprint(est_connections())

if __name__ == "__main__":
    main()
