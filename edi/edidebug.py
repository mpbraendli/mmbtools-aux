#!/usr/bin/env python2
#
# Decode an EDI file for debugging
#
# File format: concatenated data from UDP messages, no framing whatsoever
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

from pprint import pprint
import io
import sys
import struct

from crc import crc16
from reedsolo import RSCodec

class Printer:
    def __init__(self):
        self.indent = 0

    def pr(self, s):
        print(" " * self.indent + s)

    def hexpr(self, header, seq):
        if isinstance(seq, str):
            seq = bytearray(seq)

        print(" " * self.indent +
                header +
                " ({}): ".format(len(seq)) +
                " ".join("{0:02x}".format(el) for el in seq))

    def inc(self):
        self.indent += 1
    def dec(self):
        self.indent -= 1

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

def tobyte(xs):
    return bytes(bytearray([xs]))

class EtiData:
    def __init__(self):
        self.clear()

    def new_subchannel(self):
        new_stc = {}
        self.stc.append(new_stc)
        return new_stc

    def clear(self):
        self.fc = {}
        self.stc = []
        self.mnsc = 0
        self.complete = False
        self.fic = []

    def generate_eti(self):
        # generate ETI(NI)
        # SYNC
        buf = io.BytesIO()
        buf.write("\xff") # ERR
        # FSYNC
        if self.fc['FCT'] % 2 == 1:
            buf.write("\xf8\xc5\x49")
        else:
            buf.write("\x07\x3a\xb6")

        # LIDATA
        # FC
        buf.write(tobyte(self.fc['FCT'] & 0xff))

        NST = len(self.stc)
        buf.write(tobyte((self.fc['FICF'] << 7) | NST))

        if self.fc['FICF'] == 0:
            FICL = 0
        elif self.fc['MID'] == 3:
            FICL = 32
        else:
            FICL = 24

        # EN 300 799 5.3.6
        FL = NST + 1 + FICL + sum(subch['STL'] * 2 for subch in self.stc)

        print("********** NST {}, FICL {}, stl {}, sum, {}".format(
            NST, FICL, [subch['STL']  for subch in self.stc],
                sum(subch['STL'] * 2 for subch in self.stc)))

        buf.write(tobyte( (self.fc['FP'] << 5) |
                          (self.fc['MID'] << 3) |
                          ((FL & 0x700) >> 8)))

        buf.write(tobyte(FL & 0xff))

        # STC
        for subch in self.stc:
            buf.write(tobyte( (subch['SCID'] << 2) | ((subch['SAD'] & 0x300) >> 8) ))
            buf.write(tobyte( subch['SAD'] & 0xff ))
            buf.write(tobyte( (subch['TPL'] << 2) | ((subch['STL'] & 0x300) >> 8)))
            buf.write(tobyte( subch['STL'] & 0xff ))

        # EOH
        # MNSC
        buf.write(tobyte( self.mnsc & 0xff ))
        buf.write(tobyte( (self.mnsc & 0xff00) >> 8 ))
        # CRC
        buf.seek(4)
        headerdata = buf.read()
        crc_calc = crc16(headerdata)
        crc_calc ^= 0xFFFF
        buf.write(tobyte( (crc_calc & 0xff00) >> 8))
        buf.write(tobyte( crc_calc & 0xff ))

        mst_start = buf.tell()
        # MST
        # FIC data
        buf.write(bytes(bytearray(self.fic)))

        # Data stream
        for subch in self.stc:
            buf.write(bytes(bytearray(subch['data'])))

        # EOF
        # CRC
        buf.seek(mst_start)
        mst_data = buf.read()
        crc_calc = crc16(mst_data)
        crc_calc ^= 0xFFFF
        buf.write(tobyte( (crc_calc & 0xff00) >> 8))
        buf.write(tobyte( crc_calc & 0xff ))

        buf.write("\xff\xff") # RFU

        # TIST
        buf.write("\xff\xff\xff\xff") # TODO TIST in EDI is awful

        length = buf.tell()

        padding = 6144 - length

        buf.write(bytes(bytearray("\x55" * padding)))

        buf.seek(0)
        return buf.read()


eti_data = EtiData()
p = Printer()

# keys=findex
defragmenters = {}

def decode(stream):
    p.pr("start")
    success = False

    sync = stream.peek(2)

    if len(sync) < 2:
        p.pr("EOF")
        return False

    if sync == "PF":
        if decode_pft(stream):
            p.pr("PFT decode success")
            success = True
        else:
            p.pr("PFT decode fail")
    elif sync == "AF":
        if decode_af(stream, is_stream=True):
            p.pr("AF decode success")
            success = True
        else:
            p.pr("AF decode fail")
    else:
        p.pr("sync unknown {}".format(sync))
    return success


