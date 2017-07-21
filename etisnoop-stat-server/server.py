#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This is the main program that
# - Runs rtlsdr and etisnoop for 200 ETI frames
#   and generate the stats.yml
# - Runs a webserver
#
# Copyright (C) 2017
# Matthias P. Braendli, matthias.braendli@mpb.li
# http://www.opendigitalradio.org
# Licence: The MIT License, see LICENCE file

import sys
from bottle import route, run, template, static_file, request
import subprocess
import time
import datetime
import multiprocessing as mp
import threading
import shlex
import argparse
import collections

class StatCollector(threading.Thread):
    def __init__(self, options):
        threading.Thread.__init__(self)

        self.num_eti_frames = int(options.num_eti_frames)
        self.gain = int(options.gain)
        self.freq = int(options.freq)
        self.event_stop = threading.Event()

        self.dab2eti_proc = None

        self.stats_lock = threading.Lock()
        self.stats = None

    def run(self):
        if self.gain == 0:
            gain = ""
        else:
            gain = self.gain
        dab2eti_cmdline = "dab2eti {} {} | etisnoop -s stats.yml -n {}".format(
                    self.freq, gain, self.num_eti_frames)

        print("Cmdline: " + repr(dab2eti_cmdline))

        while not self.event_stop.is_set():
            print("Entering capture loop, start RX")
            self.dab2eti_proc = subprocess.Popen(dab2eti_cmdline, shell=True)
            ret = self.dab2eti_proc.wait()
            print("Quit with return value {}".format(ret))

            self.stats_lock.acquire()
            try:
                self.stats = open("stats.yml").read()
                print("Stats loaded, {} chars".format(len(self.stats)))
            except Exception as e:
                self.stats = "exception: {}".format(e)
            finally:
                self.stats_lock.release()
            time.sleep(15)

    def stop(self):
        print("Set stop event")
        self.event_stop.set()
        self.join()

    def getstats(self):
        """Return a str YAML if stats are available, or None"""
        self.stats_lock.acquire()
        stats = self.stats
        self.stats_lock.release()
        return stats


@route('/')
def index():
    stats = stat_collector.getstats()

    if stats is None:
        stats = "status: not ready"

    return template('index',
            freq = cli_args.freq,
            gain = cli_args.gain,
            stats = stats)

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root='./static')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ETISnoop statistics')

    # Options for the webserver
    parser.add_argument('--host', default='127.0.0.1', help='socket host (default: 127.0.0.1)',required=False)
    parser.add_argument('--port', default='8000', help='socket port (default: 8000)',required=False)

    # Options for RTLSDR reception
    parser.add_argument('--freq', help='Receive frequency', required=True)
    parser.add_argument('--num-eti-frames',
            default=200,
            help='Number of ETI frames to analyse.',
            required=False)
    parser.add_argument('--gain', default=0,
            help='Gain setting for rtl_sdr, 0 for auto', required=False)

    cli_args = parser.parse_args()

    stat_collector = StatCollector(cli_args)
    stat_collector.start()

    try:
        run(host=cli_args.host, port=int(cli_args.port), debug=True, reloader=False)
    finally:
        stat_collector.stop()
