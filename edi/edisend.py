#!/usr/bin/env python2
#
# Read an EDI dump file and transmit over UDP
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Matthias P. Braendli
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

import sys
import struct

from crc import crc16
from reedsolo import RSCodec

import socket
import time

UDP_IP = "239.20.64.1"
UDP_PORT = 12002

class BufferedFile:
    def __init__(self, fname):
        self.buf = []

        if fname == "-":
            self.fd = sys.stdin
        else:
            self.fd = open(fname, "rb")

    def read(self, n):
        if not self.buf:
            return self.fd.read(n)
        else:
            if len(self.buf) < n:
                self.buf.extend(self.fd.read(n - len(self.buf)))

            if len(self.buf) == n:
                ret = b"".join(self.buf)
                self.buf = []
            else:
                ret = b"".join(self.buf[:n])
                del self.buf[:n]

            return ret

    def peek(self, n):
        dat = self.fd.read(n)
        self.buf.extend(dat)
        return dat


pft_head_struct = "!2sH3B3BH"
pft_rs_head_struct = "!2B"
pft_addr_head_struct = "!2H"
af_head_struct = "!2sLHBc"
class EDI:
    def __init__(self):
        self.last_send_time = time.time()
        self.sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP

    def send_udp(self, message):
        self.sock.sendto(message, (UDP_IP, UDP_PORT))


    def decode(self, stream):
        sync = stream.peek(2)

        if len(sync) < 2:
            return False

        if sync == "PF":
            return self.decode_pft(stream)
        elif sync == "AF":
            return self.decode_af(stream, is_stream=True)



    def decode_pft(self, stream):
        headerdata = stream.read(12)
        header = struct.unpack(pft_head_struct, headerdata)

        psync, pseq, findex1, findex2, findex3, fcount1, fcount2, fcount3, fec_ad_plen = header

        findex = (findex1 << 16) | (findex2 << 8) | findex3
        fcount = (fcount1 << 16) | (fcount2 << 8) | fcount3

        fec = (fec_ad_plen & 0x8000) != 0x00
        addr = (fec_ad_plen & 0x4000) != 0x00
        plen = fec_ad_plen & 0x3FFF

        rs_k = 0
        rs_z = 0
        if fec:
            rs_head = stream.read(2)
            rs_k, rs_z = struct.unpack(pft_rs_head_struct, rs_head)
            headerdata += rs_head

        addr_source = 0
        addr_dest   = 0
        if addr:
            addr_head = stream.read(4)
            addr_source, addr_dest = struct.unpack(pft_addr_head_struct, addr_head)
            headerdata += addr_head

        # read CRC
        crc_data = stream.read(2)
        crc = struct.unpack("!H", crc_data)[0]

        crc_calc = crc16(headerdata)
        crc_calc ^= 0xFFFF

        crc_ok = crc_calc == crc

        time_now = time.time()
        if findex == 0:
            if self.last_send_time + 24e-3 > time_now:
                delay = self.last_send_time + 24e-3 - time_now
                print("Sleeping for {} ms".format(1000 * delay))
                time.sleep(delay)
            self.last_send_time = time_now


        if crc_ok:
            payload = stream.read(plen)
            self.send_udp(headerdata + crc_data + payload)

        return crc_ok


    def decode_af(self, in_data, is_stream=False):
        if is_stream:
            headerdata = in_data.read(10)
        else:
            headerdata = in_data[:10]

        sync, plen, seq, ar, pt = struct.unpack(af_head_struct, headerdata)

        if sync != "AF":
            return False

        crc_flag = (ar & 0x80) != 0x00
        revision = ar & 0x7F

        if is_stream:
            payload = in_data.read(plen)
            crc_data = in_data.read(2)
            crc = struct.unpack("!H", crc_data)[0]
        else:
            payload = in_data[10:10+plen]
            crc_data = in_data[10+plen:10+plen+2]
            crc = struct.unpack("!H", crc_data)[0]

        crc_calc = crc16(headerdata)
        crc_calc = crc16(payload, crc_calc)
        crc_calc ^= 0xFFFF

        crc_ok = crc_calc == crc

        if crc_ok:
            self.send_udp(headerdata + payload + crc_data)

        return crc_ok

if len(sys.argv) > 1:
    filename = sys.argv[1]

    edi_fd = BufferedFile(filename)
else:
    edi_fd = BufferedFile("-")

edi = EDI()
while edi.decode(edi_fd):
    pass

