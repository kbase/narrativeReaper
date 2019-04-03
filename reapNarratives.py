#!/usr/bin/python

import sys
import os
import pickle
import time
import json
import argparse
# ideally would use the docker lib, for now use a subprocess to exec into the container
import subprocess
#import docker
import requests
import pprint
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
# these are a bit crude, assumes that narrative sockets are all ESTABLISHED and on port 8888
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

def reaper(currentProxyMap, localProxyMap, shutdownUrl,estConnections,timeout, reapContainers, verbose):
    now = time.time()

    currentProxyMapUsers = []
    
    for session in currentProxyMap:
        # skip provisioned containers
        if session['state'] == 'queued':
            continue

        # real username is in proxy map, track to compare to local map
        currentProxyMapUsers.append(session['session_id'])

        if session['proxy_target'] in estConnections:
            if verbose:
                print session['session_id'] + ' currently has an established connection, updating local map'
# use what's currently in active proxy map, in case it's a new connection
            localProxyMap[session['session_id']] = session
            localProxyMap[session['session_id']]['last_seen'] = estConnections[session['proxy_target']]
        else:
            if session['session_id'] not in localProxyMap:
# if we are here, it probably means a user opened a narrative then closed the browser before next run
# of reapNarratives.  create a bogus local map entry, worst case scenario it will be expired in timeout
# seconds
                if verbose:
                    sys.stderr.write("session " + session['session_id'] + " not in local proxy map, creating dummy entry\n")
                localProxyMap[session['session_id']] = session
                localProxyMap[session['session_id']]['last_seen'] = now
#            pp.pprint(localProxyMap[session['session_id']])
            sessionAge = now - float(localProxyMap[session['session_id']]['last_seen'])
            if sessionAge > timeout:
                if reapContainers:
                    if verbose:
                        print session['session_id'] + ' in current proxy map to be reaped, ' + str(sessionAge) + ' seconds old'
                    if shutdown_session(shutdownUrl,session['session_id']):
                        # pop returns the value and removes it from the dict
                        localProxyMap.pop(session['session_id'])
                    else:
                        sys.stderr.write("unable to delete current session " + session['session_id'] + " !\n")
                else:
                    print session['session_id'] + ' in current proxy map would be reaped, ' + str(sessionAge) + ' seconds old'

            else:
                if verbose:
                    print session['session_id'] + ' in current proxy map ' + str(sessionAge) + ' seconds old, not reaping'

    localEntriesToDelete = []

# it's possible a narrative could be deleted in the nginx proxy map but still
# appear in the local proxy map (e.g., if /narrative_shutdown_noauth/userid
# was called outside this script).  this part cleans up the local proxy map

# this seems clumsy
    for localSessionId in localProxyMap:
        if localSessionId not in currentProxyMapUsers:
            if verbose:
                print localSessionId + ' not in current proxy map, removing local map entry'
            localEntriesToDelete.append(localSessionId)
# can't change dict while iterating over it, so need a separate loop
    for localSessionId in localEntriesToDelete:
        localProxyMap.pop(localSessionId)

    return localProxyMap

def main():

    parser = argparse.ArgumentParser(description='List and by default reap old narrative containers.')
    parser.add_argument('--proxyMapUrl')
    parser.add_argument('--nginxContainerName')
    parser.add_argument('--pickleFilePath')
    parser.add_argument('--shutdownUrl')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--reapContainers', default=False, action='store_true')
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()

#    proxyMapUrl=sys.argv[1]
#    nginxContainerName = sys.argv[2]
#    pickleFilePath = sys.argv[3]
#    shutdownUrl = sys.argv[4]
#    timeout = sys.argv[5]

# needed only to initialize
    if (not os.path.isfile(args.pickleFilePath)):
        sys.stderr.write("creating new pickle file " + args.pickleFilePath + "\n")
        save_pickle_data({}, args.pickleFilePath)

    oldProxyMap = read_pickle_data(args.pickleFilePath)
    estConnections = est_connections(args.nginxContainerName)
    newProxyMap = reaper(get_proxy_map(args.proxyMapUrl), oldProxyMap, args.shutdownUrl, estConnections, int(args.timeout), args.reapContainers,args.verbose)
    save_pickle_data(newProxyMap, args.pickleFilePath)

#    pp.pprint(newProxyMap)

if __name__ == "__main__":
    main()
