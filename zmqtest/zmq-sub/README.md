ZMQ ETI Receiver
================

This tool can be used to receive ODR-DabMux ZMQ ETI output and write to a file.

COMPILATION
-----------

use the makefile, no preparations needed:

    make


USAGE
-----

The tool receives from a given host and port, and outputs ETI(NI) to stdout.

Redirect stdout to a file or another tool to save or process the data.

    ./zmq-sub HOST PORT > FILE.ETI

LICENCE
-------

MIT, see `zmq-sub.c`
