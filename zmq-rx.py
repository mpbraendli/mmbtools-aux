#!/usr/bin/env python

import sys
import zmq

context = zmq.Context()

sock = context.socket(zmq.SUB)

sock.connect("tcp://localhost:8080")

sock.setsockopt(zmq.SUBSCRIBE, bytes([]))

print("Entering loop")
for i in range(10):
    data = sock.recv(flags=0, copy=True, track=False)
    print("RX {0}B, {1:2x}, {2:2x}, {3:2x}, {4:2x}, ...".format(
        len(data),
        data[0], data[1], data[2], data[3] ))
