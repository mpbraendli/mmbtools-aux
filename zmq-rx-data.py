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
# This is python3 code, it will probably not work on python2.
# TODO fix that

import sys
import zmq

context = zmq.Context()

sock = context.socket(zmq.SUB)

sock.connect("tcp://localhost:9100")
#sock.bind("tcp://*:9000")

# set a filter that lets everything through
sock.setsockopt(zmq.SUBSCRIBE, bytes([]))

sys.stderr.write("Entering loop\n")
while True:
    data = sock.recv(flags=0, copy=True, track=False)

    sys.stdout.buffer.write(data)