pft_head_struct = "!2sH3B3BH"
pft_rs_head_struct = "!2B"
pft_addr_head_struct = "!2H"
def decode_pft(stream):
    p.inc()
    p.pr("start decoding PF")

    headerdata = stream.read(12)
    header = struct.unpack(pft_head_struct, headerdata)

    psync, pseq, findex1, findex2, findex3, fcount1, fcount2, fcount3, fec_ad_plen = header

    findex = (findex1 << 16) | (findex2 << 8) | findex3
    fcount = (fcount1 << 16) | (fcount2 << 8) | fcount3

    fec = (fec_ad_plen & 0x8000) != 0x00
    addr = (fec_ad_plen & 0x4000) != 0x00
    plen = fec_ad_plen & 0x3FFF

    # try to sync according to TS 102 821 Clause 7.4.1
    if psync != "PF":
        p.pr("No PF Sync")
        p.dec()
        return False

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
    crc = struct.unpack("!H", stream.read(2))[0]

    crc_calc = crc16(headerdata)
    crc_calc ^= 0xFFFF

    crc_ok = crc_calc == crc

    if crc_ok:
        p.pr("CRC ok")
    else:
        p.pr("CRC not ok!")
        p.pr("  read 0x{:04x}, calculated 0x{:04x}".format(crc, crc_calc))

    p.pr("pseq {}".format(pseq))
    p.pr("findex {}".format(findex))
    p.pr("fcount {}".format(fcount))
    if fec:
        p.pr("with fec:")
        p.pr(" RSk={}".format(rs_k))
        p.pr(" RSz={}".format(rs_z))
    if addr:
        p.pr("with transport header:")
        p.pr(" source={}".format(addr_source))
        p.pr(" dest={}".format(addr_dest))
    p.pr("payload length={}".format(plen))

    payload = stream.read(plen)

    success = False
    if crc_ok and fec:
        # Fragmentation and
        # Reed solomon decode
        if pseq not in defragmenters:
            defragmenters[pseq] = Defragmenter(fcount, get_rs_decoder(rs_k, rs_z))
        success = defragmenters[pseq].push_fragment(findex, payload)
    elif crc_ok and fcount > 1:
        # Fragmentation
        if pseq not in defragmenters:
            defragmenters[pseq] = Defragmenter(fcount, decode_af_fragments)
        success = defragmenters[pseq].push_fragment(findex, payload)
    elif crc_ok and fcount == 1:
        success = decode_af(payload)

    p.dec()
    return success

class Defragmenter():
    def __init__(self, fcount, callback):
        self.fragments = [None for i in range(fcount)]
        self.fcount = fcount
        self.cb = callback

    def push_fragment(self, findex, fragment):
        self.fragments[findex] = fragment

        received_fragments = [f for f in self.fragments if f is not None]
        p.pr("Fragments: {} (need {})".format(len(received_fragments), self.fcount))
        if len(received_fragments) >= self.fcount:
            p.inc()
            r = self.cb(received_fragments)
            p.dec()
            return r
            # The RS decoder should be able to handle partial lists
            # of fragments. The AF decoder cannot

        return True

    def __repr__(self):
        return "<Defragmenter with fcount={}>".format(self.fcount)

