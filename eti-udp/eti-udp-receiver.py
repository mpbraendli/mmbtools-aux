#!/usr/bin/env python
#
# Read ETI data from standard input, in RAW, STREAMED or FRAMED format, and transmit
# it over UDP to several receivers, using forward erasure correction and sequences
# numbering to reorder packets.
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

from etifec import *
from socket import *
import sys
import os
import time
import zfec
import struct
import StringIO

PORT = 12525

def log(message):
    sys.stderr.write(message)
    sys.stderr.write("\n")

def recieve_eti(output_fd):
    k = 40
    m = 60
    etifec = ETI_Fec(k, m)

    decodedeti = {}

    blocks_grouped = {}
    ignore_groups = []

    start_delay = 10
    curr_seqnr = -1


    while True:
        packet = sock.recv(4096)

        # Add the received packet into the right place in the dictionary
        sequence_nr, block_nr = struct.unpack("QI", packet[:12])
        if sequence_nr in ignore_groups:
            # We've already decoded this group. Drop.
            #log("Dropped packet from already decoded group {0}".format(sequence_nr))
            continue
        #log("Registering packet sn {0} / bn {1}".format(sequence_nr, block_nr))
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
                    import ipdb; ipdb.set_trace()
                    log("Failed to receive group {0}".format(curr_seqnr))
                    if curr_seqnr in decodedeti:
                        del decodedeti[curr_seqnr]
                    ignore_groups.append(curr_seqnr)
                    curr_seqnr += 1

        rx_eti_stream.flush()

try:
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(("", PORT))
    rx_eti_stream = open("foo", "w") # sys.stdout
    recieve_eti(rx_eti_stream)
except KeyboardInterrupt:
    sock.close()

