#!/usr/bin/env python2
#
# present statistics from dabmux Stats Server
# to munin

import sys
import json
import zmq
import os

ctx = zmq.Context()

def connect():
    """Create a connection to the dabmux stats server

    returns: the socket"""

    sock = zmq.Socket(ctx, zmq.REQ)
    sock.connect("tcp://localhost:12720")

    sock.send("info")
    version = json.loads(sock.recv())

    if not version['service'].startswith("ODR-DabMux"):
        sys.stderr.write("Wrong version\n")
        sys.exit(1)

    return sock

if len(sys.argv) == 1:
    sock = connect()
    sock.send("values")
    values = json.loads(sock.recv())['values']

    tmpl = "{ident:20}{maxfill:>8}{minfill:>8}{under:>8}{over:>8}{peakleft:>8}{peakright:>8}"
    print(tmpl.format(
        ident="id",
        maxfill="max",
        minfill="min",
        under="under",
        over="over",
        peakleft="peak L",
        peakright="peak R"))

    for ident in values:
        v = values[ident]['inputstat']
        print(tmpl.format(
            ident=ident,
            maxfill=v['max_fill'],
            minfill=v['min_fill'],
            under=v['num_underruns'],
            over=v['num_overruns'],
            peakleft=v['peak_left'],
            peakright=v['peak_right']))


elif len(sys.argv) == 2 and sys.argv[1] == "config":
    sock = connect()

    sock.send("config")

    config = json.loads(sock.recv())

    print(config['config'])

