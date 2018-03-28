#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Does some TII pattern calculations
#
# http://www.opendigitalradio.org
# Licence: The MIT License, see notice at the end of this file

import sys
import argparse
import time

TII_PATTERN = [ # {{{
    [0,0,0,0,1,1,1,1],
    [0,0,0,1,0,1,1,1],
    [0,0,0,1,1,0,1,1],
    [0,0,0,1,1,1,0,1],
    [0,0,0,1,1,1,1,0],
    [0,0,1,0,0,1,1,1],
    [0,0,1,0,1,0,1,1],
    [0,0,1,0,1,1,0,1],
    [0,0,1,0,1,1,1,0],
    [0,0,1,1,0,0,1,1],
    [0,0,1,1,0,1,0,1],
    [0,0,1,1,0,1,1,0],
    [0,0,1,1,1,0,0,1],
    [0,0,1,1,1,0,1,0],
    [0,0,1,1,1,1,0,0],
    [0,1,0,0,0,1,1,1],
    [0,1,0,0,1,0,1,1],
    [0,1,0,0,1,1,0,1],
    [0,1,0,0,1,1,1,0],
    [0,1,0,1,0,0,1,1],
    [0,1,0,1,0,1,0,1],
    [0,1,0,1,0,1,1,0],
    [0,1,0,1,1,0,0,1],
    [0,1,0,1,1,0,1,0],
    [0,1,0,1,1,1,0,0],
    [0,1,1,0,0,0,1,1],
    [0,1,1,0,0,1,0,1],
    [0,1,1,0,0,1,1,0],
    [0,1,1,0,1,0,0,1],
    [0,1,1,0,1,0,1,0],
    [0,1,1,0,1,1,0,0],
    [0,1,1,1,0,0,0,1],
    [0,1,1,1,0,0,1,0],
    [0,1,1,1,0,1,0,0],
    [0,1,1,1,1,0,0,0],
    [1,0,0,0,0,1,1,1],
    [1,0,0,0,1,0,1,1],
    [1,0,0,0,1,1,0,1],
    [1,0,0,0,1,1,1,0],
    [1,0,0,1,0,0,1,1],
    [1,0,0,1,0,1,0,1],
    [1,0,0,1,0,1,1,0],
    [1,0,0,1,1,0,0,1],
    [1,0,0,1,1,0,1,0],
    [1,0,0,1,1,1,0,0],
    [1,0,1,0,0,0,1,1],
    [1,0,1,0,0,1,0,1],
    [1,0,1,0,0,1,1,0],
    [1,0,1,0,1,0,0,1],
    [1,0,1,0,1,0,1,0],
    [1,0,1,0,1,1,0,0],
    [1,0,1,1,0,0,0,1],
    [1,0,1,1,0,0,1,0],
    [1,0,1,1,0,1,0,0],
    [1,0,1,1,1,0,0,0],
    [1,1,0,0,0,0,1,1],
    [1,1,0,0,0,1,0,1],
    [1,1,0,0,0,1,1,0],
    [1,1,0,0,1,0,0,1],
    [1,1,0,0,1,0,1,0],
    [1,1,0,0,1,1,0,0],
    [1,1,0,1,0,0,0,1],
    [1,1,0,1,0,0,1,0],
    [1,1,0,1,0,1,0,0],
    [1,1,0,1,1,0,0,0],
    [1,1,1,0,0,0,0,1],
    [1,1,1,0,0,0,1,0],
    [1,1,1,0,0,1,0,0],
    [1,1,1,0,1,0,0,0],
    [1,1,1,1,0,0,0,0] ] # }}}

def calculate_A_c_p(c, p, k):
    """ETSI EN 300 401 14.8.1"""
    r = 0

    if k == 0 or k == -769:
        return 0
    elif -768 <= k and k < -384:
        for b in range(8):
            if k == -768 + 2*c + 48*b and TII_PATTERN[p][b]:
                r += 1
    elif -384 <= k and k < 0:
        for b in range(8):
            if k == -384 + 2*c + 48*b and TII_PATTERN[p][b]:
                r += 1
    elif 0 < k and k <= 384:
        for b in range(8):
            if k == 1 + 2*c + 48*b and TII_PATTERN[p][b]:
                r += 1
    elif 384 < k and k <= 768:
        for b in range(8):
            if k == 385 + 2*c + 48*b and TII_PATTERN[p][b]:
                r += 1
    else:
        raise ValueError("Invalid k={}".format(k))

    # I'm expecting that r means "enable or disable", nothing else
    assert(r < 2);
    return r

def calculate_reduced_carrier_indices(c, p):
    carriers = []
    for k in range(384):
        for b in range(8):
            if k == 1 + 2*c + 48*b and TII_PATTERN[p][b]:
                carriers.append(k)
    return carriers

def calculate_carrier_indices(c, p):
    carriers = calculate_reduced_carrier_indices(c, p)

    # because of z_m,0,k, we enable carrier k if A_c,p(k) or A_c,p(k-1) are
    # true
    carriers += [k + 1 for k in carriers]
    carriers += [k - 769 for k in carriers] + \
            [k - 385 for k in carriers] + \
            [k + 384 for k in carriers]
    carriers.sort()
    return carriers

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate TII")
    parser.add_argument('--all', action='store_const', const=True,
            help='Calulate all carrier indices', required=False)
    parser.add_argument('--check-zero', action='store_const', const=True,
            help='Check if any pattern sets zero freq', required=False)
    parser.add_argument('--test1', action='store_const', const=True,
            help='Do equivalence test 1', required=False)
    cli_args = parser.parse_args()


    if cli_args.all:
        for c in range(24):
            for p in range(70):
                carriers = calculate_carrier_indices(c, p)
                print(c, p, carriers, len(carriers))

    elif cli_args.check_zero:
        for c in range(24):
            for p in range(70):
                carriers = calculate_carrier_indices(c, p)
                if 0 in carriers:
                    print("Found 0 in")
                elif 1 in carriers:
                    print("Found 1 in")
                elif -1 in carriers:
                    print("Found -1 in")
                else:
                    continue
                print("Car: ", c, p, carriers, len(carriers))

    elif cli_args.test1:
        print("Running compare test table")
        duration1 = 0
        duration2 = 0
        for c in range(24):
            for p in range(70):
                start1 = time.time()
                carriers0 = [k
                        for k in range(-768, 769)
                        if calculate_A_c_p(c, p, k) or calculate_A_c_p(c, p, k-1)]
                carriers0.sort()
                duration1 += (time.time() - start1)

                start2 = time.time()
                carriers1 = calculate_carrier_indices(c, p)
                duration2 += (time.time() - start2)

                if carriers0 != carriers1:
                    print("0: {}".format(carriers0))
                    print("1: {}".format(carriers1))
                    sys.exit(1)
        print("Comparison successful: {} vs {}".format(duration1, duration2))

    else:
        print("Example given in standard:")
        c = 1
        p = 11
        acps = [k
                for k in range(-768, 769)
                if calculate_A_c_p(c, p, k)]
        print("ACP: ", c, p, acps, len(acps))
        carriers = calculate_carrier_indices(c, p)
        print("Car: ", c, p, carriers, len(carriers))

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
