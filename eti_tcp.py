#!/usr/bin/env python2
#
# A small program that transmits stdin to several TCP connections
#
# Known to work with TM 2. Be careful when using TM 1 or 4: modulator might
# lose frame phase synchronisation when frames are dropped. Setting
# PACKET_SIZE to 4*6144 should avoid this problem.
#
# 2012, mpb

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
                pass
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

    def __init__(self, connections):
        print("DS starting.")

        if True:
            # make stdin a non-blocking file
            fd = sys.stdin.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.running = True
        self.connections = connections
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

    ds = DataSender(connections)
    ds.start()

    while True:
        try:
            print("Main: accepting on port {0}...".format(port))
            sock, addr = serv.accept()
            connections.append(Connection(sock, addr))
        except KeyboardInterrupt:
            print("Interrupted")
            break

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
