#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Analyse TII of iq file. complexf 2048000
#
# It requires SciPy and matplotlib.
#
# http://www.opendigitalradio.org
# Licence: The MIT License, see notice at the end of this file

import sys
import functools
import numpy as np
import matplotlib.pyplot as pp
import argparse
import subprocess
from scipy.misc import imsave
from tii import calculate_carrier_indices, calculate_reduced_carrier_indices

all_tii_patterns = {}
cp_per_carrier = {}

def prepare_tii_patterns():
    print("Building TII table...")
    global all_tii_patterns
    global cp_per_carrier

    for c in range(24):
        for p in range(70):
            carriers = calculate_carrier_indices(c, p)
            all_tii_patterns[tuple(carriers)] = (c, p)

            carriers = calculate_reduced_carrier_indices(c, p)
            for k in carriers:
                if k not in cp_per_carrier:
                    cp_per_carrier[k] = set()
                cp_per_carrier[k].add((c, p))

SIZEOF_SAMPLE = 8 # complex floats

# Constants for TM 1
NbSymbols = 76
NbCarriers = 1536
Spacing = 2048
NullSize = 2656
SymSize = 2552
FicSizeOut = 288

CyclicPrefix = SymSize - Spacing

prs_phases = np.array([0, -1, 1, -1, -1, -1, -1, 0, 0, 1, -1, -1, -1, 1, 1, 0, 0, -1, 1,
        -1, -1, -1, -1, 0, 0, 1, -1, -1, -1, 1, 1, 0, 0, 1, 2, -1, 2, 1, 0, 0,
        -1, -1, 0, -1, 2, -1, 2, 0, -1, 1, 2, -1, 2, 1, 0, 0, -1, -1, 0, -1, 2,
        -1, 2, 0, -1, 1, 1, 1, -1, 1, -1, 2, 0, -1, -1, 1, -1, -1, 1, 2, 0, 1,
        1, 1, -1, 1, -1, 2, 0, -1, -1, 1, -1, -1, 1, 2, 0, 1, 0, -1, 0, 1, 2,
        0, 1, -1, 2, -1, 0, -1, 0, 0, 1, 1, 0, -1, 0, 1, 2, 0, 1, -1, 2, -1, 0,
        -1, 0, 0, 1, 2, 0, 2, 2, 2, 2, -1, -1, 0, 2, 2, 2, 0, 0, -1, -1, 2, 0,
        2, 2, 2, 2, -1, -1, 0, 2, 2, 2, 0, 0, -1, -1, 2, -1, 0, -1, 2, 1, 1, 0,
        0, 1, 0, -1, 0, -1, 1, 0, 2, -1, 0, -1, 2, 1, 1, 0, 0, 1, 0, -1, 0, -1,
        1, 0, 1, 1, 1, -1, 1, -1, 2, 0, -1, -1, 1, -1, -1, 1, 2, 0, 1, 1, 1,
        -1, 1, -1, 2, 0, -1, -1, 1, -1, -1, 1, 2, 0, 0, -1, 2, -1, 0, 1, -1, 0,
        2, 1, 2, -1, 2, -1, -1, 0, 0, -1, 2, -1, 0, 1, -1, 0, 2, 1, 2, -1, 2,
        -1, -1, 0, 2, 0, 2, 2, 2, 2, -1, -1, 0, 2, 2, 2, 0, 0, -1, -1, 2, 0, 2,
        2, 2, 2, -1, -1, 0, 2, 2, 2, 0, 0, -1, -1, 2, -1, 0, -1, 2, 1, 1, 0, 0,
        1, 0, -1, 0, -1, 1, 0, 2, -1, 0, -1, 2, 1, 1, 0, 0, 1, 0, -1, 0, -1, 1,
        0, -1, -1, -1, 1, -1, 1, 0, 2, 1, 1, -1, 1, 1, -1, 0, 2, -1, -1, -1, 1,
        -1, 1, 0, 2, 1, 1, -1, 1, 1, -1, 0, 2, -1, 2, 1, 2, -1, 0, 2, -1, 1, 0,
        1, 2, 1, 2, 2, -1, -1, 2, 1, 2, -1, 0, 2, -1, 1, 0, 1, 2, 1, 2, 2, -1,
        0, 2, 0, 0, 0, 0, 1, 1, 2, 0, 0, 0, 2, 2, 1, 1, 0, 2, 0, 0, 0, 0, 1, 1,
        2, 0, 0, 0, 2, 2, 1, 1, 2, -1, 0, -1, 2, 1, 1, 0, 0, 1, 0, -1, 0, -1,
        1, 0, 2, -1, 0, -1, 2, 1, 1, 0, 0, 1, 0, -1, 0, -1, 1, 0, 1, 1, 1, -1,
        1, -1, 2, 0, -1, -1, 1, -1, -1, 1, 2, 0, 1, 1, 1, -1, 1, -1, 2, 0, -1,
        -1, 1, -1, -1, 1, 2, 0, -1, 2, 1, 2, -1, 0, 2, -1, 1, 0, 1, 2, 1, 2, 2,
        -1, -1, 2, 1, 2, -1, 0, 2, -1, 1, 0, 1, 2, 1, 2, 2, -1, -1, 1, -1, -1,
        -1, -1, 0, 0, 1, -1, -1, -1, 1, 1, 0, 0, -1, 1, -1, -1, -1, -1, 0, 0,
        1, -1, -1, -1, 1, 1, 0, 0, -1, 0, 1, 0, -1, 2, 2, 1, 1, 2, 1, 0, 1, 0,
        2, 1, -1, 0, 1, 0, -1, 2, 2, 1, 1, 2, 1, 0, 1, 0, 2, 1, -1, -1, -1, 1,
        -1, 1, 0, 2, 1, 1, -1, 1, 1, -1, 0, 2, -1, -1, -1, 1, -1, 1, 0, 2, 1,
        1, -1, 1, 1, -1, 0, 2, 0, -1, 2, -1, 0, 1, -1, 0, 2, 1, 2, -1, 2, -1,
        -1, 0, 0, -1, 2, -1, 0, 1, -1, 0, 2, 1, 2, -1, 2, -1, -1, 0, -1, 1, -1,
        -1, -1, -1, 0, 0, 1, -1, -1, -1, 1, 1, 0, 0, -1, 1, -1, -1, -1, -1, 0,
        0, 1, -1, -1, -1, 1, 1, 0, 0, 0, 1, 2, 1, 0, -1, -1, 2, 2, -1, 2, 1, 2,
        1, -1, 2, 0, 1, 2, 1, 0, -1, -1, 2, 2, -1, 2, 1, 2, 1, -1, 2, 1, 1, 1,
        -1, 1, -1, 2, 0, -1, -1, 1, -1, -1, 1, 2, 0, 1, 1, 1, -1, 1, -1, 2, 0,
        -1, -1, 1, -1, -1, 1, 2, 0, 1, 0, -1, 0, 1, 2, 0, 1, -1, 2, -1, 0, -1,
        0, 0, 1, 1, 0, -1, 0, 1, 2, 0, 1, -1, 2, -1, 0, -1, 0, 0, 1, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, 1, 1, 1, 1, 2, 2,
-1, 1, 1, 1, -1, -1, 2, 2, 1, -1, 1, 1, 1, 1, 2, 2, -1, 1, 1, 1, -1, -1, 2, 2,
2, 1, 0, 1, 2, -1, 1, 2, 0, -1, 0, 1, 0, 1, 1, 2, 2, 1, 0, 1, 2, -1, 1, 2, 0,
-1, 0, 1, 0, 1, 1, 2, 0, 0, 0, 2, 0, 2, 1, -1, 2, 2, 0, 2, 2, 0, 1, -1, 0, 0,
0, 2, 0, 2, 1, -1, 2, 2, 0, 2, 2, 0, 1, -1, 1, 2, -1, 2, 1, 0, 0, -1, -1, 0,
-1, 2, -1, 2, 0, -1, 1, 2, -1, 2, 1, 0, 0, -1, -1, 0, -1, 2, -1, 2, 0, -1, -1,
1, -1, -1, -1, -1, 0, 0, 1, -1, -1, -1, 1, 1, 0, 0, -1, 1, -1, -1, -1, -1, 0,
0, 1, -1, -1, -1, 1, 1, 0, 0, 2, 1, 0, 1, 2, -1, 1, 2, 0, -1, 0, 1, 0, 1, 1, 2,
2, 1, 0, 1, 2, -1, 1, 2, 0, -1, 0, 1, 0, 1, 1, 2, 2, 2, 2, 0, 2, 0, -1, 1, 0,
0, 2, 0, 0, 2, -1, 1, 2, 2, 2, 0, 2, 0, -1, 1, 0, 0, 2, 0, 0, 2, -1, 1, -1, 0,
1, 0, -1, 2, 2, 1, 1, 2, 1, 0, 1, 0, 2, 1, -1, 0, 1, 0, -1, 2, 2, 1, 1, 2, 1,
0, 1, 0, 2, 1, 2, 0, 2, 2, 2, 2, -1, -1, 0, 2, 2, 2, 0, 0, -1, -1, 2, 0, 2, 2,
2, 2, -1, -1, 0, 2, 2, 2, 0, 0, -1, -1, 1, 0, -1, 0, 1, 2, 0, 1, -1, 2, -1, 0,
-1, 0, 0, 1, 1, 0, -1, 0, 1, 2, 0, 1, -1, 2, -1, 0, -1, 0, 0, 1, 2, 2, 2, 0, 2,
0, -1, 1, 0, 0, 2, 0, 0, 2, -1, 1, 2, 2, 2, 0, 2, 0, -1, 1, 0, 0, 2, 0, 0, 2,
-1, 1, -1, 0, 1, 0, -1, 2, 2, 1, 1, 2, 1, 0, 1, 0, 2, 1, -1, 0, 1, 0, -1, 2, 2,
1, 1, 2, 1, 0, 1, 0, 2, 1, 1, -1, 1, 1, 1, 1, 2, 2, -1, 1, 1, 1, -1, -1, 2, 2,
1, -1, 1, 1, 1, 1, 2, 2, -1, 1, 1, 1, -1, -1, 2, 2, 2, 1, 0, 1, 2, -1, 1, 2, 0,
-1, 0, 1, 0, 1, 1, 2, 2, 1, 0, 1, 2, -1, 1, 2, 0, -1, 0, 1, 0, 1, 1, 2, -1, -1,
-1, 1, -1, 1, 0, 2, 1, 1, -1, 1, 1, -1, 0, 2, -1, -1, -1, 1, -1, 1, 0, 2, 1, 1,
-1, 1, 1, -1, 0, 2, -1, 0, 1, 0, -1, 2, 2, 1, 1, 2, 1, 0, 1, 0, 2, 1, -1, 0, 1,
0, -1, 2, 2, 1, 1, 2, 1, 0, 1, 0, 2, 1, 2, 0, 2, 2, 2, 2, -1, -1, 0, 2, 2, 2,
0, 0, -1, -1, 2, 0, 2, 2, 2, 2, -1, -1, 0, 2, 2, 2, 0, 0, -1, -1, 2, 1, 0, 1,
2, -1, 1, 2, 0, -1, 0, 1, 0, 1, 1, 2, 2, 1, 0, 1, 2, -1, 1, 2, 0, -1, 0, 1, 0,
1, 1, 2, 2, 2, 2, 0, 2, 0, -1, 1, 0, 0, 2, 0, 0, 2, -1, 1, 2, 2, 2, 0, 2, 0,
-1, 1, 0, 0, 2, 0, 0, 2, -1, 1, 1, 2, -1, 2, 1, 0, 0, -1, -1, 0, -1, 2, -1, 2,
0, -1, 1, 2, -1, 2, 1, 0, 0, -1, -1, 0, -1, 2, -1, 2, 0, -1, 1, -1, 1, 1, 1, 1,
2, 2, -1, 1, 1, 1, -1, -1, 2, 2, 1, -1, 1, 1, 1, 1, 2, 2, -1, 1, 1, 1, -1, -1,
2, 2, -1, 2, 1, 2, -1, 0, 2, -1, 1, 0, 1, 2, 1, 2, 2, -1, -1, 2, 1, 2, -1, 0,
2, -1, 1, 0, 1, 2, 1, 2, 2, -1, 1, 1, 1, -1, 1, -1, 2, 0, -1, -1, 1, -1, -1, 1,
2, 0, 1, 1, 1, -1, 1, -1, 2, 0, -1, -1, 1, -1, -1, 1, 2, 0, 2, -1, 0, -1, 2, 1,
1, 0, 0, 1, 0, -1, 0, -1, 1, 0, 2, -1, 0, -1, 2, 1, 1, 0, 0, 1, 0, -1, 0, -1,
1, 0])