def get_rs_decoder(chunk_size, zeropad):
    p.pr("Build RS decoder for chunk size={}, zero pad={}".format(chunk_size, zeropad))
    def decode_rs(fragments):
        fragment_lengths = ", ".join(["{}:{}".format(i, len(f)) for i,f in enumerate(fragments)])
        p.pr("RS decode {} fragments of length {}".format(
            len(fragments), fragment_lengths))

        #for f in fragments:
        #    p.hexpr("  ZE FRAGMENT", f);

        # Transpose fragments to get an RS block
        rs_block = "".join("".join(f) for f in zip(*fragments))

        # chunks before protection have size chunk_size
        # protection adds 48 bytes
        # The tuples here are (data, parity)

        #p.hexpr("  ZE RS BLOCK", "".join(rs_block))

        num_chunks = len(rs_block) / chunk_size

        data_size = chunk_size + 48

        af_packet_size = num_chunks * chunk_size
        p.pr("AF Packet size {}".format(af_packet_size))

        # Cut the block into list of (data, protection) tuples
        rs_chunks = [ (rs_block[i*data_size:i*data_size + chunk_size],
                       rs_block[i*data_size + chunk_size:(i+1)*data_size])
                for i in range(num_chunks)]

        chunk_lengths = ", ".join(["{}:{}+{}".format(i, len(c[0]), len(c[1])) for i,c in enumerate(rs_chunks)])
        p.pr("{} chunks of length {}".format(num_chunks, chunk_lengths))

        #for c in rs_chunks:
        #    p.hexpr("  ZE CHUNK DATA", c[0]);
        #    p.hexpr("  ZE CHUNK PROT", c[1]);

        rs_codec = RSCodec(48, fcr=1)

        protection_ok = True
        for chunk, protection in rs_chunks:
            #p.pr(" Protection")
            #p.hexpr("  OF ZE CHUNK DATA", chunk);

            bchunk = bytearray(chunk)
            padbytes = 255-(48 + len(chunk))
            bchunk = bchunk + bytearray(0 for i in range(padbytes))
            recalc_protection = rs_codec.encode(bchunk)[-48:]
            if protection != recalc_protection:
                p.pr("  PROTECTION ERROR")
                p.hexpr("  data", chunk)
                p.hexpr("  orig", protection)
                p.hexpr("  calc", recalc_protection)
                protection_ok = False
            else:
                p.pr("  PROTECTION OK")

        if protection_ok:
            p.pr("Protection check: OK")



        afpacket = "".join(data for (data, protection) in rs_chunks)

        #p.hexpr("  ZE AF PACKET", afpacket)

        if zeropad:
            return decode_af(afpacket[0:-zeropad])
        else:
            return decode_af(afpacket)

    return decode_rs


af_head_struct = "!2sLHBc"
def decode_af_fragments(fragments):
    return decode_af("".join(fragments))

def decode_af(in_data, is_stream=False):
    p.pr("AF Packet")
    p.inc()

    if is_stream:
        headerdata = in_data.read(10)
    else:
        headerdata = in_data[:10]

    if len(headerdata) != 10:
        p.hexpr("AF Header", headerdata)

    sync, plen, seq, ar, pt = struct.unpack(af_head_struct, headerdata)

    if sync != "AF":
        p.pr("No AF Sync")
        p.hexpr("in", in_data)
        p.dec()
        return False

    crc_flag = (ar & 0x80) != 0x00
    revision = ar & 0x7F

    if is_stream:
        payload = in_data.read(plen)
        crc = struct.unpack("!H", in_data.read(2))[0]
    else:
        payload = in_data[10:10+plen]
        crc = struct.unpack("!H", in_data[10+plen:10+plen+2])[0]

    crc_calc = crc16(headerdata)
    crc_calc = crc16(payload, crc_calc)
    crc_calc ^= 0xFFFF

    crc_ok = crc_calc == crc

    if crc_flag and crc_ok:
        p.pr("CRC ok")
    elif crc_flag:
        p.pr("CRC not ok!")
        p.pr(" CRC: is 0x{0:04x}, calculated 0x{1:04x}".format(crc, crc_calc))
    else:
        p.pr("No CRC")

    p.pr("plen {}".format(plen))
    p.pr("seq {}".format(seq))
    p.pr("revision {}".format(revision))
    p.pr("protocol type {}".format(pt))

    success = False
    if pt == "T":
        success = decode_tag(payload)

    p.dec()
    return success

tag_item_head_struct = "!4sL"
def tagitems(tagpacket):
    i = 0
    while i+8 < len(tagpacket):
        name, length = struct.unpack(tag_item_head_struct, tagpacket[i:i+8])

        # length is in bits, because it's more annoying this way
        assert(length % 8 == 0)
        length /= 8

        tag_value = tagpacket[i+8:i+8+length]
        yield {'name': name, 'length': length, 'value': tag_value}

        i += 8 + length
    p.pr("Completed decoding all TAG items after {} bytes".format(i))
    eti_data.complete = True

def decode_tag(tagpacket):
    p.pr("Tag packet len={}".format(len(tagpacket)))
    p.inc()
    for item in tagitems(tagpacket):
        if item['name'].startswith("*ptr"):
            decode_starptr(item)
        elif item['name'] == "deti":
            decode_deti(item)
        elif item['name'].startswith("est"):
            decode_estn(item)
        elif item['name'] == "*dmy":
            decode_stardmy(item)
        else:
            p.hexpr("Tag item '{}'".format(item['name']), item['value'])

    p.dec()
    return True

