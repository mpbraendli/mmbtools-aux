#!/usr/bin/env python
#   Copyright (C) 2013 Matthias P. Braendli
#   http://mpb.li
#
#   This file is part of CRC-DabMux.
#
#   CRC-DabMux is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   CRC-DabMux is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with CRC-DabMux.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Use this script to receive the zmq+tcp://*:8080 output from
# crc-dabmux.
#
# It can then be piped into CRC-DabMod. Thanks to ZeroMQ, the connection
# stays up even when crc-dabmux is killed and restarted. However,
# frame-sync is lost, and UHD Underruns will happen.

# This is python3 code, it will probably not work on python2.
# TODO fix that

import sys
import zmq

RAW_LEN=6144

context = zmq.Context()

sock = context.socket(zmq.SUB)

sock.connect("tcp://localhost:8080")

# set a filter that lets everything through
sock.setsockopt(zmq.SUBSCRIBE, bytes([]))

sys.stderr.write("Entering loop\n")
while True:
    data = sock.recv(flags=0, copy=True, track=False)

    sys.stdout.buffer.write(data)
    sys.stdout.buffer.write(bytes([0x55] * (RAW_LEN - len(data))))