def load_iq(filename, u8, count):
    if u8:
        u8_interleaved = np.fromfile(filename, np.uint8, count=count)
        u8_iq = u8_interleaved.reshape(int(len(u8_interleaved)/2), 2)
        # This directly converts to fc64
        fc64_unscaled = u8_iq[...,0] + np.complex64(1j) * u8_iq[...,1]
        fc64_scaled = (fc64_unscaled - 127.0) / 128.0
        #fc64_dc_comp = fc64_scaled - np.average(fc64_scaled)
        return fc64_scaled
    else:
        return np.fromfile(filename, np.complex64, count=count)

def main():
    parser = argparse.ArgumentParser(description="Plot TII")
    parser.add_argument('--frame', default='0', help='Which transmission frame to analyse',
            required=False)
    parser.add_argument('--samplerate', default='2048000', help='Sample rate',
            required=False)
    parser.add_argument('--iq-file', default='ofdm.iq', help='File to read',
            required=False)
    parser.add_argument('--test-combs', action='store_const', const=True,
            help='Test all comb pattern values', required=False)
    parser.add_argument('--old-algo', action='store_const', const=True,
            help='Do an analysis with the old algorithm', required=False)
    parser.add_argument('--u8', action='store_const', const=True,
            help='File is in u8 and not cf32 format', required=False)
    parser.add_argument('--align', action='store_const', const=True,
            help='Find NULL and align to it', required=False)

    cli_args = parser.parse_args()

    if cli_args.test_combs:
        prepare_tii_patterns()
        prepare_comb_pattern_run(cli_args, 1, 11)
        prepare_comb_pattern_run(cli_args, 1, 12)
    elif cli_args.old_algo:
        prepare_tii_patterns()
        plot_tii_once(cli_args)
    else:
        prepare_tii_patterns()
        algo1(cli_args)


