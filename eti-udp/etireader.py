#!/usr/bin/env python

import struct
import os

ETI_FORMAT_RAW = "RAW"
ETI_FORMAT_STREAMED = "STREAMED"
ETI_FORMAT_FRAMED = "FRAMED"

class EtiReaderException(Exception):
    pass

class EtiReader(object):
    def __init__(self, filename):
        self.filename = filename
        self.fd = open(filename, "rb")
        self.fmt = self.discover_filetype()
        print("EtiReader reading {0}, discovered type {1}".format(filename, self.fmt))

    def discover_filetype(self):
        self.fd.seek(0)
        sync = False
        i = 0
        while True:
            sync = self.check_sync()
            if not sync:
                i = i + 1
                self.fd.seek(i)
            else:
                break

        if i == 0:
            self.fd.seek(0)
            return ETI_FORMAT_RAW
        elif i == 2:
            self.fd.seek(0)
            return ETI_FORMAT_STREAMED
        elif i == 6:
            self.fd.seek(4)
            return ETI_FORMAT_FRAMED
        else:
            print("ETI File not aligned, supposing RAW!")
            return ETI_FORMAT_RAW
                

    def __iter__(self):
        while True:
            n = self.next()
            if n == "":
                break
            else:
                yield n

    def next(self):
        if self.fmt == ETI_FORMAT_RAW:
            etiframe = self.fd.read(6144)
            if etiframe == "":
                raise EtiReaderException("Unable to read frame")
            return etiframe


        elif self.fmt == ETI_FORMAT_FRAMED or self.fmt == ETI_FORMAT_STREAMED:
            
            framesize_pack = self.fd.read(2)
            if len(framesize_pack) < 2:
                raise EtiReaderException("Unable to read frame size")
            framesize = struct.unpack("H", framesize_pack)[0]
            if framesize == 0 or framesize > 6144:
                raise EtiReaderException("Framesize: {0}".format(framesize))

            if not self.check_sync():
                raise EtiReaderException("Unable to read sync")

            self.fd.seek(-2, os.SEEK_CUR)
            frame = self.fd.read(framesize+2)
            if len(frame) < framesize:
                raise EtiReaderException("Unable to read frame")
            return frame

    def check_sync(self):
        here = self.fd.tell()
        sync_pack = self.fd.read(4)
        self.fd.seek(here)

        sync = struct.unpack("I", sync_pack)[0]

        return sync == 0x49c5f8ff or sync == 0xb63a07ff


if __name__ == "__main__":
    def etireadertest(reader):
        i = 0
        for frame in reader:
            allframes.append(frame)
            print("Frame {0}, length {1}".format(
                i, len(frame)))
            i += 1
            if i > 10:
                break

    allframes = []
    etireadertest(EtiReader("buddard.eti"))

    allframes = []
    etireadertest(EtiReader("streamed.eti"))

    allframes = []
    etireadertest(EtiReader("funk.eti"))

    allframes = []
    etireadertest(EtiReader("funk.raw.eti"))
