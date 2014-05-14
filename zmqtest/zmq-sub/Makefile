GIT_VERSION = $(shell git describe --long --all | cut -d "-" -f 3)

CFLAGS = -Wall -g -std=c99 -lzmq -DGIT_VERSION=\"$(GIT_VERSION)\"

all: zmq-sub

zmq-sub: zmq-sub.c
	gcc $(CFLAGS) -o zmq-sub zmq-sub.c

