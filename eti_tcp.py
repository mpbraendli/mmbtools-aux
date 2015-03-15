#!/usr/bin/env python2
#
# A small program that transmits stdin to several TCP connections
#
# We set PACKET_SIZE to 4*6144 to put four ETI frames together
# that will become one DAB frame in TM I.
#
# Copyright (c) 2015, Matthias P. Braendli
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from socket import *
import threading
import Queue
import sys
import os
import time

PACKET_SIZE=6144
QUEUE_PACKET_CAPACITY=100 # represents 2.4 seconds of ETI data

class Connection(object):
    def __init__(self, conn, addr):
        print("Got new connection from {0}".format(addr))
        self.addr = addr
        self.q = Queue.Queue(PACKET_SIZE*QUEUE_PACKET_CAPACITY)
        self.ch = ConnectionHandler(conn, self.q)
        self.ch.start()

    def send(self, data):
        if self.ch.running:
            try:
                self.q.put_nowait(data)
            except Queue.Full:
                # Abort here, otherwise we send an incomplete stream !
                self.terminate()
            return True
        else:
            return False

    def join(self):
        self.ch.join()

    def terminate(self):
        self.ch.running = False
        self.ch.close()

class ConnectionHandler(threading.Thread):
    def __init__(self, sock, queue):
        self.sock = sock
        self.queue = queue
        self.running = True
        threading.Thread.__init__(self)

    def run(self):
        print("Server for {0} created".format(self.sock.getpeername()))

        # Disable Nagle's algorithm, s.t. the TCP stack does not
        # put together small send()s
        self.sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)

        while self.running:
            data = self.queue.get()
            try:
                self.sock.sendall(data)
            except:
                self.running = False

        self.sock.close()

    def close(self):
        self.sock.close()

import fcntl
class DataSender(threading.Thread):

    def __init__(self, connections, lock):
        print("DS starting.")

        if True:
            # make stdin a non-blocking file
            fd = sys.stdin.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.running = True
        self.connections = connections
        self.lock = lock
        threading.Thread.__init__(self)

    def run(self):
        while self.running:
            try:
                data = sys.stdin.read(PACKET_SIZE)
            except KeyboardInterrupt:
                break
            except:
                time.sleep(0.005)
                continue

            removeconns = []

            self.lock.acquire()
            for c in self.connections:
                if not c.send(data):
                    removeconns.append(c)
            #print("DS: Put {0} bytes into {1} connections".format(len(data), len(self.connections)))

            for c in removeconns:
                c.terminate()
                self.connections.remove(c)
            if len(removeconns) != 0:
                print("DS: Removed {0} connections".format(len(removeconns)))
            del removeconns
            self.lock.release()

        print("DS: Bye")

def listener(port):
    print("eti_tcp.py [{0}] starting...".format(os.getpid()))
    ADDR = ("", port)

    serv = socket(AF_INET, SOCK_STREAM)

    # Can reuse a socket that is in TIME_WAIT
    serv.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    serv.bind((ADDR))
    serv.listen(3)

    connections = []
    connections_lock = threading.Lock()

    ds = DataSender(connections, connections_lock)
    ds.start()

    while True:
        try:
            print("Main: accepting on port {0}...".format(port))
            sock, addr = serv.accept()

            connections_lock.acquire()
            connections.append(Connection(sock, addr))
            connections_lock.release()
        except KeyboardInterrupt:
            print("Interrupted")
            break

    try:
        connections_lock.release()
    except:
        print("No need to release lock")

    print("Terminating {0} connections".format(len(connections)))
    for c in connections:
        c.terminate()

    print("Joining connections")
    for c in connections:
        c.join()

    print("Send Ctrl-D to close stdin")

    ds.running = False
    ds.join()

def usage():
    print("""Usage:
    {0} port

    port: specifies on which TCP port to listen for incoming connections""".format(sys.argv[0]))

if len(sys.argv) != 2:
    usage()
    sys.exit(1)
else:
    port = 0
    try:
        port = int(sys.argv[1])
    except:
        usage()
        sys.exit(1)

    listener(port)
