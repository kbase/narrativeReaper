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
    deleteUrl = url + '/' + sessionId
    sys.stderr.write("about to delete " + deleteUrl + " \n")

    response = requests.delete(deleteUrl)
    if response.status_code == requests.codes.ok:
        sys.stderr.write("successfully deleted " + deleteUrl + " \n")
    else:
# need better error reporting here
        sys.stderr.write("deleting " + deleteUrl + " failed!\n")
        
    return response.status_code == requests.codes.ok

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

def reaper(currentProxyMap, localProxyMap, shutdownUrl,estConnections,timeout):
    now = time.time()

    currentProxyMapUsers = []
    
    for session in currentProxyMap:
        # skip provisioned containers
        if session['state'] == 'queued':
            continue

        # real username is in proxy map, track to compare to local map
        currentProxyMapUsers.append(session['session_id'])

        if session['proxy_target'] in estConnections:
            print session['session_id'] + ' currently has an established connection, updating local map'
# use what's currently in active proxy map, in case it's a new connection
            localProxyMap[session['session_id']] = session
            localProxyMap[session['session_id']]['last_seen'] = estConnections[session['proxy_target']]
        else:
            if session['session_id'] not in localProxyMap:
                sys.stderr.write("session " + session['session_id'] + " not in local proxy map, creating dummy entry\n")
                localProxyMap[session['session_id']] = session
                localProxyMap[session['session_id']]['last_seen'] = now()
#            pp.pprint(localProxyMap[session['session_id']])
            sessionAge = now - float(localProxyMap[session['session_id']]['last_seen'])
            if sessionAge > timeout:
                print session['session_id'] + ' in proxy map to be timed out ' + str(sessionAge) + ' seconds old'
                if shutdown_session(shutdownUrl,session['session_id']):
                    # pop returns the value and removes it from the dict
                    localProxyMap.pop(session['session_id'])
                else:
                    sys.stderr.write("unable to delete session " + session['session_id'] + " !\n")
            else:
                print session['session_id'] + ' in proxy map ' + str(sessionAge) + ' seconds old, not reaping'

    localEntriesToDelete = []

# this seems clumsy
    for localSessionId in localProxyMap:
        if localSessionId not in currentProxyMapUsers:
            print localSessionId + ' not in current proxy map, removing local map entry'
            localEntriesToDelete.append(localSessionId)
# can't change dict while iterating over it, so need a separate loop
    for localSessionId in localEntriesToDelete:
        localProxyMap.pop(localSessionId)

    return localProxyMap

def main():
# read in previous proxy map from pickle file
# read connections fron inside container
# find connections in proxy_map but aged out/idle: DELETE and remove from local map dict
# find connections no longer in proxy_map: remove from local map dict
# save local proxy map pickle file

    proxyMapUrl=sys.argv[1]
    nginxContainerName = sys.argv[2]
    pickleFile = sys.argv[3]
    shutdownUrl = sys.argv[4]
    timeout = sys.argv[5]

    # needed only to initialize
    # put this in an if which sees if file exists and inits if not
    if (not os.path.isfile(pickleFile)):
        sys.stderr.write("creating new pickle file " + pickleFile + "\n")
        save_pickle_data({}, pickleFile)

    oldProxyMap = read_pickle_data(pickleFile)
    estConnections = est_connections(nginxContainerName)
    newProxyMap = reaper(get_proxy_map(proxyMapUrl), oldProxyMap, shutdownUrl, estConnections, int(timeout))
    save_pickle_data(newProxyMap, pickleFile)

    pp.pprint(newProxyMap)
#    pp.pprint(get_proxy_map(proxyMapUrl))
#    pp.pprint(est_connections())

if __name__ == "__main__":
    main()