item_starptr_header_struct = "!4sHH"
def decode_starptr(item):
    p.pr("TAG item {} ({})".format(item['name'], item['length']))
    p.inc()
    tag_value = item['value']

    unpacked = struct.unpack(item_starptr_header_struct, tag_value)
    protocol, major, minor = unpacked

    p.pr("Protocol {}, Ver {} {}".format(
        protocol, major, minor) )

    p.dec()

def decode_stardmy(item):
    p.pr("TAG item {} ({})".format(item['name'], item['length']))


item_deti_header_struct = "!BBBBH"
def decode_deti(item):
    p.pr("TAG item {} ({})".format(item['name'], item['length']))
    p.inc()
    tag_value = item['value']

    unpacked = struct.unpack(item_deti_header_struct, tag_value[:6])
    flag_fcth, fctl, stat, mid_fp, mnsc = unpacked
    eti_data.mnsc = mnsc

    atstf = flag_fcth & 0x80 != 0
    eti_data.fc['ATSTF'] = int(atstf)
    if atstf:
        utco, seconds, tsta1, tsta2, tsta3 = struct.unpack("!BL3B", tag_value[6:6+8])
        tsta = (tsta1 << 16) | (tsta2 << 8) | tsta3
        eti_data.fc['TSTA'] = tsta

    ficf  = flag_fcth & 0x40 != 0
    eti_data.fc['FICF'] = int(ficf)

    rfudf = flag_fcth & 0x20 != 0

    fcth  = flag_fcth & 0x1F
    fct = (fcth * 250) + fctl
    eti_data.fc['FCT'] = fct

    mid = (mid_fp >> 6) & 0x03
    eti_data.fc['MID'] = mid

    fp  = (mid_fp >> 3) & 0x07
    eti_data.fc['FP'] = fp


    p.pr("FICF        = {}".format(ficf))
    p.pr("ATST        = {}".format(atstf))
    p.pr("RFUDF       = {}".format(rfudf))
    p.pr("FCT         = {} (0x{:02x} 0x{:02x})".format(fct, fcth, fctl))
    p.pr("STAT        = 0x{:02x}".format(stat))
    p.pr("Mode id     = {}".format(mid))
    p.pr("Frame phase = {}".format(fp))
    p.pr("MNSC        = 0x{:02x}".format(mnsc))
    if atstf:
        p.pr("UTCOffset   = {}".format(utco))
        p.pr("Seconds     = {}".format(seconds))
        p.pr("TSTA        = {} ms".format(tsta / 16384.0))


    len_fic = len(tag_value) - 2 - 4

    if atstf:
        len_fic -= 8

    if rfudf:
        len_fic -= 3

    fic_offset = len(tag_value) - len_fic

    eti_data.fic = tag_value[fic_offset:]

    p.pr("FIC data len  {}".format(len_fic))

    p.dec()

item_estn_head_struct = "!BBB"
def decode_estn(item):
    estN = chr(ord("0") + ord(item['name'][3]))
    p.pr("TAG item EST{} (len={})".format(estN, item['length']))
    p.inc()
    tag_value = item['value']

    scid_sad, sad_low, tpl_rfa = struct.unpack(item_estn_head_struct, tag_value[:3])
    scid = scid_sad >> 2
    sad  = ((scid_sad << 8) | sad_low) & 0x3FF
    tpl  = tpl_rfa >> 2

    stc = eti_data.new_subchannel()
    stc['SCID'] = scid
    stc['SAD']  = sad
    stc['TPL']  = tpl
    stl = len(tag_value) - 3
    stc['STL']  = stl / 8

    p.pr("SCID = {}".format(scid))
    p.pr("SAD  = {}".format(sad))
    p.pr("TPL  = {}".format(tpl))

    assert(item['length'] == len(tag_value))

    p.pr("MST len = {}".format(stl))
    p.hexpr("MST {} data".format(scid), tag_value[3:])
    stc['data'] = tag_value[3:]

    p.dec()

if len(sys.argv) > 2:
    filename = sys.argv[1]
    edi_fd = BufferedFile(filename)

    eti_fd = open(sys.argv[2], "wb")


elif len(sys.argv) == 2:
    filename = sys.argv[1]

    edi_fd = BufferedFile(filename)
    eti_fd = None
else:
    edi_fd = BufferedFile("-")
    eti_fd = None

c = 0
while decode(edi_fd):
    if eti_data.complete and eti_fd:
        eti_fd.write(eti_data.generate_eti())
        c += 1
        if c > 2:
            break

