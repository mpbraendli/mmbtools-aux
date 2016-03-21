#!/usr/bin/env python2
#
# Analyse an mp2 file for debugging
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Matthias P. Braendli
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#    THE SOFTWARE.

from pprint import pprint
import sys
import struct

# Header:
# AAAAAAAA AAABBCCD EEEEFFGH IIJJKLMM
# see http://mpgedit.org/mpgedit/mpeg_format/mpeghdr.htm

audio_version_ids = ["MPEG version 2.5", "reserved", "MPEG Version 2 (ISO/IEC 13818-3)", "MPEG Version 1 (ISO/IEC 11172-3)"]
layer_descriptions = ["reserved", "Layer III", "Layer II", "Layer I"]

# bitrate index:
# bits	V1,L1	V1,L2	V1,L3	V2,L1	V2, L2 & L3
# 0000	free	free	free	free	free
# 0001	32	32	32	32	8
# 0010	64	48	40	48	16
# 0011	96	56	48	56	24
# 0100	128	64	56	64	32
# 0101	160	80	64	80	40
# 0110	192	96	80	96	48
# 0111	224	112	96	112	56
# 1000	256	128	112	128	64
# 1001	288	160	128	144	80
# 1010	320	192	160	160	96
# 1011	352	224	192	176	112
# 1100	384	256	224	192	128
# 1101	416	320	256	224	144
# 1110	448	384	320	256	160
# 1111	bad	bad	bad	bad	bad

def analyse(fd):
    headerdata = struct.unpack("!BBBB", fd.read(4))

    sync = (headerdata[0] << 3) | (headerdata[1] >> 5)
    print("Sync: {:x}".format(sync))

    audio_version_id = (headerdata[1] >> 3) & 0x3
    print("audio_version_id {}".format(audio_version_ids[audio_version_id]))

    layer_description = (headerdata[1] >> 1) & 0x3
    print("layer_description {}".format(layer_descriptions[layer_description]))

    protection_bit = headerdata[1] & 0x1
    if protection_bit:
        print("Without protection")
    else:
        print("With protection")

    bitrate_index = headerdata[2] >> 4
    print("bitrate_index {}".format(bitrate_index))

    sampling_rate = (headerdata[2] >> 2) & 0x3
    print("sampling_rate {}".format(sampling_rate))

    padding_bit = (headerdata[2] >> 1) & 0x1
    if padding_bit:
        print("With padding")
    else:
        print("Without padding")

    private_bit = headerdata[2] & 0x1
    if private_bit:
        print("Private bit set")
    else:
        print("Private bit unset")

    channel_mode = headerdata[3] >> 6
    print("channel_mode {}".format(channel_mode))

    mode_extension = (headerdata[3] >> 4) & 0x3
    print("mode_extension {}".format(mode_extension))

    copyright = (headerdata[3] >> 3) & 0x1
    if copyright:
        print("With copyright")
    else:
        print("Without copyright")

    original = (headerdata[3] >> 2) & 0x1
    if original:
        print("With original")
    else:
        print("Without original")

    emphasis = headerdata[3] & 0x3
    print("emphasis {}".format(emphasis))



fd = open(sys.argv[1], "rb")
analyse(fd)
