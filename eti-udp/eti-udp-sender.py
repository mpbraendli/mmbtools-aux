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


from etireader import *
from etifec import *
from socket import *
import sys
import os
import time
import zfec
import struct
import StringIO

PORT = 12525

udpdestinations = [('localhost', PORT)]

sock = socket(AF_INET, SOCK_DGRAM)

reader = EtiReader("../eti/streamed.eti")

seqnr = 0

k = 40
m = 60
etifec = ETI_Fec(k, m)

while True:
    seqnr += 1
    # Read four ETI frames
    try:
        etigroup = "".join([reader.next() for i in range(4)])
    except EtiReaderException as e:
        print("End of file reached")
        break

    time.sleep(0.002)

    #print("Seqnr {0}".format(seqnr))
    tx_packets = etifec.encode_eti_group(etigroup, seqnr)

    for packet in tx_packets:
        for dest in udpdestinations:
            sock.sendto(packet, dest)

