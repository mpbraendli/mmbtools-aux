#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Read two IQ files, complexf 2048000, and sum them
# together with separate amplitudes and add noise.
#
# It requires SciPy and matplotlib.
#
# http://www.opendigitalradio.org
# Licence: The MIT License, see notice at the end of this file

import sys
import numpy as np

import argparse

def main():
    parser = argparse.ArgumentParser(description="MergeIQ")
    #parser.add_argument('--noise', default='0', help='Noise amplitude to add', required=False)
    parser.add_argument('--delay', default='20', help='Number of samples delay of second file', required=False)
    #parser.add_argument('--noise', action='store_const', const=True, help='Test all comb pattern values', required=False)

    cli_args = parser.parse_args()

    num_samples = 1024
    delay = int(cli_args.delay)

    fd1 = open("ofdm-c1p12.iq", "rb")
    fd2 = open("ofdm-c2p12.iq", "rb")
    fd_out = open("ofdm.iq", "wb")

    frame1 = np.fromfile(fd1, np.complex64, count=num_samples)
    frame2 = np.fromfile(fd2, np.complex64, count=num_samples-delay)
    frame2 = np.concatenate((np.zeros(delay, dtype=np.complex64), frame2))

    totalsize = 0
    while True:
        n = 0.000001
        noise_r = np.random.normal(0, n, num_samples)
        noise_i = np.random.normal(0, n, num_samples)
        noise = noise_r + 1j * noise_i
        sum_frame = 0.8 * frame1 + 0.22 * frame2 + noise.astype(np.complex64)
        totalsize += len(sum_frame)
        fd_out.write(sum_frame.tobytes())

        frame1 = np.fromfile(fd1, np.complex64, count=num_samples)
        frame2 = np.fromfile(fd2, np.complex64, count=num_samples)

        if len(frame1) != num_samples or len(frame2) != num_samples:
            print("Stop {}".format(totalsize))
            break

main()
