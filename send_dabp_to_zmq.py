#!/usr/bin/env python
#
# Sends a dabp file in the format output by ODR-AudioEnc over ZMQ.
# Requires at least python 3.3 because we use time.monotonic()
#
# LICENCE: MIT, see end of file

import sys
import zmq
import argparse
import struct
import time

# First parse the arguments given on command line
parser = argparse.ArgumentParser(description='Send .dabp over ZMQ')
parser.add_argument('--input', help='.dabp file to send', required=True)
parser.add_argument('--bitrate', help='The bitrate of the source file', required=True)
parser.add_argument('--to', default='tcp://127.0.0.1:9001', help='Default zmq endpoint to send to (default: tcp://127.0.0.1:9001', required=False)
args = parser.parse_args()

# The ZMQ frames from the audio encoder are expected
# to have the following format, in pseudo C struct, no alignment,
# little-endian. See ODR-DabMux' src/input/Zmq.h for reference.
#
#   uint16_t version; // we support version=1 now
#   uint16_t encoder; // see ZMQ_ENCODER_XYZ
#
#   /* length of the 'data' field */
#   uint32_t datasize;
#
#   /* Audio level, peak, linear PCM */
#   int16_t audiolevel_left;
#   int16_t audiolevel_right;
#
#   /* Data follows the header */
#   uint8_t data[datasize];

# Using the python struct module, we can represent the above C struct as follows:
frame_header = "<HHIhh"

# Taken from ODR-AudioEnc sources' utils.h
ZMQ_ENCODER_FDK=1

# About the datasize field and the number of bytes per ZMQ message:
# One ZMQ message contains 120ms worth of encoded data, i.e. one superframe
# of five frames. This is, according to ODR-DabMux' MuxElements.cpp
# DabSubchannel::getSizeByte() equals to bitrate * 3.
# This means one ZMQ frame must contain bitrate * 3 * 5 data payload bytes.
datasize = int(args.bitrate) * 15


# Open our input file for reading in binary mode, even though that distinction only
# makes sense on other platforms (e.g. Windows). But you should *always* write
# your code in the most portable way, because you never know how your future needs
# will be...
fd = open(args.input, "rb")
# fd stands for "file descriptor", one of the many names for a file handle.

context = zmq.Context()

# ODR-DabMux has a ZeroMQ SUB socket, receiving data from this
# PUB socket. see man zmq_socket for more info
sock = context.socket(zmq.PUB)

sock.connect(args.to)

# We will need this for our throttle logic below. We work with
# integer millisecond granularity and not with float seconds, because
# of rounding errors floats incur.
frame_send_time_ms = int(time.monotonic() * 1000)

print("Entering main loop")
while True:
    # Have a look at the definition of the read() function. It reads "as most"
    # size bytes from the file, meaning it could actually return less bytes
    # than requested. The POSIX read() function has the same behaviour, see
    # man 2 read for more information.
    file_bytes = fd.read(datasize)

    # We assume that a short read is an indication that we're at the EOF.
    if len(file_bytes) != datasize:
        print("End of file reached, aborting")
        break

    # Let us build a frame starting with the header
    version=1
    encoder=ZMQ_ENCODER_FDK

    # we fake the audio level, munin might flag a warning, but that can be sorted out
    # later. Range for the audiolevel is 0 to 0x7FFF (range of signed 16-bit integer)
    audiolevel=0

    # Prepare the header with all its fields
    frame = struct.pack(frame_header, version, encoder, datasize, audiolevel, audiolevel)

    # Append the payload
    frame += file_bytes

    # Send the frame as one zmq message
    sock.send(frame)

    print("Send {} at time {}".format(len(frame), frame_send_time_ms))

    # We need to throttle our process down to one ZMQ frame every 120ms. We use a monotonic
    # clock for that, because it's "The Correct Thing To Do". Non-monotonic clocks can jump
    # around.
    # We want all our time variables to have the same format: integers in milliseconds !
    time_now_ms = int(time.monotonic() * 1000)

    # We cannot just sleep for 120ms, because that wouldn't take in account the time
    # it takes to read the data from the file and to give it to the socket. So our sleep
    # duration must depend on some absolute tracking of time, which is held in
    # the frame_send_time_ms variable.
    diff = time_now_ms - frame_send_time_ms
    waiting = 120 - diff

    # It's illegal to wait a negative time, time.sleep() raises an exception if you do that.
    # Anyway, if time is negative it means we're late sending our packet. We will catch up
    # after the next frame.
    if waiting > 0:
        time.sleep(waiting / 1000)

    # Keep track of our "absolute frame send time"
    frame_send_time_ms += 120


# The MIT License (MIT)
#
# Copyright (c) 2017 Matthias P. Braendli
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
