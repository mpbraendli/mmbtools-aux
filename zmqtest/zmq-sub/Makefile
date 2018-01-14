GIT_VERSION = $(shell git describe --long --all | cut -d "-" -f 3)

ZMQ_LIB=$(shell pkg-config --libs libzmq)

CFLAGS = -Wall -g -std=gnu11 $(ZMQ_LIB) -DGIT_VERSION=\"$(GIT_VERSION)\"

all: zmq-sub

zmq-sub: zmq-sub.c
	gcc $(CFLAGS) -o zmq-sub zmq-sub.c