def prepare_comb_pattern_run(options, comb, pattern):
    tii_ini_template = open("tii.ini.template", "r").read()
    fd = open("tii.ini", "w")
    fd.write(tii_ini_template.format(comb=comb, pattern=pattern, oldvariant=0))
    fd.close()

    subprocess.call(['./odr-dabmod', 'tii.ini'])

    ret = plot_tii_once(options)
    if ret[0] == "ok":
        _, c, p, variant = ret
        if c == comb and p == pattern:
            print("== OK    {}".format(ret))
        else:
            print("== WRONG {}".format(ret))
    else:
        print("== FAIL  {}".format(ret))

def advance_to_null(frames):
    for i in range(0, len(frames), NullSize//2):
        if np.all(np.abs(frames[i:i+NullSize//2]) < 1e-2):
            print("NULL at?", i)
            # First non-zero sample is first PRS sample
            for j in range(NullSize):
                if np.abs(frames[i+j]) > 1e-2:
                    print("NULL at ", i+j - NullSize)
                    return frames[i+j - NullSize:]
    print("NULL not found")
    sys.exit(1)

def plot_tii_once(options):
    oversample = int(int(options.samplerate) / 2048000)
    num_samples_per_tf = oversample * (NullSize + NbSymbols * SymSize)
    print("{} samples per TF".format(num_samples_per_tf))

    N = 8
    num_samples = num_samples_per_tf * (int(options.frame) + N)

    frames = load_iq(options.iq_file, options.u8, count=num_samples)

    #skip to frame
    frames = frames[num_samples_per_tf * int(options.frame):]
    print("{} samples loaded".format(len(frames)))

    #fig = pp.figure()
    #fig.suptitle("TII analysis")
    #ax1 = fig.add_subplot(N, 1, i+1)
    #ax1.set_title("Frame {}".format(i))
    #ax1.plot(np.abs(null_fft))

    # analyse N successive frames
    for i in range(N):
        frame = frames[num_samples_per_tf * i:num_samples_per_tf * (i + 1)]

        if np.max(np.abs(frame[:NullSize])) != 0:
            print("Frame {} has nonzero power in null symbol".format(i))

        # Take the NULL symbol from that frame, but skip the cyclic prefix and truncate
        null_skip = NullSize - Spacing
        frame_null = frame[oversample*null_skip:oversample*(null_skip + Spacing)]

        null_fft = np.fft.fft(frame_null, oversample*Spacing)
        null_fft_abs = np.abs(null_fft)

        # The phase reference symbol, skip the cyclic prefix
        frame_prs = frame[oversample*(NullSize + CyclicPrefix):oversample * (NullSize + CyclicPrefix + Spacing)]
        prs_fft = np.fft.fft(frame_prs, oversample*Spacing)

        threshold = 0.01
        carrier_indices = np.nonzero(null_fft_abs > threshold)[0]
        print("Frame {} has {} carriers".format(i, len(carrier_indices)))

        if len(carrier_indices) != 32 and len(carrier_indices) != 0:
            print("Invalid number of TII carriers")
            return ('fail', )

        def ix_to_k(ix):
            "Convert a FFT index to a carrier index k"
            # ix goes from 0 to 2047
            # 0..1024 positive, 1024..2047 negative, 0 is DC, 1..768 and 1280..2047 have power.
            carrieroffset = int(oversample*Spacing)
            if ix <= 1024:
                return ix
            else:
                return ix - carrieroffset

        analyse_prs = False
        if len(carrier_indices) and not analyse_prs:
            print("k              =" + " ".join("{:>4}".format(ix_to_k(ix)) for ix in carrier_indices))
            print("phases         =" + " ".join("{:>4}".format(int(round(p))) for p in np.angle(prs_fft[null_fft_abs > threshold], deg=True)))

            phases_tii = np.angle(null_fft[null_fft_abs > threshold], deg=True)
            phases_prs = np.angle(prs_fft[null_fft_abs > threshold], deg=True)
            phase_error_wrong_impl = np.mod(np.asarray(np.around(phases_tii - phases_prs), dtype=np.int), 360)

            print("phases wrong   =" + " ".join("{:>4}".format(p) for p in phase_error_wrong_impl))

            pair_indices = carrier_indices.reshape(-1,2)[...,0]
            correct_phase_indices = np.stack([pair_indices, pair_indices]).T.flatten()
            phases_prs2 = np.angle(prs_fft[correct_phase_indices], deg=True)
            phase_error_correct_impl = np.mod(np.asarray(np.around(phases_tii - phases_prs2), dtype=np.int), 360)
            print("phases correct =" + " ".join("{:>4}".format(p) for p in phase_error_correct_impl))

            variant = "unknown"
            if np.all(phase_error_correct_impl == 0):
                print("TII uses correct implementation variant")
                variant = "correct"
            elif np.all(phase_error_wrong_impl == 0):
                print("TII uses old wrong implementation variant")
                variant = "wrong"
            else:
                print("TII is wrong")

            carrier_indices_t = tuple(sorted(ix_to_k(c) for c in carrier_indices))
            print(carrier_indices_t)
            if carrier_indices_t in all_tii_patterns:
                c, p = all_tii_patterns[carrier_indices_t]
                print("TII is using comb {} and pattern {}".format(c, p))
                return ("ok", c, p, variant)
            else:
                print("Unrecognised TII comb and pattern")

            return ("fail", variant)

        if analyse_prs:
            delta = ((prs_phases[null_fft_abs > threshold] * 90) - np.angle(prs_fft[null_fft_abs > threshold], deg=True))
            print("prs=" + " ".join("{:>4}".format(int(round(p)) % 360) for p in delta))

    #pp.show()

def algo1(options):
    oversample = 1
    if int(options.samplerate) != 2048000:
        print("oversampling not supported for new algo")
        sys.exit(1)

    num_samples_per_tf = NullSize + NbSymbols * SymSize
    print("{} samples per TF".format(num_samples_per_tf))

    def ix_to_k(ix):
        "Convert a FFT index to a carrier index k"
        # ix goes from 0 to 2047
        # 0..1024 positive, 1024..2047 negative, 0 is DC, 1..768 and 1280..2047 have power.
        carrieroffset = int(Spacing)
        if ix <= 1024:
            return ix
        else:
            return ix - carrieroffset

    N = 8
    num_samples = num_samples_per_tf * (int(options.frame) + N)

    frames = load_iq(options.iq_file, options.u8, count=num_samples)

    if options.align:
        frames = advance_to_null(frames)

    #skip to frame
    frames = frames[num_samples_per_tf * int(options.frame):]
    print("{} samples loaded".format(len(frames)))

    # analyse N successive frames
    for i in range(N):
        frame = frames[num_samples_per_tf * i:num_samples_per_tf * (i + 1)]

        # Take the NULL symbol from that frame, but skip the cyclic prefix and truncate
        null_skip = NullSize - Spacing
        frame_null = frame[null_skip:(null_skip + Spacing)]

        null_fft = np.fft.fft(frame_null, Spacing)

        # The phase reference symbol, skip the cyclic prefix
        frame_prs = frame[NullSize + CyclicPrefix:NullSize + CyclicPrefix + Spacing]
        prs_fft = np.fft.fft(frame_prs, Spacing)

        # In TM1, the carriers repeat four times:
        # [-768, -384[
        # [-384, 0[
        # ]0, 384]
        # ]384, 768]
        # A consequence of the fact that the 0 bin is never used is that the
        # first carrier of each pair is even for negative k, odd for positive k

        blocks = [null_fft[-768:-384], null_fft[-384:], null_fft[1:385], null_fft[385:769]]
        blocks_multiplied = np.zeros(384//2, dtype=np.complex128)
        #print("blocks {}".format(i))
        for block in blocks:
            even_odd = block.reshape(-1, 2)
            b = even_odd[...,0] * np.conj(even_odd[...,1])
            #print("".join('#' if i else '.' for i in np.abs(b) > 1e-7))
            blocks_multiplied += b

        threshold = 0.01
        indices_above_threshold = np.nonzero(np.abs(blocks_multiplied) > threshold)[0]
        carrier_indices = indices_above_threshold * 2 + 1

        if len(frame) < NullSize:
            break

        if np.max(np.abs(frame[:NullSize])) != 0:
            print("Frame {} has nonzero power in null symbol and {} TII carriers".format(i, len(carrier_indices)))

        if len(carrier_indices) >= 4:
            carriers = [ix_to_k(ix) for ix in carrier_indices]

            cp_counts = {}
            for k in carriers:
                if k in cp_per_carrier:
                    cps = cp_per_carrier[k]
                    for cp in cps:
                        if cp not in cp_counts:
                            cp_counts[cp] = 0
                        cp_counts[cp] += 1

            if len(cp_counts) > 0:
                print(carriers)
                for cp in cp_counts:
                    if cp_counts[cp] >= 4:
                        c, p = cp
                        valid, delay, err = analyse_phase(c, p, null_fft, prs_fft)
                        if valid:
                            print("TII likelihood {}: comb {} and pattern {}, delay {} samples, err {}".format(
                                cp_counts[cp], c, p,
                                delay, err))
                        else:
                            print("TII likelihood {}: comb {} and pattern {}, invalid delay measurement, err {}".format(
                                cp_counts[cp], c, p, err))
            else:
                print("Unrecognised TII comb and pattern")

def convert_angles(angle):
    """Convert 0 to 2pi degree angles to -pi to pi"""
    if angle * 2.0 > np.pi:
        return angle - 2*np.pi
    elif angle * 2.0 < -np.pi:
        return angle + 2*np.pi
    else:
        return angle
phase_corrector = np.vectorize(convert_angles)

def analyse_phase(c, p, null_fft, prs_fft):
    carriers = np.array(calculate_carrier_indices(c, p))

    #print("k              =" + " ".join("{:>4}".format(k) for k in carriers))
    #print("phases         =" + " ".join("{:>4}".format(int(round(p))) for p in np.angle(prs_fft[carriers], deg=True)))

    phases_tii = np.angle(null_fft[carriers])

    pair_indices = carriers.reshape(-1,2)[...,0]
    correct_phase_indices = np.stack([pair_indices, pair_indices]).T.flatten()
    phases_prs2 = np.angle(prs_fft[correct_phase_indices])

    fig = pp.figure()
    fig.suptitle("Phase error C {} P {}".format(c, p))

    phase_errors = {}
    search_range = (-20, 500)
    for err in range(*search_range):
        rotate_vec = np.exp(2j * np.pi * err * carriers / 2048)
        rotated = null_fft[carriers] * rotate_vec
        delta = np.asarray(np.around(np.angle(rotated) - phases_prs2), dtype=np.int)
        delta = phase_corrector(delta)
        #print("phases {:>3} =".format(err) + " ".join("{:>4}".format(int(180*p/np.pi)) for p in delta))
        phase_errors[err] = delta

        #ax1 = fig.add_subplot(7, 1, i+1)
        #ax1.set_title("err {}".format(err))
        #ax1.plot(correct_phase_indices, delta, '.')
        #ax1.plot(correct_phase_indices, slopepoly(correct_phase_indices))
    #pp.show()

    best_err = min(phase_errors.items(), key=(lambda e: np.sum(np.abs(e[1]))))
    #print("Best err: {}".format(best_err[0]))
    #print("phases =" + " ".join("{:>4}".format(p) for p in best_err[1]))

    meas_err = np.sum(np.abs(best_err[1]))

    if best_err[0] != search_range[0] and best_err[0] != search_range[1]:
        return (True, best_err[0], meas_err)
    else:
        return (False, best_err[0], meas_err)

main()

# The MIT License (MIT)
#
# Copyright (c) 2018 Matthias P. Braendli
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
