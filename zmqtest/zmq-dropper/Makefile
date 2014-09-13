GIT_VERSION = $(shell git describe --long --all | cut -d "-" -f 3)

CFLAGS = -Wall -g -std=c99 -lzmq -DGIT_VERSION=\"$(GIT_VERSION)\"

all: zmq-dropper

zmq-dropper: zmq-dropper.c
	gcc $(CFLAGS) -o zmq-dropper zmq-dropper.c

