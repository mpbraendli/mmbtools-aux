GIT_VERSION = $(shell git describe --long --all | cut -d "-" -f 3)

CFLAGS = -Wall -g $(ZMQ_LIB) -DGIT_VERSION=\"$(GIT_VERSION)\"
LINK = -lzmq

all: zmq-sub

zmq-sub: zmq-sub.c
	gcc $(CFLAGS) -o zmq-sub zmq-sub.c $(LINK)

