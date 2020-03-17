GIT_VERSION = $(shell git describe --long --all | cut -d "-" -f 3)

CXXFLAGS = -std=c++11 -Wall -Wno-unused -g $(ZMQ_LIB) -DGIT_VERSION=\"$(GIT_VERSION)\" -fsanitize=address -fsanitize=undefined
LINK = -lzmq

all: zmq-sub

zmq-sub: zmq-sub.cpp
	g++ $(CXXFLAGS) -o zmq-sub zmq-sub.cpp $(LINK)

