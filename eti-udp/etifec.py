#!/usr/bin/env python
#
# Read ETI data from standard input, in RAW, STREAMED or FRAMED format, and
# apply FEC
#
# Copyright (c) 2012, Matthias P. Braendli <matthias@mpb.li>
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.


from socket import *
import sys
import os
import time
import zfec
import struct

MAX_WAIT_GROUPS = 8 # The number of complete groups to receive before we stop waiting
                    # for packets of the current group, and declare it lost.

class ETI_Fec(object):
    def __init__(self, k, m):
        self.k = k
        self.m = m
        self.z_encoder = zfec.Encoder(k=k, m=m)
        self.z_decoder = zfec.Decoder(k=k, m=m)

    def encode_eti_group(self, etidata, SEQ):
        # prepend the data length (as an unsigned int)
        # and add padding s.t. the total length is multiple of k
        framelen = len(etidata)

        paddinglen = 40 - ((framelen+4) % 40)

        frame_uncorrected = struct.pack("I", framelen) + etidata + (" "*paddinglen)

        # split into k blocks
        bs = len(frame_uncorrected)/self.k
        blocks_uncorrected = [frame_uncorrected[i*bs:(i+1)*bs] for i in range(self.k)]

        # Apply FEC using ZFEC
        blocks_encoded = self.z_encoder.encode(blocks_uncorrected)

        # Prepend sequence number (unsigned long) and block identificator for each block (unsigned int)
        return [struct.pack("QI", SEQ, i) + block for i,block in enumerate(blocks_encoded)]

    def decode_eti_group(self, group_sn, blocks_rx, block_nr):

        #print("Decoding group {0}, using {1} blocks".format(group_sn, len(blocks_rx)))

        if len(blocks_rx) < self.k:
            raise Exception("Not enough packets for frame")

        rx_blocks_encoded = blocks_rx[:self.k]

        # Use ZFEC to get the original blocks
        rx_blocks_corrected = self.z_decoder.decode(rx_blocks_encoded, block_nr)

        # Concatenate together, get length, remove padding
        rx_frame_padded = "".join(rx_blocks_corrected)

        rx_framelen = struct.unpack("I", rx_frame_padded[:4])[0]

        return rx_frame_padded[4:4+rx_framelen]

if __name__ == "__main__":
    from etireader import *
    import StringIO

    def read_eti_group(reader):
        # read 4 eti frames
        return "".join([reader.next() for i in range(4)])

    reader = EtiReader("buddard.eti")

    # k: the number of packets required for reconstruction 
    # m: the number of packets generated 
    k = 40
    m = 60

    etifec = ETI_Fec(k, m)

    #### ENCODE

    NPACK = 20
    tx = []
    eti_tx = ""
    for s in range(NPACK):
        sn = s + 43
        etigroup = read_eti_group(reader)
        tx += etifec.encode_eti_group(etigroup, sn)
        eti_tx += etigroup
        print("TX group {0} of len {1}".format(sn, len(etigroup)))


    ###### TRANSMIT
    # The network connection drops some frames, and might reorder them

    import random

    packets_rx = []

    MAX_DIST = 25
    for packet in tx:
        if random.random() < 0.75:
            packets_rx.append(packet)

        if len(packets_rx) > MAX_DIST:
            #do some swapping
            if random.random() < 0.75:
                p = random.randint(2, MAX_DIST)
                packets_rx[-1], packets_rx[-p] = packets_rx[-p], packets_rx[-1]


    ###### DECODE


    decodedeti = {}

    blocks_grouped = {}
    ignore_groups = []

    start_delay = 10
    curr_seqnr = -1

    rx_eti_stream = StringIO.StringIO()
    for packet in packets_rx:
        # Add the received packet into the right place in the dictionary
        sequence_nr, block_nr = struct.unpack("QI", packet[:12])
        if sequence_nr in ignore_groups:
            # We've already decoded this group. Drop.
            continue
        print("Registering packet sn {0} / bn {1}".format(sequence_nr, block_nr))
        if sequence_nr not in blocks_grouped:
            blocks_grouped[sequence_nr] = [(block_nr, packet[12:])]
        else:
            blocks_grouped[sequence_nr].append((block_nr, packet[12:]))

        # If we have enough blocks for one group (with same sequence number), decode
        # and add to completed list
        for group_sn in blocks_grouped.keys()[:]:
            if len(blocks_grouped[group_sn]) >= k:
                block_numbers, blocks = zip(*blocks_grouped[group_sn])
                decodedeti[group_sn] = etifec.decode_eti_group(group_sn, blocks, block_numbers)
                del blocks_grouped[group_sn]
                ignore_groups.append(group_sn)

        # append to received stream in-order, handle incomplete groups
        if start_delay > 0:
            start_delay -= 1
        if start_delay == 1:
            curr_seqnr = min(blocks_grouped.keys())
        if start_delay <= 1:
            while curr_seqnr in ignore_groups:
                rx_eti_stream.write(decodedeti[curr_seqnr])
                del decodedeti[curr_seqnr]
                curr_seqnr += 1
            else:
                if len(blocks_grouped.keys()) > MAX_WAIT_GROUPS:
                    if curr_seqnr in decodedeti:
                        del decodedeti[curr_seqnr]
                    ignore_groups.append(curr_seqnr)
                    curr_seqnr += 1

    rx_eti_stream.seek(0)


    print("Decoded frames: [{0}], Incomplete [{1}]".format(",".join(str(i) for i in ignore_groups), ",".join(str(i) for i in blocks_grouped.keys())))

    if rx_eti_stream.read() == eti_tx:
        print("ALL OK")
    else:
        print("FAIL")
